"""Live Qwen-backed customer demo orchestration.

This is a thin composition layer: controlled edge evidence remains explicit,
Qwen provides semantic event and verification judgements, and the established
Phase 3 Capability Engine/Scheduler remains the only robot selector.
"""

from __future__ import annotations

from pathlib import Path
from math import isfinite
from copy import deepcopy
from typing import Any
from uuid import uuid4
from threading import Lock, Thread
from time import sleep

from perception.config import get_agent_model, get_runtime
from perception.multiview.autonomous import RECOVERABLE_AMBIGUITIES, acquisition_contract, run_autonomous_acquisition
from perception.qwen import (
    TARGET_ROI_VERIFICATION_PROMPT_SHA256,
    run_event_qwen_vl,
    run_target_roi_verification,
    run_targeted_event_qwen_vl,
    run_verification_qwen_vl,
    validate_verification_response,
)
from perception.verification_evidence import build_verification_evidence
from perception.yolo import RealInferenceError
from database.connection import (
    get_event,
    get_fleet_state,
    get_transitions,
    record_transition,
    save_event,
    save_assignment_decision,
    save_human_work_order,
    update_fleet_robot,
    runtime_transaction,
)
from scheduling.capability_engine import evaluate_capabilities
from scheduling.scheduler import make_assignment_decision
from spatial.calibration import CalibrationError, map_pixel_to_slam
from spatial.route_planner import RouteNotFoundError, plan_route
from spatial.spatial_data import CAMERAS, MAPS
from demo_v1.replay import evidence_key, load_replay_bundle, save_live_bundle, validate_response
from demo_v1.perception_records import (
    PIPELINE_SCHEMA, RecordedToolTurns, load_perception_record,
    save_perception_record, validate_judgment,
)
from workflow.fixtures import EVENT_TEMPLATES
from workbench.service import DEMO_SCENARIOS, scenario_assets
from robot_operations.coordination import event_stage
from observability.errors import classify as classify_error

ASSET_ROOT = Path(__file__).resolve().parents[2] / "sample_data" / "camera_events"
_AUTONOMOUS_RUNS: set[str] = set()
_AUTONOMOUS_RUNS_LOCK = Lock()

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


