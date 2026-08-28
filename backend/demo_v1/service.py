"""Live Qwen-backed customer demo orchestration.

This is a thin composition layer: controlled edge evidence remains explicit,
Qwen provides semantic event and verification judgements, and the established
Phase 3 Capability Engine/Scheduler remains the only robot selector.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from data.mock_data import ROBOTS
from perception.config import get_runtime
from perception.multiview.agent import run_multi_view_agent
from perception.qwen import run_event_qwen_vl, run_verification_qwen_vl
from perception.yolo import RealInferenceError
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


def scenario_catalog() -> list[dict[str, Any]]:
    return [{"id": demo_id, "event_id": event_id, "title": scenario_assets(event_id)["title"], "verification_mode": scenario_assets(event_id)["verification_mode"]} for demo_id, event_id in SCENARIO_IDS.items()]


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
        return _human_review("云端综合研判不可用；未创建机器人任务。请人工复核或手动开启稳定回放。", manifest, evidence=evidence, multi_view=multi_view)
    if mode == "replay":
        return _stable_replay(demo_id, manifest, evidence, location, multi_view)
    runtime = get_runtime()
    if not runtime.qwen_ready:
        return _human_review("未配置云端综合研判；现场演示模式不允许自动切换稳定回放。", manifest, evidence=evidence, multi_view=multi_view)
    try:
        qwen = run_event_qwen_vl(qwen_images, evidence, _camera_contexts(manifest, evidence), runtime.qwen_model)
    except RealInferenceError as error:
        return _human_review(f"云端综合研判失败：{error}", manifest, evidence=evidence, multi_view=multi_view)
    event_type = _event_type(qwen["event_type"])
    qwen["event_type"] = event_type
    eligible_for_dispatch = qwen["need_clean"] and qwen["decision_confidence"] >= 0.85 and qwen["next_action"] == "dispatch_robot" and event_type != "unknown"
    if not eligible_for_dispatch:
        return _human_review("云端综合研判未达到自动派发门控；未创建机器人任务。", manifest, qwen, evidence, multi_view)
    profile = _task_profile(qwen, location)
    evaluations = evaluate_capabilities(profile, location, ROBOTS)
    decision = make_assignment_decision(profile, evaluations)
    if decision["status"] != "ASSIGNED":
        return {"mode": "LIVE", "status": "HUMAN_FALLBACK", "reason": decision["reason"], "asset_manifest": manifest, "controlled_yolo": evidence, "multi_view": multi_view, "qwen_review": qwen, "task_profile": profile, "assignment_decision": decision, "verification": None, "human_work_order": {"status": "OPEN", "reason": decision["reason"], "source": "capability_engine"}}
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
    return {"mode": "LIVE", "status": status, "reason": reason, "asset_manifest": manifest, "controlled_yolo": evidence, "multi_view": multi_view, "qwen_review": qwen, "task_profile": profile, "assignment_decision": decision, "verification": verification, "human_work_order": {"status": "OPEN", "reason": reason, "source": "verification"} if status == "HUMAN_REVIEW" else None}


def _stable_replay(demo_id: str, manifest: dict[str, Any], evidence: list[dict[str, Any]], location: dict[str, Any], multi_view: dict[str, Any] | None) -> dict[str, Any]:
    event_type = {"demo01": "small_litter", "demo02": "liquid", "demo03": "can", "demo04": "large_object"}[demo_id]
    qwen = {"provider": "Stable Replay", "model": None, "image_count": 3 if demo_id == "demo02" else 1, "elapsed_ms": None, "need_clean": True, "event_type": event_type, "decision_confidence": 0.91, "severity": "medium", "surface_type": "asphalt" if demo_id == "demo01" else "tile", "interference_factors": ["受控演示回放"], "evidence_summary": "用户手动开启稳定回放，使用预置且可审计的业务结论。", "recommended_capabilities": [], "next_action": "dispatch_robot"}
    profile = _task_profile(qwen, location)
    decision = make_assignment_decision(profile, evaluate_capabilities(profile, location, ROBOTS))
    if decision["status"] != "ASSIGNED":
        return {"mode": "STABLE_REPLAY", "status": "HUMAN_FALLBACK", "reason": decision["reason"], "asset_manifest": manifest, "controlled_yolo": evidence, "multi_view": multi_view, "qwen_review": qwen, "task_profile": profile, "assignment_decision": decision, "verification": None, "human_work_order": {"status": "OPEN", "reason": decision["reason"]}}
    return {"mode": "STABLE_REPLAY", "status": "CLOSED", "reason": "用户手动开启稳定回放，受控验收通过。", "asset_manifest": manifest, "controlled_yolo": evidence, "multi_view": multi_view, "qwen_review": qwen, "task_profile": profile, "assignment_decision": decision, "verification": {"provider": "Stable Replay", "verification_pass": True, "confidence": 0.95, "evidence_summary": "受控回放验收通过。", "next_action": "close", "elapsed_ms": None}, "human_work_order": None}
