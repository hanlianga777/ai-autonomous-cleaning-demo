"""Advanced read model: no model, workflow, planner or Fleet mutation imports."""
import json

from database.connection import database_session, get_event, get_transitions
from perception.config import get_runtime
from robot_operations.catalog import DELIVERY_ADAPTERS
from observability.errors import classify
from observability.redaction import safe, pick, text

JUDGMENT_FIELDS = ("provider", "model", "source", "event_type", "need_action", "need_clean", "confidence", "decision_confidence",
                   "evidence_sufficient", "ambiguity_type", "severity", "surface_type", "evidence_summary", "image_count", "elapsed_ms", "historical_elapsed_ms")


def _events():
    with database_session() as connection:
        rows = connection.execute("SELECT event_id,state,payload FROM cleaning_events WHERE event_id LIKE 'integrated-%' ORDER BY created_at DESC,rowid DESC LIMIT 100").fetchall()
    return [{"event_id": row["event_id"], "state": row["state"], "trace_id": json.loads(row["payload"]).get("trace_id")} for row in rows]


def _operations(event_id, trace_id):
    with database_session() as connection:
        # A pre-F database can still be inspected without creating tables here.
        exists = connection.execute("SELECT 1 FROM sqlite_master WHERE name='ops_tasks'").fetchone()
        if not exists:
            return [], []
        all_tasks = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM ops_tasks")]
        tasks = [task for task in all_tasks if task.get("event_id") == event_id or (trace_id and task.get("trace_id") == trace_id)]
        task_ids = {task["task_id"] for task in tasks}
        request_traces = {task["origin_request_trace_id"] for task in tasks if task.get("origin_request_trace_id")}
        audits = []
        for row in connection.execute("SELECT id,payload FROM ops_audit ORDER BY id"):
            entry = json.loads(row["payload"])
            if (trace_id and entry.get("trace_id") == trace_id) or entry.get("task_id") in task_ids or entry.get("request_trace_id") in request_traces:
                audits.append({"id": row["id"], **entry})
    return tasks, audits


def _requests(trace_ids):
    if not trace_ids:
        return []
    with database_session() as connection:
        rows = connection.execute("SELECT payload FROM runtime_requests WHERE trace_id IN (" + ",".join("?" for _ in trace_ids) + ") ORDER BY rowid", tuple(trace_ids)).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def _spans(trace_id):
    with database_session() as connection:
        rows = connection.execute("SELECT payload FROM runtime_spans WHERE trace_id=? ORDER BY rowid", (trace_id,)).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def _evidence(snapshot, roles, cameras=None):
    assets = (snapshot.get("asset_manifest") or {}).get("assets", [])
    return [{**pick(asset, "camera_id", "role"), "url": asset["url"]} for asset in assets
            if asset.get("role") in roles and (cameras is None or asset.get("camera_id") in cameras)
            and isinstance(asset.get("url"), str) and asset["url"].startswith("/demo-assets/")
            and ".." not in asset["url"] and "?" not in asset["url"]]


def _verification_projection(verification):
    """Expose verdict provenance, never raw model payloads or reasoning."""
    if not isinstance(verification, dict):
        return {}
    output = pick(
        verification,
        "provider", "model", "source", "verification_pass", "issue_remaining", "confidence", "next_action",
        "elapsed_ms", "roi", "roi_source", "independent_roi_review",
    )
    first = verification.get("first_review")
    if isinstance(first, dict):
        # Deliberately project only adjudicable fields; ``raw`` and any provider
        # reasoning/prompt fields cannot reach Advanced through this structure.
        output["first_review"] = pick(first, "verification_pass", "confidence", "next_action")
    return output


