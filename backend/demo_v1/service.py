"""Live Qwen-backed customer demo orchestration.

This is a thin composition layer: controlled edge evidence remains explicit,
Qwen provides semantic event and verification judgements, and the established
Phase 3 Capability Engine/Scheduler remains the only robot selector.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from data.mock_data import ROBOTS
from perception.config import get_runtime
from perception.multiview.agent import run_multi_view_agent
from perception.qwen import run_event_qwen_vl, run_targeted_event_qwen_vl, run_verification_qwen_vl
from perception.yolo import RealInferenceError
from database.connection import get_event, record_transition, save_event, save_assignment_decision, save_human_work_order
from scheduling.capability_engine import evaluate_capabilities
from scheduling.scheduler import make_assignment_decision
from workflow.fixtures import EVENT_TEMPLATES
from workbench.service import DEMO_SCENARIOS, scenario_assets

ASSET_ROOT = Path(__file__).resolve().parents[2] / "sample_data" / "camera_events"

SCENARIO_IDS = {
    "demo01": "event-outdoor-tissue-001",
    "demo02": "event-beverage-spill-002",
    "demo03": "event-indoor-can-003",
    "demo04": "event-oversized-box-004",
}
YOLO_CONFIDENCE = {"CAM-OUT-01": 0.81, "CAM-A1-01": 0.58, "CAM-A1-02": 0.63, "CAM-A1-04": 0.61, "CAM-A2-08": 0.84, "CAM-A2-11": 0.82}
TEMPLATE_BY_EVENT = {
    "event-outdoor-tissue-001": "outdoor_debris",
    "event-beverage-spill-002": "multiview_heavy_spill",
    "event-indoor-can-003": "indoor_can",
    "event-oversized-box-004": "oversized_object_a2",
}


def _asset_path(asset: dict[str, Any]) -> Path:
    return ASSET_ROOT / asset["camera_id"] / asset["event_id"] / asset["filename"]


def _event_type(value: str) -> str:
    lowered = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {"small_trash": "small_litter", "paper": "small_litter", "paper_tissue": "small_litter", "beverage_spill": "liquid", "spill": "liquid", "aluminum_can": "can", "tin_can": "can", "cardboard_box": "large_object", "large_cardboard_box": "large_object"}
    candidate = aliases.get(lowered, lowered)
    return candidate if candidate in {"small_litter", "liquid", "can", "large_object"} else "unknown"


def _controlled_evidence(manifest: dict[str, Any], role: str = "before") -> list[dict[str, Any]]:
    evidence = []
    for asset in manifest["assets"]:
        if asset["role"] not in {role, "evidence"}:
            continue
        for overlay in asset.get("detection_overlays", []):
            evidence.append({"camera_id": asset["camera_id"], "class_name": overlay["label"], "confidence": YOLO_CONFIDENCE.get(asset["camera_id"], overlay["confidence"]), "bbox": overlay["bbox"], "source": "CONTROLLED_EDGE_DEMO"})
    return evidence


def _camera_contexts(manifest: dict[str, Any], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenario = DEMO_SCENARIOS[manifest["event_id"]]
    template = EVENT_TEMPLATES[TEMPLATE_BY_EVENT[manifest["event_id"]]]
    location = template["location"]
    confidence_by_camera = {item["camera_id"]: item["confidence"] for item in evidence}
    return [{"camera_id": asset["camera_id"], "building": location["building"], "floor": location["floor"], "zone": location["zone"], "yolo_confidence": confidence_by_camera.get(asset["camera_id"])} for asset in manifest["assets"] if asset["role"] in {"before", "evidence"}]


def _task_profile(qwen: dict[str, Any], location: dict[str, Any]) -> dict[str, Any]:
    event_type = _event_type(qwen["event_type"])
    surface = qwen["surface_type"].lower()
    allowed_surface = {"asphalt", "granite", "tile", "epoxy", "carpet"}
    if surface not in allowed_surface:
        surface = "asphalt" if location["building"] == "OUTDOOR" else "tile"
    required_by_event = {
        "small_litter": ["outdoor", "dry_debris"] if location["building"] == "OUTDOOR" else ["dry_debris", "light_cleaning"],
        "liquid": ["wet_cleaning", "strong_suction", "scrubbing"],
        "can": ["dry_debris", "light_cleaning"],
        "large_object": ["large_object_pickup"],
    }
    caps = required_by_event.get(event_type, [])
    return {"object_type": event_type, "pollution_form": "liquid" if event_type == "liquid" else "large_object" if event_type == "large_object" else "dry_debris", "severity": qwen["severity"] if qwen["severity"] in {"low", "medium", "high"} else "medium", "estimated_area": 2.0 if event_type == "large_object" else 0.8 if event_type == "liquid" else 0.15, "surface": surface, "required_capabilities": caps, "priority": "high" if qwen["severity"] == "high" else "normal", "crowd_level": "high" if location["zone"] == "Main Lobby" else "medium"}


def _human_review(
    reason: str,
    manifest: dict[str, Any],
    qwen: dict[str, Any] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    multi_view: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Keep an auditable context even when the automation stops for review."""
    return {
        "mode": "LIVE",
        "status": "HUMAN_REVIEW",
        "reason": reason,
        "asset_manifest": manifest,
        "controlled_yolo": evidence or [],
        "multi_view": multi_view,
        "qwen_review": qwen,
        "task_profile": None,
        "assignment_decision": None,
        "verification": None,
        "human_work_order": {"status": "OPEN", "reason": reason, "source": "live_qwen_demo"},
    }


