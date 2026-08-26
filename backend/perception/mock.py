"""Stable, business-shaped AI Lab results for offline compatibility testing."""

from __future__ import annotations

from typing import Any

from perception.models import AI_RESULT_SCHEMA_VERSION
from spatial.calibration import CalibrationError, map_pixel_to_slam


MOCK_CASES: dict[str, dict[str, Any]] = {
    "outdoor_small_litter": {
        "label": "室外小垃圾 · Robot A", "camera_id": "CAM-OUT-01", "class_name": "bottle", "center": (554, 400),
        "summary": "Small dry litter was confirmed on the outdoor asphalt road.",
        "task_profile": {"object_type": "small_litter", "pollution_form": "dry_debris", "severity": "low", "estimated_area": 0.2, "surface": "asphalt", "required_capabilities": ["outdoor", "dry_debris"], "priority": "normal", "crowd_level": "medium"},
    },
    "heavy_milk_tea_spill": {
        "label": "奶茶/液体重污 · Robot B", "camera_id": "CAM-A1-01", "class_name": "beverage_spill", "center": (500, 400),
        "summary": "A large liquid beverage spill was confirmed on a tiled public lobby floor.",
        "task_profile": {"object_type": "beverage_spill", "pollution_form": "liquid", "severity": "high", "estimated_area": 3.5, "surface": "tile", "required_capabilities": ["wet_cleaning", "strong_suction", "scrubbing"], "priority": "high", "crowd_level": "high"},
    },
    "low_confidence_milk_tea_spill": {
        "label": "低置信度奶茶污渍 · Multi-view", "camera_id": "CAM-A1-01", "class_name": "beverage_spill", "center": (500, 400),
        "summary": "The primary view suggests a beverage spill, but requires corroboration from adjacent cameras.",
        "task_profile": {"object_type": "beverage_spill", "pollution_form": "liquid", "severity": "high", "estimated_area": 3.5, "surface": "tile", "required_capabilities": ["wet_cleaning", "strong_suction", "scrubbing"], "priority": "high", "crowd_level": "high"},
    },
    "indoor_paper_cup": {
        "label": "室内纸杯/纸屑 · Robot C", "camera_id": "CAM-A1-01", "class_name": "paper_cup", "center": (500, 350),
        "summary": "A small paper cup and light dry debris were confirmed indoors.",
        "task_profile": {"object_type": "paper_cup", "pollution_form": "dry_debris", "severity": "low", "estimated_area": 0.15, "surface": "tile", "required_capabilities": ["dry_debris"], "priority": "normal", "crowd_level": "high"},
    },
    "oversized_box_or_bag": {
        "label": "大纸箱/大垃圾袋 · Human Fallback", "camera_id": "CAM-A1-01", "class_name": "large_cardboard_box", "center": (380, 365),
        "summary": "An oversized object was confirmed; it exceeds the supported autonomous pickup capability.",
        "task_profile": {"object_type": "large_cardboard_box", "pollution_form": "large_object", "severity": "medium", "estimated_area": 2.0, "surface": "tile", "required_capabilities": ["large_object_pickup"], "priority": "normal", "crowd_level": "high"},
    },
}


def list_mock_cases() -> list[dict[str, str]]:
    return [{"case": key, "label": value["label"], "camera_id": value["camera_id"]} for key, value in MOCK_CASES.items()]


def _base_mock_result(filename: str, media_type: str, camera_id: str, case: dict[str, Any]) -> dict[str, Any]:
    u, v = case["center"]
    bbox = {"x1": u - 93, "y1": v - 96, "x2": u + 93, "y2": v + 96}
    try:
        location = map_pixel_to_slam(camera_id, u, v)
    except CalibrationError:
        location = None
    notes = ["Stable local Mock result; no model or cloud API was called.", "AI Lab output is intentionally separate from the Scenario workflow."]
    if location is None:
        notes.append("This camera has no four-point calibration in the Phase 2 dataset, so no SLAM coordinate is asserted.")
    return {
        "schema_version": AI_RESULT_SCHEMA_VERSION,
        "mode": "mock", "mode_label": "DEMO MOCK MODE",
        "source": {"filename": filename, "media_type": media_type, "camera_id": camera_id},
        "pipeline": {"yolo": "mock-yolo26n", "vlm": "mock-qwen-vl", "keyframes": 3 if media_type == "video" else 1},
        "detections": [{"class_name": case["class_name"], "confidence": 0.91, "bbox": bbox, "frame_index": 0}],
        "location": location,
        "perception": {"need_clean": True, "confidence": 0.67 if case["label"].startswith("低置信度") else 0.94, "summary": case["summary"], "raw": {"provider": "mock", "case": case["label"]}},
        "task_profile": case["task_profile"],
        "workflow_input": None, "scheduler_preview": None, "notes": notes,
    }


def mock_analysis(filename: str, media_type: str, camera_id: str) -> dict[str, Any]:
    lowered = filename.lower()
    matched_case = next((value for key, value in MOCK_CASES.items() if any(token in lowered for token in key.split("_"))), None)
    case = matched_case or MOCK_CASES["indoor_paper_cup"]
    return _base_mock_result(filename, media_type, camera_id, case)


def mock_case_analysis(case_name: str) -> dict[str, Any]:
    case = MOCK_CASES.get(case_name)
    if case is None:
        raise ValueError("Unknown AI Lab mock validation case.")
    return _base_mock_result(f"{case_name}.jpg", "image", case["camera_id"], case)