def trace_view(event_id=None):
    events = _events()
    if event_id is None and events:
        event_id = events[0]["event_id"]
    event = get_event(event_id) if event_id else None
    if event_id and (not event or "demo_v1" not in event):
        raise ValueError("Integrated event trace not found.")
    event = event or {}
    trace_id = event.get("trace_id")
    transitions = get_transitions(event_id) if event_id else []
    snapshot = event.get("demo_v1") or {}
    mode = snapshot.get("mode")
    replay = mode == "STABLE_REPLAY"
    ai_source = "REPLAY" if replay else "LIVE MODEL"
    first = snapshot.get("first_qwen_review") or {}
    review = snapshot.get("qwen_review") or {}
    multi = snapshot.get("multi_view") or {}
    second = snapshot.get("second_qwen_review")
    assignment = event.get("assignment_decision") or snapshot.get("assignment_decision") or {}
    spatial = snapshot.get("spatial_location")
    route = snapshot.get("navigation_plan")
    verification = snapshot.get("verification")
    error = classify(snapshot.get("error"))
    errors = [error] if error else []
    for transition in transitions:
        detail = transition.get("detail") or {}
        projected = classify(detail.get("error") or ({"error_type": detail["error_type"]} if detail.get("error_type") else None))
        if projected and projected not in errors:
            errors.append(projected)
    tasks, audits = _operations(event_id, trace_id) if event_id else ([], [])
    linked_traces = {value for task in tasks for value in (task.get("trace_id"), task.get("origin_request_trace_id")) if value}
    linked_traces.update(entry["request_trace_id"] for entry in audits if entry.get("request_trace_id"))
    if trace_id:
        linked_traces.add(trace_id)
    requests = _requests(linked_traces)
    spans = _spans(trace_id) if trace_id else []

    def node(id, label, group, output, *, source="DETERMINISTIC RUNTIME", trigger="SYSTEM_WORKFLOW", states=(), input=None, duration=None, evidence=None, status=None, node_error=None):
        return {"id": id, "trace_id": trace_id, "label": label, "group": group,
                "status": status or ("ERROR" if node_error else "RECORDED" if output else "NOT_RECORDED"),
                "source": source if output or node_error else "NOT_RECORDED", "trigger_source": trigger, "start_time": None, "duration_ms": duration,
                "input_summary": safe(input or {}), "output_summary": safe(output or {}), "evidence": evidence or [], "error": node_error}

    multi_status = "ERROR" if multi.get("error") else "RECORDED" if multi else "NOT_TRIGGERED / EVIDENCE_ALREADY_SUFFICIENT" if first.get("evidence_sufficient") is True else "NOT_RECORDED"
    nodes = [
        node("edge", "边缘检测证据", "AI", {"candidates": snapshot.get("controlled_yolo")} if snapshot.get("controlled_yolo") else {},
             source="CONTROLLED EDGE DEMO", states=("EDGE_DETECTED",), evidence=_evidence(snapshot, {"before"})),
        node("single_view", "Single-view Cloud VLM", "AI", pick(first, *JUDGMENT_FIELDS), source=ai_source,
             states=("SINGLE_VIEW_REVIEW",), duration=None if replay else first.get("elapsed_ms"), evidence=_evidence(snapshot, {"before"}),
             node_error=error if error and error["type"] == "MODEL_ERROR" and not first else None),
        node("multi_view_agent", "Conditional Multi-view Agent", "AI", pick(multi, "selected_cameras", "iteration_count", "decision", "final_confidence"),
             source=ai_source, trigger="MODEL_TOOL_CALL" if multi else "SYSTEM_WORKFLOW", states=("MULTI_VIEW",), status=multi_status,
             input=pick(first, "confidence", "evidence_sufficient", "ambiguity_type"), node_error=classify(multi.get("error"))),
        node("multi_view_cloud", "Multi-view Cloud Judgment", "AI", pick(multi.get("review"), *JUDGMENT_FIELDS), source=ai_source,
             trigger="MODEL_TOOL_CALL" if multi else "SYSTEM_WORKFLOW", states=("MULTI_VIEW",), status=multi_status,
             duration=None if replay else (multi.get("review") or {}).get("elapsed_ms"), evidence=_evidence(snapshot, {"evidence"}, set(multi.get("selected_cameras") or []))),
        node("business", "Business Decision / Fusion", "AI", {"evidence_fusion": snapshot.get("evidence_fusion"), "task_profile": event.get("task_profile"),
             "independent_second_review": pick(second, *JUDGMENT_FIELDS) if second else None} if snapshot.get("evidence_fusion") else {},
             states=("CLOUD_REVIEW", "HUMAN_REVIEW"), input=pick(review, *JUDGMENT_FIELDS)),
        node("verification", "固定摄像头 Verification", "AI", _verification_projection(verification),
             source=ai_source, states=("VERIFYING",), duration=None if replay else (verification or {}).get("elapsed_ms"), evidence=_evidence(snapshot, {"after"}),
             node_error=error if error and error["type"] == "VERIFICATION_ERROR" else None),
        node("spatial", "Camera → SLAM 四点映射", "SPATIAL", spatial, states=("LOCATED",), node_error=error if error and error["type"] == "SPATIAL_ERROR" else None),
        node("capability", "Capability 硬约束", "SPATIAL", pick(assignment, "candidate_count", "candidates", "status"), states=("ASSIGNED", "HUMAN_FALLBACK"), input=event.get("task_profile")),
        node("scheduler", "Scheduler 唯一机器人选择器", "SPATIAL", pick(assignment, "selected_robot_id", "selected_robot_name", "weights", "candidates", "candidate_count", "status"),
             states=("ASSIGNED", "HUMAN_FALLBACK"), status="ZERO_CANDIDATE / HUMAN_FALLBACK" if assignment.get("candidate_count") == 0 else None),
        node("dijkstra", "Dijkstra Global Topology Route", "SPATIAL", route, states=("NAVIGATING",),
             node_error=next((item for item in errors if item["type"] == "ROUTE_ERROR"), None)),
    ]
    calls = []
    for span in spans:
        calls.append({"id": span["span_id"], "trace_id": trace_id, "name": text(span["name"]),
                      "trigger_source": span["trigger_source"], "source": "DETERMINISTIC RUNTIME",
                      "start_time": span["started_at"], "duration_ms": span.get("duration_ms"), "status": span["status"],
                      "input_summary": {"event_id": event_id}, "result_summary": pick(span, "result_state")})
    for index, entry in enumerate(multi.get("audit") or []):
        if entry.get("source") != "MODEL_TOOL_CALL":
            continue
        calls.append({"id": entry.get("tool_call_id") or f"recorded-multi-{index}", "trace_id": trace_id, "name": text(entry.get("name")),
                      "trigger_source": "MODEL_TOOL_CALL", "source": ai_source, "start_time": entry.get("started_at"),
                      "duration_ms": entry.get("tool_duration_ms"), "status": entry.get("status"),
                      "input_summary": pick(entry.get("arguments"), "camera_id"),
                      "result_summary": pick(entry, "candidate_count", "candidates", "historical_elapsed_ms", "evidence_source")})
    for entry in audits:
        if entry.get("phase") not in {"tool", "operator_action"}:
            continue
        projected_error = classify({"type": "POLICY_REJECTED", "code": "POLICY_REJECTED"}) if entry.get("policy") == "REJECT" else None
        if projected_error and projected_error not in errors:
            errors.append(projected_error)
        result = entry.get("result") or {}
        calls.append({"id": f"ops-audit-{entry['id']}", "trace_id": entry.get("trace_id"), "name": text(entry.get("tool")),
                      "trigger_source": "USER_ACTION" if entry["phase"] == "operator_action" else "MODEL_TOOL_CALL", "source": "DETERMINISTIC RUNTIME",
                      "start_time": entry.get("started_at"), "duration_ms": entry.get("duration_ms"), "status": entry.get("policy"),
                      "input_summary": pick(entry.get("args"), "task_id", "event_id", "robot_id", "origin_poi", "destination_poi", "resource", "id"),
                      "result_summary": pick(result.get("result") if isinstance(result, dict) else {}, "task_id", "status", "robot_id", "source")})
    for request in requests:
        nodes.append(node(request["request_id"], "模型请求 · " + str(text(request.get("model"))), "RUNTIME", pick(request, "request_id", "trace_id", "model", "provider", "status", "tool_enabled"),
                          source="LIVE MODEL", duration=request.get("duration_ms"), status=request["status"], node_error=classify(request.get("error"))))
        nodes[-1]["start_time"] = request.get("started_at")
        nodes[-1]["trace_id"] = request.get("trace_id")
    configured = get_runtime().qwen_ready
    latest = requests[-1] if requests else None
    # Legacy successful provider results still show their saved historical latency;
    # they are not converted to new request records or new LIVE calls.
    last_result = verification or review or first
    runtime = {"provider": "DashScope", "model": text(latest.get("model")) if latest else text(last_result.get("model")),
               "configured": configured, "last_request_status": latest["status"] if latest else "REPLAY / NO_NEW_MODEL_CALL" if replay else "LEGACY_RECORDED" if last_result else "IDLE",
               "last_latency_ms": latest.get("duration_ms") if latest else None if replay else last_result.get("elapsed_ms"),
               "last_request_at": latest.get("started_at") if latest else None}
    reality = [
        {"component": "云端语义/验收", "status": ai_source if last_result else "AUTH REQUIRED / NOT CONNECTED", "execution_status": "RECORDED" if last_result else "NOT_RECORDED", "detail": "历史或本次已保存模型响应；配置存在不等于本次调用成功。", "replacement": "Configured Cloud VLM"},
        {"component": "YOLO / 摄像头证据", "status": "CONTROLLED EVIDENCE", "detail": "未配置生产YOLO权重；受控检测框和证据图，不是RTSP同步流。", "replacement": "Controlled Evidence → RTSP/VMS/NVR + validated YOLO"},
        {"component": "SLAM / Capability / Scheduler / Dijkstra", "status": "DETERMINISTIC RUNTIME", "detail": "已有确定性实现，当前执行结果见节点；Dijkstra不是Nav2或局部避障。", "replacement": "Validated maps / navigation adapter"},
        {"component": "机器人 / 电梯 / Skybridge / 门禁", "status": "POC SIMULATION", "detail": "无生产机器人遥测、真实电梯或门禁控制。", "replacement": "PoC Robot → Vendor Fleet API；PoC Elevator → Elevator IoT API"},
        {"component": "外部配送平台", "status": "AUTH REQUIRED / NOT CONNECTED", "detail": "、".join(DELIVERY_ADAPTERS) + "未接真实平台订单或回调。", "replacement": "PoC Delivery → Authorized Platform API"},
        {"component": "语音 ASR", "status": "AUTH REQUIRED / NOT CONNECTED", "detail": "麦克风disabled，未配置真实语音provider。", "replacement": "ASR Disabled → Configured Real ASR"},
        {"component": "Stable Replay", "status": "REPLAY", "execution_status": "SELECTED" if replay else "NOT_SELECTED", "detail": "仅响应回放，Spatial/Capability/Scheduler/Fleet/Verification workflow重新执行；LIVE失败不自动回放。", "replacement": None},
    ]
    return {"trace_id": trace_id, "trace_status": "RECORDED" if trace_id else "LEGACY_MISSING" if event_id else "NO_EVENT",
            "event_id": event_id, "mode": mode, "runtime": runtime, "events": [row for row in events if row["event_id"] == event_id], "nodes": nodes, "tool_calls": calls, "reality": reality, "errors": errors,
            "linked_tasks": [pick(task, "task_id", "trace_id", "event_id", "kind", "status", "robot_id") for task in tasks]}