def _validated_cloud_review(response: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(response, dict) or not isinstance(response.get("event_type"), str):
        raise RealInferenceError("Cloud event response is missing a valid event type.")
    response = {**response, "event_type": _event_type(response["event_type"])}
    validate_response(response, "event_review")
    validate_judgment(response)
    return response


def _controlled_evidence(manifest: dict[str, Any], role: str = "before") -> list[dict[str, Any]]:
    evidence = []
    for asset in manifest["assets"]:
        if asset["role"] not in {role, "evidence"}:
            continue
        for overlay in asset.get("detection_overlays", []):
            evidence.append({"camera_id": asset["camera_id"], "class_name": overlay["label"], "confidence": YOLO_CONFIDENCE.get(asset["camera_id"], overlay["confidence"]), "bbox": overlay["bbox"], "source": "CONTROLLED_EDGE_DEMO"})
    return evidence


def _camera_contexts(manifest: dict[str, Any], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    template = EVENT_TEMPLATES[TEMPLATE_BY_EVENT[manifest["event_id"]]]
    location = template["location"]
    confidence_by_camera = {item["camera_id"]: item["confidence"] for item in evidence}
    scene_context = manifest.get("scene_context") or {}
    return [{"camera_id": asset["camera_id"], "building": location["building"], "floor": location["floor"], "zone": location["zone"], "yolo_confidence": confidence_by_camera.get(asset["camera_id"]),
             "operational_context": scene_context if scene_context.get("camera_id") == asset["camera_id"] else {}}
            for asset in manifest["assets"] if asset["role"] in {"before", "evidence"}]


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


def _primary_asset(result: dict[str, Any]) -> dict[str, Any]:
    return next(asset for asset in result["asset_manifest"]["assets"] if asset["role"] == "before")


def _ground_point_from_bbox(bbox: dict[str, Any], event_type: str) -> tuple[float, float, str]:
    """Convert the reviewed normalised bbox into the calibration pixel domain.

    Controlled source frames are 1448×1086, while the Phase 2 calibration
    contract is explicitly 100..900 × 100..700.  The normalisation is kept in
    this one audited function so Camera→SLAM cannot silently mix image spaces.
    """
    try:
        x1, y1, x2, y2 = (float(bbox[key]) for key in ("x1", "y1", "x2", "y2"))
    except (KeyError, TypeError, ValueError) as error:
        raise CalibrationError("Bounding box coordinates are missing or invalid.") from error
    if not all(isfinite(value) for value in (x1, y1, x2, y2)) or not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        raise CalibrationError("Bounding box must be finite, ordered and within the source frame.")
    center_x = (x1 + x2) / 2
    # Liquid has no physical bottom edge.  Its lower region is the defined
    # representative point; discrete objects use bbox bottom-centre.
    normalized_y = y1 + (y2 - y1) * (0.65 if event_type == "liquid" else 1.0)
    return (100 + center_x * 800, 100 + normalized_y * 600, "region_lower_center" if event_type == "liquid" else "bbox_bottom_center")


def _located_position(result: dict[str, Any], event_type: str) -> dict[str, Any]:
    primary = _primary_asset(result)
    overlay = next(iter(primary.get("detection_overlays", [])), None)
    if not overlay or not isinstance(overlay.get("bbox"), dict):
        raise CalibrationError("Primary controlled edge evidence has no mappable bounding box.")
    u, v, representative_point = _ground_point_from_bbox(overlay["bbox"], event_type)
    mapped = map_pixel_to_slam(primary["camera_id"], u, v)
    location = mapped.get("location", {})
    map_data = next((item for item in MAPS if item["map_id"] == location.get("map_id")), None)
    x, y = location.get("x"), location.get("y")
    if (not map_data or any(isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) for value in (x, y))
            or not 0 <= x <= map_data["width"] or not 0 <= y <= map_data["height"]
            or location.get("building") != map_data["building"] or location.get("floor") != map_data["floor"]):
        raise CalibrationError("Mapping did not produce a valid SLAM coordinate in the expected map.")
    return {
        "source": "camera_to_slam_phase2",
        "mapping_method": "four_point_homography",
        "representative_point": representative_point,
        "camera_id": primary["camera_id"],
        "bbox": overlay["bbox"],
        "pixel": mapped["pixel"],
        **location,
    }




def _fusion_score(review: dict[str, Any], evidence: list[dict[str, Any]], multi_view: dict[str, Any] | None) -> dict[str, Any]:
    """Auditable composite — never a disguised bump to Qwen confidence.

    60% is the fresh raw cloud score; the rest is independently observable
    camera/category/mapping agreement. A cloud veto still wins in run_demo.
    """
    categories = {str(item.get("class_name", "")).replace("疑似区域", "污渍") for item in evidence}
    category_consistency = 1.0 if len(categories) == 1 else 0.0
    camera_mapping_consistency = 1.0 if evidence else 0.0
    # One legal supporting camera plus the primary already is multi-view.
    # Count successful fetched evidence, never candidates or metadata alone.
    successful_fetches = {item.get("arguments", {}).get("camera_id") for item in (multi_view or {}).get("audit", [])
                          if item.get("name") == "fetch_camera_evidence" and item.get("status") == "OK"}
    fetched_assets = {item.get("camera_id") for item in (multi_view or {}).get("evidence_assets", [])}
    final_view = (multi_view or {}).get("review") or {}
    multi_view_consistency = float(bool(successful_fetches & fetched_assets)
                                   and final_view.get("evidence_sufficient") is True
                                   and final_view.get("image_count", 0) >= 2)
    raw = float(review.get("decision_confidence", 0.0))
    score = 0.60 * raw + 0.20 * category_consistency + 0.12 * camera_mapping_consistency + 0.08 * multi_view_consistency
    return {"name": "Evidence Fusion Composite Disposal Score", "score": round(score, 4), "components": {"second_raw_cloud_confidence": raw, "yolo_category_consistency": category_consistency, "camera_location_time_mapping_consistency": camera_mapping_consistency, "multi_view_consistency": multi_view_consistency}, "formula": "0.60×raw_cloud + 0.20×yolo_category + 0.12×camera_mapping + 0.08×multi_view"}




def scenario_catalog() -> list[dict[str, Any]]:
    return [{"id": demo_id, "event_id": event_id, "title": scenario_assets(event_id)["title"], "verification_mode": scenario_assets(event_id)["verification_mode"]} for demo_id, event_id in SCENARIO_IDS.items()]


def start_autonomous_progression(event_id: str) -> None:
    """Run the official event flow from durable backend state, never React.

    Each handler commits its own state. A navigation pause/cancel or a human
    fallback ends this worker safely; reopening or closing a chat cannot alter
    the persisted progress. A process restart leaves the latest state durable
    and a launcher/startup recovery may resume a non-terminal event later.
    """
    with _AUTONOMOUS_RUNS_LOCK:
        if event_id in _AUTONOMOUS_RUNS:
            return
        _AUTONOMOUS_RUNS.add(event_id)

    def progress() -> None:
        handlers = {
            "DETECTED": edge_review,
            "EDGE_DETECTED": cloud_review,
            "CLOUD_REVIEW": locate_event,
            "LOCATED": assign_event,
            "ASSIGNED": start_navigation,
            "NAVIGATING": complete_navigation,
            "ARRIVED": complete_cleaning,
            "CLEANING_COMPLETED": verify_event,
        }
        try:
            while True:
                stored = get_event(event_id)
                if not stored or stored.get("operations_control") in {"PAUSED", "CANCELLED"}:
                    return
                handler = handlers.get(str(stored.get("state")))
                if handler is None:
                    return
                # Keep state changes observable in the business timeline and
                # allow planned navigation to be seen before arrival.
                if stored.get("state") == "NAVIGATING":
                    sleep(2.0)
                handler(event_id)
                sleep(0.25)
        except (ValueError, RealInferenceError):
            # The stage itself has already recorded HUMAN_REVIEW when that is
            # appropriate. Never fabricate a fallback or silently replay.
            return
        finally:
            with _AUTONOMOUS_RUNS_LOCK:
                _AUTONOMOUS_RUNS.discard(event_id)

    Thread(target=progress, name=f"demo-progress-{event_id[-8:]}", daemon=True).start()


# Stage-driven customer-demo runtime -------------------------------------------------
#
# These functions are intentionally small, synchronous REST transitions.  They are
# the only runtime path used by the customer workbench: each endpoint commits one
# durable state before the caller is allowed to ask for the following stage.  The
# `run_demo` compatibility helper delegates to these same stages; its old HTTP
# endpoint is retired and no second runtime or synthetic replay path exists.

def available_evidence_manifest(result: dict[str, Any], state: str, transitions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return the customer/Agent consumable evidence set, never the full asset store.

    The repository manifest deliberately remains complete so the authoritative
    runtime can obtain assets at the correct future stage.  It is *not* a
    business evidence list.  Every external projection must use this gate.
    """
    manifest = deepcopy(result.get("asset_manifest") or {})
    assets = manifest.get("assets") if isinstance(manifest.get("assets"), list) else []
    states = {state, *(item.get("state") for item in (transitions or []) if isinstance(item, dict))}
    multi_view = result.get("multi_view") if isinstance(result.get("multi_view"), dict) else {}
    acquired = {
        asset.get("camera_id") for asset in multi_view.get("evidence_assets", [])
        if isinstance(asset, dict) and asset.get("camera_id")
    }
    after_released = "VERIFYING" in states or bool(result.get("verification"))
    visible: list[dict[str, Any]] = []
    for asset in assets:
        role = asset.get("role")
        if role == "before":
            visible.append(asset)
        elif role == "evidence" and asset.get("camera_id") in acquired:
            visible.append(asset)
        elif role == "after" and after_released:
            visible.append(asset)
    manifest["assets"] = visible
    manifest["availability"] = {
        "primary_before": True,
        "supporting_camera_ids": sorted(str(item) for item in acquired),
        "after_released": after_released,
    }
    return manifest


def _snapshot(stored: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(stored.get("demo_v1") or {})
    transitions = stored.get("transitions", [])
    result["asset_manifest"] = available_evidence_manifest(result, str(stored.get("state", "DETECTED")), transitions)
    if str(stored.get("state")) == "DETECTED":
        result["controlled_yolo"] = []
    result.update({
        "event_id": stored["event_id"],
        "state": stored["state"],
        "status": stored["state"],
        "location": stored.get("location"),
        "task_profile": stored.get("task_profile"),
        "assignment_decision": stored.get("assignment_decision"),
        "created_at": stored.get("created_at"),
        "updated_at": stored.get("updated_at"),
        "operations_task_id": stored.get("operations_task_id"),
        "operations_control": stored.get("operations_control"),
        "operations_pause_started_at": stored.get("operations_pause_started_at"),
        "operations_paused_ms": stored.get("operations_paused_ms", 0),
        "transitions": transitions,
    })
    return result


def customer_event_snapshot(event_id: str) -> dict[str, Any]:
    """The only public integrated-event projection used by customer surfaces."""
    stored = _load_stage_event(event_id)
    stored["transitions"] = get_transitions(event_id)
    return _snapshot(stored)


def _require_state(stored: dict[str, Any], *allowed: str) -> None:
    if stored.get("operations_control") in {"PAUSED", "CANCELLED"}:
        raise ValueError("Operations task is paused or cancelled; workflow advancement is blocked.")
    if stored["state"] not in allowed:
        expected = " / ".join(allowed)
        raise ValueError(f"This stage requires state {expected}; current state is {stored['state']}.")


def _save_stage(stored: dict[str, Any], state: str, detail: dict[str, Any], **updates: Any) -> dict[str, Any]:
    projected_error = classify_error(updates.get("error"))
    if projected_error:
        updates["error"] = {**updates["error"], "error_type": projected_error["type"]}
    result = stored.setdefault("demo_v1", {})
    result.update(updates)
    stored["state"] = state
    save_event(stored)
    record_transition(stored["event_id"], state, detail)
    refreshed = get_event(stored["event_id"]) or stored
    refreshed["transitions"] = get_transitions(stored["event_id"])
    return _snapshot(refreshed)


def _load_stage_event(event_id: str) -> dict[str, Any]:
    stored = get_event(event_id)
    if not stored or not str(stored.get("event_id", "")).startswith("integrated-"):
        raise ValueError("Integrated demo event was not found.")
    return stored


def create_demo_event(demo_id: str, mode: str = "LIVE") -> dict[str, Any]:
    """Create and persist only the camera-discovered event; no AI or scheduler work."""
    if demo_id not in SCENARIO_IDS:
        raise ValueError("Unknown integrated demo scenario.")
    source_event_id = SCENARIO_IDS[demo_id]
    manifest = scenario_assets(source_event_id)
    template = EVENT_TEMPLATES[TEMPLATE_BY_EVENT[source_event_id]]
    event_id = f"integrated-{demo_id}-{uuid4().hex[:10]}"
    normalized_mode = mode.upper()
    if normalized_mode not in {"LIVE", "STABLE_REPLAY"}:
        raise ValueError("Unsupported runtime mode.")
    stored = {
        "event_id": event_id,
        "source": "INTERVIEW_RUNTIME",
        "state": "DETECTED",
        "template": TEMPLATE_BY_EVENT[source_event_id],
        "location": template["location"],
        "task_profile": None,
        "assignment_decision": None,
        "demo_v1": {
            "mode": normalized_mode,
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
    refreshed = get_event(event_id) or stored
    refreshed["transitions"] = get_transitions(event_id)
    return _snapshot(refreshed)


@event_stage
def edge_review(event_id: str) -> dict[str, Any]:
    """Load controlled edge evidence only; never invokes Qwen, Scheduler or verification."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "DETECTED")
    manifest = stored["demo_v1"]["asset_manifest"]
    evidence = _controlled_evidence({**manifest, "assets": [_primary_asset(stored["demo_v1"])]})
    return _save_stage(
        stored,
        "EDGE_DETECTED",
        {"source": "CONTROLLED_EDGE_DEMO", "camera_count": len({item["camera_id"] for item in evidence})},
        controlled_yolo=evidence,
        reason="主摄像头受控边缘证据已生成，等待单视角云端语义研判。",
    )


def multi_view_review(event_id: str) -> dict[str, Any]:
    """Retired manual entry: acquisition is owned by the cloud evidence gate."""
    _load_stage_event(event_id)
    raise ValueError("Multi-view is evidence-gated inside cloud-review, not a caller-selected stage.")


def _cloud_images(result: dict[str, Any], selected_ids: set[str] | None = None) -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    """Never disclose supporting pixels/edge labels until legally acquired."""
    manifest = result["asset_manifest"]
    selected_ids = selected_ids or set()
    assets = [_primary_asset(result)] + [
        asset for asset in manifest["assets"]
        if asset["role"] == "evidence" and asset["camera_id"] in selected_ids
    ]
    filtered = {**manifest, "assets": assets}
    evidence = _controlled_evidence(filtered)
    return [_asset_path(asset) for asset in assets], evidence, _camera_contexts(filtered, evidence)


def _perception_failure(stored: dict, code: str, message: str) -> dict:
    return _save_stage(
        stored, "HUMAN_REVIEW", {"reason": code},
        error={"error_type": "PERCEPTION_ERROR", "code": code, "message": message},
        reason=message,
        human_work_order={"status": "OPEN", "reason": message, "source": "cloud_gate"},
    )


def _one_transient_retry(call):
    """Retry a provider transport failure exactly once; never retry semantics."""
    try:
        return call()
    except RealInferenceError as first:
        message = str(first).lower()
        transient = any(token in message for token in ("timeout", "timed out", "temporar", "connection", "rate limit", "429", "502", "503", "504"))
        if not transient:
            raise
        return call()


@event_stage
def cloud_review(event_id: str, force_unavailable: bool = False) -> dict[str, Any]:
    """Single view → evidence acquisition → final confidence → independent review.

    Only external model responses are replayable. Coverage, evidence fetch,
    gates, Fusion and every later business stage execute for the new event.
    """
    stored = _load_stage_event(event_id)
    _require_state(stored, "EDGE_DETECTED")
    result = stored["demo_v1"]
    manifest = result["asset_manifest"]
    images, evidence, contexts = _cloud_images(result)
    result["cloud_context"] = contexts
    replay = result.get("mode") == "STABLE_REPLAY"
    runtime = get_runtime()
    if force_unavailable:
        return _perception_failure(stored, "simulated_cloud_unavailable", "云端综合研判不可用；未创建机器人任务。")
    if not replay and not runtime.qwen_ready:
        return _perception_failure(stored, "cloud_not_configured", "未配置云端综合研判；未创建机器人任务。")

    try:
        # Hashing available evidence is a cache-compatibility check, not a model
        # disclosure: the initial provider request still receives ONE image.
        available_assets = [asset for asset in manifest["assets"] if asset["role"] in {"before", "evidence"}]
        key = evidence_key(
            [_asset_path(asset) for asset in available_assets],
            {"pipeline": PIPELINE_SCHEMA, "evidence": evidence, "cameras": contexts,
             "asset_cameras": [asset["camera_id"] for asset in available_assets],
             "camera_coverage": CAMERAS, "agent_model": get_agent_model(), "agent_contract": acquisition_contract()},
            runtime.qwen_model,
        )
        bundle = load_perception_record(stored, key) if replay else None
        first = _validated_cloud_review(bundle["responses"]["first"] if replay else _one_transient_retry(lambda: run_event_qwen_vl(images, evidence, contexts, runtime.qwen_model)))
    except RealInferenceError as error:
        return _perception_failure(stored, "replay_record_unavailable" if replay else "cloud_error", str(error))

    _save_stage(stored, "SINGLE_VIEW_REVIEW", {
        "confidence": first["decision_confidence"], "evidence_sufficient": first["evidence_sufficient"],
        "ambiguity_type": first["ambiguity_type"], "source": "REPLAY" if replay else "LIVE_MODEL",
    }, first_qwen_review=first, qwen_review=first, reason="单视角研判已返回，正在检查证据充分性。")
    final = first
    turns = []
    if not first["evidence_sufficient"]:
        if first["ambiguity_type"] not in RECOVERABLE_AMBIGUITIES:
            return _perception_failure(stored, "unrecoverable_ambiguity", "当前证据不足且无法通过额外视角缓解，转人工复核。")
        try:
            # This is only a Coverage query hint. The dispatch location is still
            # written exclusively by the later explicit Locate stage.
            coverage_location = _located_position(result, first["event_type"])
        except (CalibrationError, KeyError, TypeError, ValueError, StopIteration) as error:
            return _save_stage(stored, "HUMAN_REVIEW", {"error_type": "SPATIAL_ERROR", "reason": str(error)},
                               error={"error_type": "SPATIAL_ERROR", "code": "CAMERA_MAPPING_FAILED", "message": str(error)},
                               reason="证据获取前的 Camera→SLAM 定位失败；不会派发任务。")
        result["multi_view"] = {"audit": [], "selected_cameras": [], "decision": None, "iteration_count": 0}
        def persist_audit(entry: dict) -> None:
            result["multi_view"]["audit"].append(entry)
            if entry.get("name") == "fetch_camera_evidence" and entry.get("status") == "OK":
                result["multi_view"]["selected_cameras"].append(entry["arguments"]["camera_id"])
            if entry.get("name") == "agent_start" and stored["state"] != "MULTI_VIEW":
                _save_stage(stored, "MULTI_VIEW", {"source": "REPLAY" if replay else "LIVE_MODEL"},
                            reason="证据不足，Multi-view Agent 正在调用工具获取合法补充视角。")
            else:
                save_event(stored)

        feed = RecordedToolTurns(bundle["model_turns"]) if replay else None
        acquired = run_autonomous_acquisition(
            initial_review=first, primary_asset=_primary_asset(result), primary_path=images[0],
            location=coverage_location, supporting_assets=manifest["assets"], model=get_agent_model(),
            resolve_asset=_asset_path, on_audit=persist_audit,
            request_turn=feed, response_source="REPLAY" if replay else "LIVE_MODEL",
            primary_context={"cameras": contexts, "edge_evidence": evidence},
        )
        result["multi_view"] = {key: value for key, value in acquired.items() if key != "model_turns"}
        turns = acquired["model_turns"]
        result["multi_view"]["model_requests"] = [
            {field: turn.get(field) for field in ("turn", "source", "elapsed_ms", "historical_elapsed_ms")}
            for turn in turns
        ]
        final = acquired["review"]
        if replay:
            try:
                feed.assert_consumed()
            except RealInferenceError as error:
                return _perception_failure(stored, "replay_execution_mismatch", str(error))
            # Use archived attribution only after legal tools have re-executed.
            saved_final = bundle["responses"]["final"]
            if any(final.get(field) != saved_final.get(field) for field in ("need_clean", "event_type", "decision_confidence", "evidence_sufficient", "ambiguity_type")):
                return _perception_failure(stored, "replay_execution_mismatch", "回放工具执行结果与已保存语义结果不一致。")
            final = saved_final
            result["multi_view"]["review"] = final
        result["qwen_review"] = final
        if acquired["error"] or not final["evidence_sufficient"]:
            return _perception_failure(stored, acquired["error"] or "final_evidence_insufficient", "合法多视角证据不足或获取失败，转人工复核。")
        images, evidence, contexts = _cloud_images(result, set(acquired["selected_cameras"]))
        result["cloud_context"] = contexts
    elif replay and bundle["model_turns"]:
        return _perception_failure(stored, "replay_execution_mismatch", "充分的单视角记录不得包含额外 Agent 调用。")

    second = None
    try:
        if final["evidence_sufficient"] and 0.50 <= final["decision_confidence"] < 0.85:
            # Fresh independent judgment: only the legally acquired image set
            # and factual camera/edge context, never a previous model answer.
            second = _validated_cloud_review(bundle["responses"]["second"] if replay else _one_transient_retry(lambda: run_targeted_event_qwen_vl(images, evidence, contexts, runtime.qwen_model)))
        if not replay:
            save_perception_record(stored, key, first, final, second, turns)
    except RealInferenceError as error:
        return _perception_failure(stored, "cloud_error", str(error))
    decision_review = second or final
    result.update({"qwen_review": decision_review, "second_qwen_review": second, "controlled_yolo": evidence})
    if result.get("multi_view"):
        result["multi_view"].update({
            "final_confidence": decision_review["decision_confidence"],
            "decision": "HUMAN_REVIEW" if not decision_review["evidence_sufficient"] or decision_review["decision_confidence"] < 0.50
            else "CONFIRM" if decision_review["need_clean"] else "REJECT",
        })
    if not decision_review["evidence_sufficient"] or decision_review["decision_confidence"] < 0.50:
        return _perception_failure(stored, "final_evidence_or_confidence_gate", "最终证据不足或置信度低于 0.50；转人工复核。")

    fusion = _fusion_score(decision_review, evidence, result.get("multi_view"))
    profile = _task_profile(decision_review, stored["location"])
    stored["task_profile"] = profile
    veto = not decision_review["need_clean"] or decision_review["event_type"] == "unknown"
    updates = dict(controlled_yolo=evidence, qwen_review=decision_review, first_qwen_review=first,
                   second_qwen_review=second, evidence_fusion=fusion, task_profile=profile)
    if veto or fusion["score"] < 0.85:
        reason = "云端综合研判未达到自动派发门控；未创建机器人任务。"
        return _save_stage(stored, "HUMAN_REVIEW", {"reason": reason, "cloud_review": decision_review, "fusion": fusion},
                           **updates, reason=reason, human_work_order={"status": "OPEN", "reason": reason, "source": "cloud_gate"})
    return _save_stage(stored, "CLOUD_REVIEW", {"cloud_review": decision_review, "fusion": fusion},
                       **updates, reason="云端综合研判通过，等待空间定位。")


@event_stage
def locate_event(event_id: str) -> dict[str, Any]:
    """Map the primary detection through the shared Phase 2 calibration."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "CLOUD_REVIEW")
    event_type = str((stored.get("task_profile") or {}).get("object_type", "unknown"))
    try:
        spatial_location = _located_position(stored["demo_v1"], event_type)
    except (CalibrationError, KeyError, TypeError, ValueError, StopIteration) as error:
        return _save_stage(
            stored, "HUMAN_REVIEW", {"error_type": "SPATIAL_ERROR", "reason": str(error)},
            error={"error_type": "SPATIAL_ERROR", "code": "CAMERA_MAPPING_FAILED", "message": str(error)},
            spatial_location=None,
            reason=f"摄像头空间定位失败：{error}",
            human_work_order={"status": "OPEN", "reason": "摄像头空间定位失败", "source": "camera_to_slam"},
        )
    # The mapped location becomes the only dispatch/route target.  The old
    # fixture location remains only as the scenario's pre-detection context.
    stored["location"] = {key: spatial_location[key] for key in ("building", "floor", "zone", "map_id", "x", "y")}
    return _save_stage(stored, "LOCATED", spatial_location, spatial_location=spatial_location, reason="已通过四点标定完成摄像头到园区空间位置映射。")


@event_stage
@runtime_transaction()
def assign_event(event_id: str) -> dict[str, Any]:
    """The only stage allowed to call Capability Engine and Scheduler."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "LOCATED")
    profile = stored.get("task_profile")
    if not profile:
        raise ValueError("TaskProfile is missing; cloud review must complete first.")
    fleet = [robot for robot in get_fleet_state() if robot["id"] in {"robot-a", "robot-b", "robot-c"}]
    decision = make_assignment_decision(profile, evaluate_capabilities(profile, stored["location"], fleet))
    stored["assignment_decision"] = decision
    save_assignment_decision(event_id, decision)
    if decision["status"] != "ASSIGNED":
        work_order = {"status": "OPEN", "reason": decision["reason"], "source": "capability_engine"}
        snapshot = _save_stage(stored, "HUMAN_FALLBACK", {"reason": decision["reason"], "assignment_decision": decision}, assignment_decision=decision, reason=decision["reason"], human_work_order=work_order)
        save_human_work_order({"work_order_id": f"human-{event_id}", "event_id": event_id, **work_order})
        return snapshot
    robot = update_fleet_robot(
        str(decision["selected_robot_id"]), status="assigned", active_event_id=event_id,
        active_task_id=stored.get("operations_task_id"),
    )
    return _save_stage(stored, "ASSIGNED", {"assignment_decision": decision, "fleet_robot": robot}, assignment_decision=decision, fleet_snapshot=get_fleet_state(), reason="能力匹配与调度已生成机器人任务。")


@event_stage
@runtime_transaction()
def start_navigation(event_id: str) -> dict[str, Any]:
    stored = _load_stage_event(event_id)
    _require_state(stored, "ASSIGNED")
    decision = stored.get("assignment_decision") or {}
    robot_id = str(decision["selected_robot_id"])
    robot = next((item for item in get_fleet_state() if item["id"] == robot_id), None)
    if robot is None:
        return _save_stage(stored, "HUMAN_REVIEW", {"error_type": "ROUTE_ERROR", "reason": "fleet robot missing"}, reason="Fleet 中未找到已派发机器人。")
    try:
        plan = plan_route(str(robot["map_id"]), str(stored["location"]["map_id"]))
    except RouteNotFoundError as error:
        return _save_stage(stored, "HUMAN_REVIEW", {"error_type": "ROUTE_ERROR", "reason": str(error)}, reason=f"拓扑路线规划失败：{error}")
    plan.update({"robot_id": robot_id, "source": "dijkstra_global_topology_planner", "display_anchors": plan["node_path"]})
    update_fleet_robot(robot_id, status="navigating", active_event_id=event_id)
    return _save_stage(stored, "NAVIGATING", {"navigation_plan": plan}, navigation_plan=plan, fleet_snapshot=get_fleet_state(), reason="机器人已按 Dijkstra 园区拓扑路线前往目标区域。")


@event_stage
@runtime_transaction()
def complete_navigation(event_id: str) -> dict[str, Any]:
    stored = _load_stage_event(event_id)
    _require_state(stored, "NAVIGATING")
    decision = stored.get("assignment_decision") or {}
    target = stored["location"]
    robot = update_fleet_robot(
        str(decision["selected_robot_id"]), status="arrived", map_id=target["map_id"],
        coordinates={"x": target["x"], "y": target["y"]}, building=target["building"], floor=target["floor"],
        zone=target["zone"], location=f"{target['building']} 栋 {target['floor']} · {target['zone']}", active_event_id=event_id,
    )
    return _save_stage(stored, "ARRIVED", {"navigation_plan": stored["demo_v1"].get("navigation_plan"), "fleet_robot": robot}, fleet_snapshot=get_fleet_state(), reason="机器人已到达目标区域。")


@event_stage
@runtime_transaction()
def complete_cleaning(event_id: str) -> dict[str, Any]:
    stored = _load_stage_event(event_id)
    _require_state(stored, "ARRIVED")
    decision = stored.get("assignment_decision") or {}
    update_fleet_robot(str(decision["selected_robot_id"]), status="cleaning", active_event_id=event_id)
    return _save_stage(stored, "CLEANING_COMPLETED", {"source": "poc_robot_execution"}, fleet_snapshot=get_fleet_state(), reason="清洁动作已完成，等待固定摄像头验收。")


def _verification_closes(verification: dict[str, Any] | None) -> bool:
    """The existing terminal verification gate, kept in one audited predicate."""
    return bool(
        verification
        and verification.get("verification_pass") is True
        and verification.get("confidence", 0) >= 0.85
        and verification.get("next_action") == "close"
    )


def _independent_roi_context(context: dict[str, Any]) -> dict[str, Any]:
    """Select only factual target evidence for the bounded independent review."""
    return {
        "verification_contract": context["verification_contract"],
        "roi_source": context["roi_source"],
        "target": context["target"],
        "event_type": context.get("event_type"),
        "camera_id": context.get("camera_id"),
        "manual_completion": context.get("manual_completion", False),
    }


def _validate_replayed_verification(verification: dict[str, Any]) -> None:
    """Reject a legacy failed record that lacks its required independent ROI turn."""
    validate_verification_response(verification)
    first_present = "first_review" in verification
    if first_present:
        first = verification.get("first_review")
        if not isinstance(first, dict):
            raise RealInferenceError("Replay independent ROI record has an invalid primary verification response.")
        validate_verification_response(first)
        # Once a record claims a primary response, it cannot masquerade as an
        # old primary-pass bundle: a failed first response always requires the
        # one bounded independent ROI result and its exact prompt contract.
        if verification.get("independent_roi_review") is not True:
            raise RealInferenceError("Replay verification record lacks the required independent ROI review.")
        if _verification_closes(first):
            raise RealInferenceError("Replay independent ROI record cannot follow a passing primary verification.")
        if verification.get("second_prompt_sha256") != TARGET_ROI_VERIFICATION_PROMPT_SHA256:
            raise RealInferenceError("Replay independent ROI prompt contract does not match the current runtime.")
        return
    # Legacy compatibility is deliberately narrow: it applies only to an
    # unannotated primary-pass response, never to a record with partial or
    # false independent-review metadata.
    if "independent_roi_review" in verification or "second_prompt_sha256" in verification:
        raise RealInferenceError("Replay verification metadata is incomplete.")
    if _verification_closes(verification):
        return
    raise RealInferenceError("Replay verification record lacks the required independent ROI review.")


def _verify_stored_event(stored: dict[str, Any], *, manual: bool = False) -> dict[str, Any]:
    """Run the same after-evidence workflow for robot and human completion."""
    result = stored["demo_v1"]
    primary = _primary_asset(result)
    after = next((asset for asset in result["asset_manifest"]["assets"] if asset["role"] == "after"), None)
    if manual:
        result["human_work_order"] = {"status": "COMPLETED", "source": "manual_operator"}
    _save_stage(stored, "VERIFYING", {
        "source": "manual_completion" if manual else "post_cleaning_cloud_verification",
        "manual_completion": manual,
    }, reason="正在读取清洁后证据并执行验收。")
    verification = None
    error = None
    try:
        if after is None:
            raise RealInferenceError("After-cleaning evidence is unavailable.")
        before_path = _asset_path(primary)
        after_path = _asset_path(after)
        target_evidence = build_verification_evidence(
            before=before_path,
            after=after_path,
            controlled_yolo=result.get("controlled_yolo") or [],
            camera_id=primary["camera_id"],
            object_type=(stored.get("task_profile") or {}).get("object_type"),
        )
        context = {
            "event_type": (stored.get("task_profile") or {}).get("object_type"),
            "camera_id": primary["camera_id"],
            "manual_completion": manual,
            **target_evidence.context,
        }
        runtime = get_runtime()
        # Crop hashes and the versioned ROI contract are in ``context``; the
        # existing evidence_key therefore invalidates old full-frame records.
        key = evidence_key([before_path, after_path], context, runtime.qwen_model)
        if result.get("mode") == "STABLE_REPLAY":
            verification = load_replay_bundle(stored, "verification", key)["verification"]
            _validate_replayed_verification(verification)
        else:
            if not runtime.qwen_ready:
                raise RealInferenceError("Cloud verification is not configured.")
            first_verification = run_verification_qwen_vl(
                before_path,
                after_path,
                context,
                runtime.qwen_model,
                before_roi=target_evidence.before_roi,
                after_roi=target_evidence.after_roi,
            )
            verification = first_verification
            if not _verification_closes(first_verification):
                # The ROI review receives exactly the same paired crop bytes
                # and factual contract, never the first answer/confidence or
                # hidden reasoning.  It is bounded to one turn.
                roi_context = _independent_roi_context(context)
                try:
                    independent = run_target_roi_verification(
                        target_evidence.before_roi,
                        target_evidence.after_roi,
                        roi_context,
                        runtime.qwen_model,
                    )
                except RealInferenceError as second_failure:
                    verification = {
                        **first_verification,
                        "first_review": first_verification,
                        "independent_roi_review": True,
                        "second_prompt_sha256": TARGET_ROI_VERIFICATION_PROMPT_SHA256,
                        "independent_roi_error": str(second_failure),
                    }
                    error = {
                        "error_type": "VERIFICATION_ERROR",
                        "code": "INDEPENDENT_ROI_REVIEW_UNAVAILABLE",
                        "message": str(second_failure),
                    }
                else:
                    verification = {
                        **independent,
                        "first_review": first_verification,
                        "independent_roi_review": True,
                        "second_prompt_sha256": TARGET_ROI_VERIFICATION_PROMPT_SHA256,
                    }
            validate_response(verification, "verification")
            # Do not create a replayable success-looking record when the
            # required independent review transport was unavailable.
            if error is None:
                save_live_bundle(stored, "verification", key, {"verification": verification})
    except RealInferenceError as failure:
        error = {"error_type": "VERIFICATION_ERROR", "code": "VERIFICATION_UNAVAILABLE", "message": str(failure)}

    # A replay-contract validation error must never leave an otherwise passing
    # archived response able to close the current event.
    passed = error is None and _verification_closes(verification)
    state = "CLOSED" if passed else "HUMAN_REVIEW"
    reason = "验收通过，事件已闭环。" if passed else "验收未通过或证据不可用，已转人工复核。"
    robot_id = (stored.get("assignment_decision") or {}).get("selected_robot_id")
    if robot_id:
        # The cleaning action has finished even when verification is unavailable.
        # Release the reservation, retaining the terminal coordinate.
        robot = next(item for item in get_fleet_state() if item["id"] == robot_id)
        update_fleet_robot(str(robot_id), status="idle", active_event_id=None, active_task_id=None,
                           battery=max(0, int(robot.get("battery", 0)) - 2))
    work_order = ({"status": "COMPLETED", "source": "manual_operator"} if manual else None) if passed else {
        "status": "OPEN", "reason": reason, "source": "verification",
    }
    if manual:
        save_human_work_order({"work_order_id": f"human-{stored['event_id']}", "event_id": stored["event_id"], **work_order})
    return _save_stage(stored, state, {
        "verification": verification, "reason": reason, "error": error, "manual_completion": manual,
    }, verification=verification, error=error, fleet_snapshot=get_fleet_state(), reason=reason, human_work_order=work_order)


@event_stage
def verify_event(event_id: str) -> dict[str, Any]:
    stored = _load_stage_event(event_id)
    _require_state(stored, "CLEANING_COMPLETED")
    return _verify_stored_event(stored)


@event_stage
def complete_demo04_manual(event_id: str) -> dict[str, Any]:
    """Complete a capability-created human work order, irrespective of demo id."""
    stored = _load_stage_event(event_id)
    _require_state(stored, "HUMAN_FALLBACK")
    decision = stored.get("assignment_decision") or {}
    if decision.get("status") != "HUMAN_FALLBACK" or decision.get("candidate_count") != 0:
        raise ValueError("Human completion requires an audited zero-candidate capability decision.")
    return _verify_stored_event(stored, manual=True)


def run_demo(demo_id: str, mode: str = "live", force_unavailable: bool = False) -> dict[str, Any]:
    """Technical compatibility runner delegating exclusively to durable stages.

    The retired HTTP /runs API stays 410. There is no synthetic replay path.
    Human completion always requires a separate explicit operator action.
    """
    normalized_mode = "STABLE_REPLAY" if mode.lower() in {"replay", "stable_replay"} else mode.upper()
    event_id = create_demo_event(demo_id, normalized_mode)["event_id"]
    edge_review(event_id)
    reviewed = cloud_review(event_id, force_unavailable=force_unavailable)
    if reviewed["state"] != "CLOUD_REVIEW":
        return reviewed
    located = locate_event(event_id)
    if located["state"] != "LOCATED":
        return located
    assigned = assign_event(event_id)
    if assigned["state"] != "ASSIGNED":
        return assigned
    navigating = start_navigation(event_id)
    if navigating["state"] != "NAVIGATING":
        return navigating
    complete_navigation(event_id)
    complete_cleaning(event_id)
    return verify_event(event_id)