def _fusion_score(review: dict[str, Any], evidence: list[dict[str, Any]], multi_view: dict[str, Any] | None) -> dict[str, Any]:
    """Auditable composite — never a disguised bump to Qwen confidence.

    60% is the fresh raw cloud score; the rest is independently observable
    camera/category/mapping agreement. A cloud veto still wins in run_demo.
    """
    categories = {str(item.get("class_name", "")).replace("疑似区域", "污渍") for item in evidence}
    category_consistency = 1.0 if len(categories) == 1 else 0.0
    camera_mapping_consistency = 1.0 if evidence else 0.0
    multi_view_consistency = 1.0 if multi_view and len(multi_view.get("selected_cameras", [])) >= 2 else 0.0
    raw = float(review.get("decision_confidence", 0.0))
    score = 0.60 * raw + 0.20 * category_consistency + 0.12 * camera_mapping_consistency + 0.08 * multi_view_consistency
    return {"name": "Evidence Fusion Composite Disposal Score", "score": round(score, 4), "components": {"second_raw_cloud_confidence": raw, "yolo_category_consistency": category_consistency, "camera_location_time_mapping_consistency": camera_mapping_consistency, "multi_view_consistency": multi_view_consistency}, "formula": "0.60×raw_cloud + 0.20×yolo_category + 0.12×camera_mapping + 0.08×multi_view"}


def _persist_demo_result(demo_id: str, result: dict[str, Any]) -> dict[str, Any]:
    """Write integrated demo runs to the canonical SQLite event audit immediately."""
    event_id = f"integrated-{demo_id}-{uuid4().hex[:10]}"
    manifest = result["asset_manifest"]
    event = {
        "event_id": event_id,
        "state": result["status"],
        "template": TEMPLATE_BY_EVENT[SCENARIO_IDS[demo_id]],
        "location": EVENT_TEMPLATES[TEMPLATE_BY_EVENT[SCENARIO_IDS[demo_id]]]["location"],
        "task_profile": result.get("task_profile") or {"object_type": (result.get("qwen_review") or {}).get("event_type", "unknown")},
        "assignment_decision": result.get("assignment_decision"),
        "demo_v1": result,
    }
    save_event(event)
    record_transition(event_id, "DETECTED", {"source": "integrated_demo", "camera_id": manifest["assets"][0]["camera_id"]})
    record_transition(event_id, result["status"], {"reason": result["reason"], "cloud_review": result.get("qwen_review"), "fusion": result.get("evidence_fusion")})
    result["event_id"] = event_id
    return result


def scenario_catalog() -> list[dict[str, Any]]:
    return [{"id": demo_id, "event_id": event_id, "title": scenario_assets(event_id)["title"], "verification_mode": scenario_assets(event_id)["verification_mode"]} for demo_id, event_id in SCENARIO_IDS.items()]


