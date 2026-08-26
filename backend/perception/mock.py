"""Stable and clearly-labelled AI Lab results for offline demonstrations."""

from __future__ import annotations

from pathlib import Path

from spatial.calibration import CalibrationError, map_pixel_to_slam


def mock_analysis(filename: str, media_type: str, camera_id: str) -> dict:
    video = media_type == "video"
    label = "bottle" if "bottle" in filename.lower() else "cup"
    bbox = {"x1": 418, "y1": 246, "x2": 604, "y2": 438}
    try:
        location = map_pixel_to_slam(camera_id, 511, 342)
    except CalibrationError:
        location = None
    notes = ["Stable local Mock result; no model or cloud API was called.", "AI Lab output is intentionally separate from the Scenario workflow."]
    if location is None:
        notes.append("This camera has no four-point calibration in the Phase 2 dataset, so no SLAM coordinate is asserted.")
    return {
        "mode": "mock",
        "mode_label": "DEMO MOCK MODE",
        "source": {"filename": filename, "media_type": media_type, "camera_id": camera_id},
        "pipeline": {"yolo": "mock-yolo26n", "vlm": "mock-qwen-vl", "keyframes": 3 if video else 1},
        "detections": [{"class_name": label, "confidence": 0.91, "bbox": bbox, "frame_index": 12 if video else 0}],
        "location": location,
        "vlm": {"needs_cleaning": True, "confidence": 0.94, "summary": "Mock VLM confirmed a small beverage container and localized dry debris.", "raw": {"provider": "mock", "source_name": Path(filename).name}},
        "task_profile": {"object_type": label, "pollution_form": "dry_debris", "severity": "low", "estimated_area": 0.12, "surface": "tile", "required_capabilities": ["vacuum", "dry_cleaning"], "priority": "normal", "crowd_level": "medium"},
        "notes": notes,
    }
