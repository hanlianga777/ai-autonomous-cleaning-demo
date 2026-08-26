"""Bounded structured records shared by YOLO, Qwen-VL and AI Lab."""

from __future__ import annotations

from typing import Any


def empty_task_profile() -> dict[str, Any]:
    return {
        "object_type": "unknown",
        "pollution_form": "unknown",
        "severity": "low",
        "estimated_area": 0.0,
        "surface": "unknown",
        "required_capabilities": [],
        "priority": "normal",
        "crowd_level": "unknown",
    }


def normalize_task_profile(value: dict[str, Any] | None) -> dict[str, Any]:
    """Constrain VLM output to the Phase 3 scheduler-compatible schema."""
    result = empty_task_profile()
    if not isinstance(value, dict):
        return result
    for key in ("object_type", "pollution_form", "severity", "surface", "priority", "crowd_level"):
        if isinstance(value.get(key), str) and value[key].strip():
            result[key] = value[key].strip().lower()
    area = value.get("estimated_area", 0.0)
    if isinstance(area, (int, float)) and 0 <= area <= 10000:
        result["estimated_area"] = round(float(area), 2)
    capabilities = value.get("required_capabilities", [])
    if isinstance(capabilities, list):
        result["required_capabilities"] = [str(item).strip().lower() for item in capabilities if str(item).strip()][:8]
    return result