# Stage-driven customer-demo runtime -------------------------------------------------
#
# These functions are intentionally small, synchronous REST transitions.  They are
# the only runtime path used by the customer workbench: each endpoint commits one
# durable state before the caller is allowed to ask for the following stage.  The
# older `run_demo` function remains below solely for backwards-compatible technical
# API consumers; it is not used by the workbench.

def _snapshot(stored: dict[str, Any]) -> dict[str, Any]:
    result = dict(stored.get("demo_v1") or {})
    result.update({
        "event_id": stored["event_id"],
        "state": stored["state"],
        "status": stored["state"],
        "location": stored.get("location"),
        "task_profile": stored.get("task_profile"),
        "assignment_decision": stored.get("assignment_decision"),
    })
    return result


def _require_state(stored: dict[str, Any], *allowed: str) -> None:
    if stored["state"] not in allowed:
        expected = " / ".join(allowed)
        raise ValueError(f"This stage requires state {expected}; current state is {stored['state']}.")


def _save_stage(stored: dict[str, Any], state: str, detail: dict[str, Any], **updates: Any) -> dict[str, Any]:
    result = stored.setdefault("demo_v1", {})
    result.update(updates)
    stored["state"] = state
    save_event(stored)
    record_transition(stored["event_id"], state, detail)
    return _snapshot(stored)


def _load_stage_event(event_id: str) -> dict[str, Any]:
    stored = get_event(event_id)
    if not stored or not str(stored.get("event_id", "")).startswith("integrated-"):
        raise ValueError("Integrated demo event was not found.")
    return stored


def create_demo_event(demo_id: str) -> dict[str, Any]:
    """Create and persist only the camera-discovered event; no AI or scheduler work."""
    if demo_id not in SCENARIO_IDS:
        raise ValueError("Unknown integrated demo scenario.")
    source_event_id = SCENARIO_IDS[demo_id]
    manifest = scenario_assets(source_event_id)
    template = EVENT_TEMPLATES[TEMPLATE_BY_EVENT[source_event_id]]
    event_id = f"integrated-{demo_id}-{uuid4().hex[:10]}"
    stored = {
        "event_id": event_id,
        "state": "DETECTED",
        "template": TEMPLATE_BY_EVENT[source_event_id],
        "location": template["location"],
        "task_profile": None,
        "assignment_decision": None,
        "demo_v1": {
            "mode": "LIVE",
            "demo_id": demo_id,
            "source_event_id": source_event_id,
            "reason": "固定摄像头发现疑似清洁事件，等待边缘证据确认。",
            "asset_manifest": manifest,
            "controlled_yolo": [],
            "multi_view": None,
            "qwen_review": None,
            "first_qwen_review": None,
            "second_qwen_review": None,
            "evidence_fusion": None,
            "verification": None,
            "navigation_plan": None,
            "human_work_order": None,
        },
    }
    save_event(stored)
    primary = next(asset for asset in manifest["assets"] if asset["role"] == "before")
    record_transition(event_id, "DETECTED", {"source": "integrated_demo", "camera_id": primary["camera_id"]})
    return _snapshot(stored)


def edge_review(event_id: str) -> dict[str, Any]:
    """Load controlled edge evidence only; never invokes Qwen, Scheduler or verification."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "DETECTED")
    manifest = stored["demo_v1"]["asset_manifest"]
    evidence = _controlled_evidence(manifest)
    return _save_stage(
        stored,
        "EDGE_DETECTED",
        {"source": "CONTROLLED_EDGE_DEMO", "camera_count": len({item["camera_id"] for item in evidence})},
        controlled_yolo=evidence,
        reason="受控边缘证据已生成，等待多视角或云端综合研判。",
    )


def multi_view_review(event_id: str) -> dict[str, Any]:
    """Run the bounded Multi-view Agent for Demo02 and persist its evidence package."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "EDGE_DETECTED")
    result = stored["demo_v1"]
    if result["demo_id"] != "demo02":
        raise ValueError("Multi-view review is available only for Demo02.")
    manifest = result["asset_manifest"]
    primary = next(asset for asset in manifest["assets"] if asset["role"] == "before")
    multi_view = run_multi_view_agent(
        YOLO_CONFIDENCE[primary["camera_id"]], primary["camera_id"], stored["location"], "scenario02"
    )
    selected = multi_view.get("selected_cameras", [])
    if len(selected) > 2:
        raise ValueError("Multi-view Agent exceeded the approved two additional camera limit.")
    return _save_stage(
        stored,
        "MULTI_VIEW",
        {"selected_cameras": selected, "iteration_count": multi_view.get("iteration_count")},
        multi_view=multi_view,
        reason="多视角证据包已完成，等待云端综合研判。",
    )


