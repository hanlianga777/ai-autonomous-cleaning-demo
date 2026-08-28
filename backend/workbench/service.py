"""Customer-workbench adapter for the four approved, image-backed demo scenarios.

This module only composes the established AI Lab, Spatial, Multi-view and
Workflow layers. It does not create a second scheduler, map or perception
schema. Upload matching is deliberately content-hash based so the controlled
Demo assets remain deterministic while the UI can still use a normal upload.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from perception.config import get_runtime
from perception.qwen import run_qwen_vl
from perception.service import analyze_mock_case
from perception.yolo import RealInferenceError
from workflow.engine import create_mock_event, run_event
from workbench.preset_detections import overlays_for_asset


ASSET_ROOT = Path(__file__).resolve().parents[2] / "sample_data" / "camera_events"

DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "event-outdoor-tissue-001": {
        "title": "Scenario 01 · 室外道路纸巾", "subtitle": "室外道路小型干垃圾 · Robot A 自主闭环",
        "template": "outdoor_debris", "mock_case": "outdoor_small_litter", "primary_camera_id": "CAM-OUT-01",
        "expected_robot": "ROBOT_A", "verification_mode": "AUTONOMOUS", "location_label": "园区室外 · 东侧道路",
        "assets": [("CAM-OUT-01", "primary.png", "清洁前主视角", "before"), ("CAM-OUT-01", "after.png", "清洁后固定摄像头图", "after")],
    },
    "event-beverage-spill-002": {
        "title": "Scenario 02 · 大堂奶茶污渍", "subtitle": "低置信度液体重污 · 多视角确认后由 Robot B 清洁",
        "template": "multiview_heavy_spill", "mock_case": "low_confidence_milk_tea_spill", "primary_camera_id": "CAM-A1-01",
        "expected_robot": "ROBOT_B", "verification_mode": "AUTONOMOUS", "location_label": "A 栋 · 1F · 主大堂",
        "assets": [("CAM-A1-01", "primary.png", "清洁前主视角", "before"), ("CAM-A1-02", "secondary.png", "补充视角", "evidence"), ("CAM-A1-04", "secondary.png", "补充视角", "evidence"), ("CAM-A1-01", "after.png", "清洁后固定摄像头图", "after")],
    },
    "event-indoor-can-003": {
        "title": "Scenario 03 · 二楼易拉罐", "subtitle": "室内地毯小型干垃圾 · Robot C 跨楼栋自主闭环",
        "template": "indoor_can", "mock_case": "indoor_aluminum_can", "primary_camera_id": "CAM-A2-08",
        "expected_robot": "ROBOT_C", "verification_mode": "AUTONOMOUS", "location_label": "A 栋 · 2F · 连廊入口",
        "assets": [("CAM-A2-08", "primary.png", "清洁前主视角", "before"), ("CAM-A2-08", "after.png", "清洁后固定摄像头图", "after")],
    },
    "event-oversized-box-004": {
        "title": "Scenario 04 · 走廊大型纸箱", "subtitle": "超出机器人能力边界 · 创建人工工单，不伪造验收",
        "template": "oversized_object_a2", "mock_case": "oversized_box_or_bag", "primary_camera_id": "CAM-A2-11",
        "expected_robot": "HUMAN_FALLBACK", "verification_mode": "HUMAN_REQUIRED", "location_label": "A 栋 · 2F · 走廊回收点",
        "assets": [("CAM-A2-11", "primary.png", "清洁前主视角", "before")],
    },
}


def _asset_item(event_id: str, camera_id: str, filename: str, label: str, role: str) -> dict[str, Any]:
    path = ASSET_ROOT / camera_id / event_id / filename
    available = path.is_file()
    return {
        "camera_id": camera_id,
        "event_id": event_id,
        "filename": filename,
        "label": label,
        "role": role,
        "available": available,
        "url": f"/demo-assets/{camera_id}/{event_id}/{filename}" if available else None,
        "sha256": sha256(path.read_bytes()).hexdigest() if available else None,
        "detection_overlays": overlays_for_asset(event_id, camera_id, filename),
    }


def scenario_assets(event_id: str) -> dict[str, Any]:
    scenario = DEMO_SCENARIOS.get(event_id)
    if scenario is None:
        raise ValueError("Unknown customer workbench scenario.")
    assets = [_asset_item(event_id, *asset) for asset in scenario["assets"]]
    metadata_path = ASSET_ROOT / scenario["primary_camera_id"] / event_id / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else None
    return {
        "event_id": event_id,
        "title": scenario["title"],
        "subtitle": scenario["subtitle"],
        "expected_robot": scenario["expected_robot"],
        "verification_mode": scenario["verification_mode"],
        "location_label": scenario["location_label"],
        "metadata": metadata,
        "assets": assets,
        "missing_assets": [asset["filename"] for asset in assets if not asset["available"]],
    }


def list_scenario_assets() -> list[dict[str, Any]]:
    return [scenario_assets(event_id) for event_id in DEMO_SCENARIOS]


def _initial_ai_result(event_id: str, uploaded_filename: str | None = None) -> dict[str, Any]:
    result = analyze_mock_case(DEMO_SCENARIOS[event_id]["mock_case"])
    scenario = DEMO_SCENARIOS[event_id]
    primary = next(
        (asset for asset in scenario_assets(event_id)["assets"] if asset["role"] == "before"),
        None,
    )
    overlays = primary["detection_overlays"] if primary else []
    if overlays:
        result["detections"] = [
            {
                "class_name": overlay["label"],
                "confidence": overlay["confidence"],
                "bbox": overlay["bbox"],
                "frame_index": 0,
                "source": overlay["source"],
            }
            for overlay in overlays
        ]
        result["business_detections"][0]["bbox"] = overlays[0]["bbox"]
        result["business_detections"][0]["display_confidence"] = overlays[0]["confidence"]
        result["business_detections"][0]["confidence_source"] = "CONTROLLED_REPLAY"
        result["business_detections"][0]["raw_yolo_class"] = None
        result["business_detections"][0]["raw_yolo_confidence"] = None
        result["pipeline"]["yolo"] = "controlled-replay-overlay"
        result["notes"][0] = "Controlled replay uses reviewed overlays for the exact authorised before-cleaning image; no local model or cloud API was called."
    _attach_optional_cloud_review(result, primary)
    if uploaded_filename:
        result["source"]["filename"] = uploaded_filename
        result["notes"].append("Upload content matched an approved demo before-cleaning asset by SHA-256.")
    return result


def _attach_optional_cloud_review(result: dict[str, Any], primary: dict[str, Any] | None) -> None:
    """Run Qwen-VL only after the local user has configured its key.

    A cloud review is evidence alongside the controlled replay; it cannot
    overwrite the established Scenario workflow or pretend to be raw YOLO.
    """
    runtime = get_runtime()
    if not runtime.qwen_ready:
        result["cloud_review"] = {"status": "NOT_CONFIGURED", "model": runtime.qwen_model}
        return
    if not primary:
        result["cloud_review"] = {"status": "FAILED", "model": runtime.qwen_model, "reason": "No primary image is available for cloud review."}
        return
    image_path = ASSET_ROOT / primary["camera_id"] / primary["event_id"] / primary["filename"]
    try:
        vlm = run_qwen_vl(image_path, runtime.qwen_model)
        result["cloud_review"] = {
            "status": "REAL",
            "model": runtime.qwen_model,
            "need_clean": vlm["need_clean"],
            "confidence": vlm["confidence"],
            "summary": vlm["summary"],
            "business_class": vlm["business_class"],
        }
        result["notes"].append("DashScope Qwen-VL executed for this controlled image; its result is retained as secondary evidence.")
    except RealInferenceError as error:
        result["cloud_review"] = {"status": "FAILED", "model": runtime.qwen_model, "reason": str(error)}


def run_workbench_event(event_id: str, uploaded_filename: str | None = None) -> dict[str, Any]:
    """Run the unchanged Phase 3 workflow for one image-backed demo scenario."""
    if event_id not in DEMO_SCENARIOS:
        raise ValueError("Unknown customer workbench scenario.")
    scenario = DEMO_SCENARIOS[event_id]
    event = create_mock_event(scenario["template"])
    workflow_event = run_event(event["event_id"])
    return {
        "asset_manifest": scenario_assets(event_id),
        "initial_ai_result": _initial_ai_result(event_id, uploaded_filename),
        "workflow_event": workflow_event,
        "multi_view": workflow_event.get("multi_view_trace"),
    }


def match_before_upload(content: bytes) -> dict[str, Any] | None:
    """Identify only supplied before-cleaning assets; after frames never trigger work."""
    digest = sha256(content).hexdigest()
    for event_id in DEMO_SCENARIOS:
        manifest = scenario_assets(event_id)
        for asset in manifest["assets"]:
            if asset["role"] == "before" and asset["sha256"] == digest:
                return {"event_id": event_id, "camera_id": asset["camera_id"], "filename": asset["filename"], "sha256": digest}
    return None


def run_workbench_upload(filename: str, content: bytes) -> dict[str, Any]:
    match = match_before_upload(content)
    if match is None:
        raise ValueError("该上传图片不属于当前四个已授权的演示清洁前素材；请选择工作台中的受控场景，或上传对应的清洁前原图。")
    result = run_workbench_event(match["event_id"], uploaded_filename=filename)
    result["upload_match"] = match
    return result


# Phase 8 API aliases retained for links and tests created before the four-scenario workbench.
SCENARIO_02_EVENT_ID = "event-beverage-spill-002"


def scenario_02_assets() -> dict[str, Any]:
    return scenario_assets(SCENARIO_02_EVENT_ID)


def run_scenario_02_workbench() -> dict[str, Any]:
    return run_workbench_event(SCENARIO_02_EVENT_ID)