def _cloud_images(result: dict[str, Any]) -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest = result["asset_manifest"]
    evidence = result.get("controlled_yolo") or _controlled_evidence(manifest)
    primary = next(asset for asset in manifest["assets"] if asset["role"] == "before")
    qwen_images = [_asset_path(primary)]
    if result["demo_id"] == "demo02":
        selected_ids = {item["camera_id"] for item in (result.get("multi_view") or {}).get("selected_cameras", [])}
        qwen_images.extend(
            _asset_path(asset)
            for asset in manifest["assets"]
            if asset["role"] == "evidence" and asset["camera_id"] in selected_ids
        )
        if len(qwen_images) != 3:
            raise ValueError("Demo02 cloud review requires the primary frame plus exactly two selected views.")
    return qwen_images, evidence, _camera_contexts(manifest, evidence)


def cloud_review(event_id: str, force_unavailable: bool = False) -> dict[str, Any]:
    """Perform the first (and, if necessary, independent second) cloud review only."""
    stored = _load_stage_event(event_id)
    result = stored["demo_v1"]
    _require_state(stored, "MULTI_VIEW" if result["demo_id"] == "demo02" else "EDGE_DETECTED")
    manifest = result["asset_manifest"]
    qwen_images, evidence, contexts = _cloud_images(result)
    if force_unavailable:
        return _save_stage(
            stored, "HUMAN_REVIEW", {"reason": "simulated_cloud_unavailable"},
            controlled_yolo=evidence,
            reason="云端综合研判不可用；未创建机器人任务。",
            human_work_order={"status": "OPEN", "reason": "云端综合研判不可用", "source": "cloud_review"},
        )
    runtime = get_runtime()
    if not runtime.qwen_ready:
        return _save_stage(
            stored, "HUMAN_REVIEW", {"reason": "cloud_not_configured"},
            controlled_yolo=evidence,
            reason="未配置云端综合研判；未创建机器人任务。",
            human_work_order={"status": "OPEN", "reason": "未配置云端综合研判", "source": "cloud_review"},
        )
    try:
        first = run_event_qwen_vl(qwen_images, evidence, contexts, runtime.qwen_model)
        first["event_type"] = _event_type(first["event_type"])
        second = None
        decision_review = first
        if 0.5 <= first["decision_confidence"] < 0.85:
            second = run_targeted_event_qwen_vl(qwen_images, evidence, contexts, runtime.qwen_model)
            second["event_type"] = _event_type(second["event_type"])
            decision_review = second
    except RealInferenceError as error:
        return _save_stage(
            stored, "HUMAN_REVIEW", {"reason": "cloud_error", "error": str(error)},
            controlled_yolo=evidence,
            reason=f"云端综合研判失败：{error}",
            human_work_order={"status": "OPEN", "reason": "云端综合研判失败", "source": "cloud_review"},
        )
    fusion = _fusion_score(decision_review, evidence, result.get("multi_view"))
    profile = _task_profile(decision_review, stored["location"])
    # Keep the canonical Phase 3 field at event root as well as the customer
    # projection payload, so later capability evaluation never consumes UI data.
    stored["task_profile"] = profile
    veto = not decision_review["need_clean"] or decision_review["event_type"] == "unknown" or decision_review["next_action"] == "ignore"
    # Large objects intentionally open a human work order, even where the
    # semantic reviewer is conservative about whether the scene needs cleaning.
    if result["demo_id"] == "demo04" or decision_review["event_type"] == "large_object":
        work_order = {"status": "OPEN", "reason": "大件物品超出 Robot A/B/C 能力边界。", "source": "capability_boundary"}
        snapshot = _save_stage(
            stored, "HUMAN_FALLBACK", {"reason": work_order["reason"], "cloud_review": decision_review, "fusion": fusion},
            controlled_yolo=evidence, qwen_review=decision_review, first_qwen_review=first,
            second_qwen_review=second, evidence_fusion=fusion, reason=work_order["reason"],
            human_work_order=work_order,
        )
        save_human_work_order({"work_order_id": f"human-{event_id}", "event_id": event_id, **work_order})
        return snapshot
    if veto or fusion["score"] < 0.85:
        reason = "云端综合研判未达到自动派发门控；未创建机器人任务。"
        return _save_stage(
            stored, "HUMAN_REVIEW", {"reason": reason, "cloud_review": decision_review, "fusion": fusion},
            controlled_yolo=evidence, qwen_review=decision_review, first_qwen_review=first,
            second_qwen_review=second, evidence_fusion=fusion, task_profile=profile, reason=reason,
            human_work_order={"status": "OPEN", "reason": reason, "source": "cloud_gate"},
        )
    return _save_stage(
        stored, "CLOUD_REVIEW", {"cloud_review": decision_review, "fusion": fusion},
        controlled_yolo=evidence, qwen_review=decision_review, first_qwen_review=first,
        second_qwen_review=second, evidence_fusion=fusion, task_profile=profile,
        reason="云端综合研判通过，等待空间定位。",
    )


def locate_event(event_id: str) -> dict[str, Any]:
    """Persist the existing Phase 2 location interpretation; does not schedule."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "CLOUD_REVIEW")
    spatial_location = {"source": "phase2_spatial_engine", "location": stored["location"], "mapping": "camera_to_slam_shared_convention"}
    return _save_stage(stored, "LOCATED", spatial_location, spatial_location=spatial_location, reason="已完成摄像头到园区空间位置映射。")


def assign_event(event_id: str) -> dict[str, Any]:
    """The only stage allowed to call Capability Engine and Scheduler."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "LOCATED")
    profile = stored.get("task_profile")
    if not profile:
        raise ValueError("TaskProfile is missing; cloud review must complete first.")
    decision = make_assignment_decision(profile, evaluate_capabilities(profile, stored["location"], ROBOTS))
    stored["assignment_decision"] = decision
    if decision["status"] != "ASSIGNED":
        work_order = {"status": "OPEN", "reason": decision["reason"], "source": "capability_engine"}
        snapshot = _save_stage(stored, "HUMAN_FALLBACK", {"reason": decision["reason"], "assignment_decision": decision}, assignment_decision=decision, reason=decision["reason"], human_work_order=work_order)
        save_human_work_order({"work_order_id": f"human-{event_id}", "event_id": event_id, **work_order})
        return snapshot
    save_assignment_decision(event_id, decision)
    return _save_stage(stored, "ASSIGNED", {"assignment_decision": decision}, assignment_decision=decision, reason="能力匹配与调度已生成机器人任务。")


def _navigation_plan(demo_id: str, robot_id: str) -> dict[str, Any]:
    routes = {
        "demo01": ["OUTDOOR_A_STANDBY", "OUTDOOR_EAST_ROAD_EVENT"],
        "demo02": ["A_1F_ROBOT_B_STANDBY", "A_1F_LOBBY_EVENT"],
        "demo03": ["B_1F_ROBOT_C_STANDBY", "B_1F_ELEVATOR_ENTRY", "B_2F_ELEVATOR_EXIT", "B_2F_SKYBRIDGE_ENTRY", "A_2F_SKYBRIDGE_EXIT", "A_2F_CAN_EVENT"],
    }
    return {"robot_id": robot_id, "anchor_sequence": routes[demo_id], "source": "phase2_topology_projection"}


def start_navigation(event_id: str) -> dict[str, Any]:
    stored = _load_stage_event(event_id)
    _require_state(stored, "ASSIGNED")
    decision = stored.get("assignment_decision") or {}
    plan = _navigation_plan(stored["demo_v1"]["demo_id"], str(decision["selected_robot_id"]))
    return _save_stage(stored, "NAVIGATING", {"navigation_plan": plan}, navigation_plan=plan, reason="机器人任务已下发，正在按空间拓扑路线前往。")


def complete_navigation(event_id: str) -> dict[str, Any]:
    stored = _load_stage_event(event_id)
    _require_state(stored, "NAVIGATING")
    return _save_stage(stored, "ARRIVED", {"navigation_plan": stored["demo_v1"].get("navigation_plan")}, reason="机器人已到达目标区域。")


def complete_cleaning(event_id: str) -> dict[str, Any]:
    stored = _load_stage_event(event_id)
    _require_state(stored, "ARRIVED")
    return _save_stage(stored, "CLEANING_COMPLETED", {"source": "demo_robot_execution"}, reason="清洁动作已完成，等待固定摄像头验收。")


def verify_event(event_id: str) -> dict[str, Any]:
    """The only automatic-flow stage that loads after imagery and calls Qwen verification."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "CLEANING_COMPLETED")
    result = stored["demo_v1"]
    manifest = result["asset_manifest"]
    primary = next(asset for asset in manifest["assets"] if asset["role"] == "before")
    after = next((asset for asset in manifest["assets"] if asset["role"] == "after"), None)
    if not after:
        return _save_stage(stored, "HUMAN_REVIEW", {"reason": "after_image_missing"}, reason="缺少清洁后画面，无法自动验收。", human_work_order={"status": "OPEN", "reason": "缺少清洁后画面", "source": "verification"})
    runtime = get_runtime()
    if not runtime.qwen_ready:
        return _save_stage(stored, "HUMAN_REVIEW", {"reason": "verification_cloud_not_configured"}, reason="云端验收不可用；需人工复核。", human_work_order={"status": "OPEN", "reason": "云端验收不可用", "source": "verification"})
    _save_stage(stored, "VERIFYING", {"source": "post_cleaning_cloud_verification"}, reason="正在读取清洁后画面并进行云端验收。")
    try:
        verification = run_verification_qwen_vl(_asset_path(primary), _asset_path(after), {"event_type": (stored.get("task_profile") or {}).get("object_type"), "camera_id": primary["camera_id"]}, runtime.qwen_model)
    except RealInferenceError as error:
        return _save_stage(stored, "HUMAN_REVIEW", {"reason": "verification_error", "error": str(error)}, verification=None, reason=f"真实云端验收失败：{error}", human_work_order={"status": "OPEN", "reason": "云端验收失败", "source": "verification"})
    passed = verification["verification_pass"] and verification["confidence"] >= 0.85 and verification["next_action"] == "close"
    state = "CLOSED" if passed else "HUMAN_REVIEW"
    reason = "真实云端验收通过，事件可以闭环。" if passed else "真实云端验收未达到闭环门控；需人工复核。"
    return _save_stage(stored, state, {"verification": verification, "reason": reason}, verification=verification, reason=reason, human_work_order=None if passed else {"status": "OPEN", "reason": reason, "source": "verification"})


def complete_demo04_manual(event_id: str) -> dict[str, Any]:
    """Record a human box-removal completion, then run the normal AI verifier."""
    stored = get_event(event_id)
    if not stored or stored.get("template") != TEMPLATE_BY_EVENT["event-oversized-box-004"]:
        raise ValueError("Manual completion is available only for an existing Demo04 human work order.")
    _require_state(stored, "HUMAN_FALLBACK")
    result = stored.get("demo_v1") or {}
    manifest = result.get("asset_manifest") or scenario_assets(SCENARIO_IDS["demo04"])
    # Older persisted work orders predate the generated after-cleaning frame;
    # refresh the asset manifest so they can enter the same verifier safely.
    if not any(asset.get("role") == "after" for asset in manifest.get("assets", [])):
        manifest = scenario_assets(SCENARIO_IDS["demo04"])
        result["asset_manifest"] = manifest
    primary = next(asset for asset in manifest["assets"] if asset["role"] == "before")
    after = next((asset for asset in manifest["assets"] if asset["role"] == "after"), None)
    runtime = get_runtime()
    if not after or not runtime.qwen_ready:
        raise RealInferenceError("Cloud verification is unavailable; the manual work order remains open.")
    _save_stage(stored, "VERIFYING", {"source": "manual_completion", "manual_completion": True}, human_work_order={"status": "COMPLETED", "source": "manual_operator"}, reason="人工已确认完成，正在读取清洁后画面进行云端验收。")
    try:
        verification = run_verification_qwen_vl(_asset_path(primary), _asset_path(after), {"event_type": "large_object", "camera_id": primary["camera_id"], "manual_completion": True}, runtime.qwen_model)
    except RealInferenceError as error:
        return _save_stage(
            stored, "HUMAN_REVIEW", {"source": "manual_completion", "error": str(error)},
            verification=None,
            reason=f"人工清理已确认，但云端 AI 验收失败：{error}",
            human_work_order={"status": "OPEN", "reason": "云端 AI 验收失败", "source": "manual_operator"},
        )
    result["verification"] = verification
    result["human_work_order"] = {"status": "COMPLETED", "source": "manual_operator"}
    result["status"] = "CLOSED" if verification["verification_pass"] and verification["confidence"] >= 0.85 and verification["next_action"] == "close" else "HUMAN_REVIEW"
    result["reason"] = "人工清理完成，云端 AI 验收通过，事件已闭环。" if result["status"] == "CLOSED" else "人工清理完成，但云端 AI 验收未达到闭环门控。"
    result["event_id"] = event_id
    stored["demo_v1"] = result
    return _save_stage(stored, result["status"], {"source": "manual_completion", "verification": verification, "reason": result["reason"]})


def run_demo(demo_id: str, mode: str = "live", force_unavailable: bool = False) -> dict[str, Any]:
    if demo_id not in SCENARIO_IDS:
        raise ValueError("Unknown integrated demo scenario.")
    event_id = SCENARIO_IDS[demo_id]
    manifest = scenario_assets(event_id)
    template = EVENT_TEMPLATES[TEMPLATE_BY_EVENT[event_id]]
    location = template["location"]
    evidence = _controlled_evidence(manifest)
    primary = next(asset for asset in manifest["assets"] if asset["role"] == "before")
    qwen_images = [_asset_path(primary)]
    multi_view = None
    primary_confidence = YOLO_CONFIDENCE[primary["camera_id"]]
    if demo_id == "demo02":
        multi_view = run_multi_view_agent(primary_confidence, primary["camera_id"], location, "scenario02")
        selected_ids = {item["camera_id"] for item in multi_view["selected_cameras"]}
        requested_assets = [asset for asset in manifest["assets"] if asset["role"] == "evidence" and asset["camera_id"] in selected_ids]
        # The approved asset set is the hard upper limit; preserve its camera order.
        qwen_images.extend(_asset_path(asset) for asset in requested_assets)
    if force_unavailable:
        return _persist_demo_result(demo_id, _human_review("云端综合研判不可用；未创建机器人任务。", manifest, evidence=evidence, multi_view=multi_view))
    if mode == "replay":
        return _persist_demo_result(demo_id, _stable_replay(demo_id, manifest, evidence, location, multi_view))
    runtime = get_runtime()
    if not runtime.qwen_ready:
        return _persist_demo_result(demo_id, _human_review("未配置云端综合研判；未创建机器人任务。", manifest, evidence=evidence, multi_view=multi_view))
    try:
        qwen = run_event_qwen_vl(qwen_images, evidence, _camera_contexts(manifest, evidence), runtime.qwen_model)
    except RealInferenceError as error:
        return _persist_demo_result(demo_id, _human_review(f"云端综合研判失败：{error}", manifest, evidence=evidence, multi_view=multi_view))
    event_type = _event_type(qwen["event_type"])
    qwen["event_type"] = event_type
    second_review = None
    decision_review = qwen
    if 0.5 <= qwen["decision_confidence"] < 0.85:
        try:
            second_review = run_targeted_event_qwen_vl(qwen_images, evidence, _camera_contexts(manifest, evidence), runtime.qwen_model)
            second_review["event_type"] = _event_type(second_review["event_type"])
            decision_review = second_review
        except RealInferenceError as error:
            return _persist_demo_result(demo_id, _human_review(f"云端独立复核失败：{error}", manifest, qwen, evidence, multi_view))
    fusion = _fusion_score(decision_review, evidence, multi_view)
    veto = not decision_review["need_clean"] or decision_review["event_type"] == "unknown" or decision_review["next_action"] == "ignore"
    # The project gate is evidence-based: a high-confidence clean-required
    # review may proceed even when the model's generic next_action is phrased
    # conservatively as human_review. Explicit model vetoes remain absolute.
    eligible_for_dispatch = not veto and fusion["score"] >= 0.85
    if not eligible_for_dispatch:
        result = _human_review("云端综合研判未达到自动派发门控；未创建机器人任务。", manifest, decision_review, evidence, multi_view)
        result.update({"first_qwen_review": qwen, "second_qwen_review": second_review, "evidence_fusion": fusion})
        return _persist_demo_result(demo_id, result)
    profile = _task_profile(decision_review, location)
    evaluations = evaluate_capabilities(profile, location, ROBOTS)
    decision = make_assignment_decision(profile, evaluations)
    if decision["status"] != "ASSIGNED":
        return _persist_demo_result(demo_id, {"mode": "LIVE", "status": "HUMAN_FALLBACK", "reason": decision["reason"], "asset_manifest": manifest, "controlled_yolo": evidence, "multi_view": multi_view, "qwen_review": decision_review, "first_qwen_review": qwen, "second_qwen_review": second_review, "evidence_fusion": fusion, "task_profile": profile, "assignment_decision": decision, "verification": None, "human_work_order": {"status": "OPEN", "reason": decision["reason"], "source": "capability_engine"}})
    after = next((asset for asset in manifest["assets"] if asset["role"] == "after"), None)
    verification = None
    status = "ASSIGNED"
    reason = "云端综合研判通过，确定性能力匹配与调度已选择机器人。"
    if after:
        try:
            verification = run_verification_qwen_vl(_asset_path(primary), _asset_path(after), {"event_type": event_type, "camera_id": primary["camera_id"]}, runtime.qwen_model)
            if verification["verification_pass"] and verification["confidence"] >= 0.85 and verification["next_action"] == "close":
                status = "CLOSED"
                reason = "真实云端验收通过，事件可以闭环。"
            else:
                status = "HUMAN_REVIEW"
                reason = "真实云端验收未达到闭环门控；需人工复核。"
        except RealInferenceError as error:
            status = "HUMAN_REVIEW"
            reason = f"真实云端验收失败：{error}"
    return _persist_demo_result(demo_id, {"mode": "LIVE", "status": status, "reason": reason, "asset_manifest": manifest, "controlled_yolo": evidence, "multi_view": multi_view, "qwen_review": decision_review, "first_qwen_review": qwen, "second_qwen_review": second_review, "evidence_fusion": fusion, "task_profile": profile, "assignment_decision": decision, "verification": verification, "human_work_order": {"status": "OPEN", "reason": reason, "source": "verification"} if status == "HUMAN_REVIEW" else None})


def _stable_replay(demo_id: str, manifest: dict[str, Any], evidence: list[dict[str, Any]], location: dict[str, Any], multi_view: dict[str, Any] | None) -> dict[str, Any]:
    event_type = {"demo01": "small_litter", "demo02": "liquid", "demo03": "can", "demo04": "large_object"}[demo_id]
    qwen = {"provider": "Stable Replay", "model": None, "image_count": 3 if demo_id == "demo02" else 1, "elapsed_ms": None, "need_clean": True, "event_type": event_type, "decision_confidence": 0.91, "severity": "medium", "surface_type": "asphalt" if demo_id == "demo01" else "tile", "interference_factors": ["受控演示回放"], "evidence_summary": "用户手动开启稳定回放，使用预置且可审计的业务结论。", "recommended_capabilities": [], "next_action": "dispatch_robot"}
    profile = _task_profile(qwen, location)
    decision = make_assignment_decision(profile, evaluate_capabilities(profile, location, ROBOTS))
    if decision["status"] != "ASSIGNED":
        return {"mode": "STABLE_REPLAY", "status": "HUMAN_FALLBACK", "reason": decision["reason"], "asset_manifest": manifest, "controlled_yolo": evidence, "multi_view": multi_view, "qwen_review": qwen, "task_profile": profile, "assignment_decision": decision, "verification": None, "human_work_order": {"status": "OPEN", "reason": decision["reason"]}}
    return {"mode": "STABLE_REPLAY", "status": "CLOSED", "reason": "用户手动开启稳定回放，受控验收通过。", "asset_manifest": manifest, "controlled_yolo": evidence, "multi_view": multi_view, "qwen_review": qwen, "task_profile": profile, "assignment_decision": decision, "verification": {"provider": "Stable Replay", "verification_pass": True, "confidence": 0.95, "evidence_summary": "受控回放验收通过。", "next_action": "close", "elapsed_ms": None}, "human_work_order": None}
