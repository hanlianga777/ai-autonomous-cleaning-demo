"""Bounded structured records shared by YOLO, Qwen-VL and AI Lab."""

from __future__ import annotations

from typing import Any


AI_RESULT_SCHEMA_VERSION = "ai-lab.v1"
TASK_PROFILE_FIELDS = ("object_type", "pollution_form", "severity", "estimated_area", "surface", "required_capabilities", "priority", "crowd_level")
VALID_SURFACES = {"asphalt", "granite", "tile", "epoxy", "carpet", "unknown"}
VALID_CAPABILITIES = {"outdoor", "dry_debris", "road_sweeping", "wet_cleaning", "strong_suction", "scrubbing", "heavy_stain", "light_cleaning", "large_object_pickup"}


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
    if result["surface"] not in VALID_SURFACES:
        result["surface"] = "unknown"
    area = value.get("estimated_area", 0.0)
    if isinstance(area, (int, float)) and 0 <= area <= 10000:
        result["estimated_area"] = round(float(area), 2)
    capabilities = value.get("required_capabilities", [])
    if isinstance(capabilities, list):
        result["required_capabilities"] = [str(item).strip().lower() for item in capabilities if str(item).strip().lower() in VALID_CAPABILITIES][:8]
    return result


def derive_required_capabilities(profile: dict[str, Any], building: str) -> dict[str, Any]:
    """Fill the standard Phase 3 capability vocabulary when VLM omits it."""
    normalized = normalize_task_profile(profile)
    if normalized["required_capabilities"]:
        return normalized
    if normalized["pollution_form"] == "large_object":
        normalized["required_capabilities"] = ["large_object_pickup"]
    elif normalized["pollution_form"] == "liquid":
        normalized["required_capabilities"] = ["wet_cleaning", "strong_suction", "scrubbing"] if normalized["severity"] == "high" else ["wet_cleaning"]
    elif building == "OUTDOOR":
        normalized["required_capabilities"] = ["outdoor", "dry_debris"]
    elif normalized["pollution_form"] == "dry_debris":
        normalized["required_capabilities"] = ["dry_debris"]
    return normalized


def perception_schema() -> dict[str, Any]:
    """Public contract used identically by REAL and MOCK response builders."""
    return {
        "schema_version": AI_RESULT_SCHEMA_VERSION,
        "required_top_level": ["schema_version", "mode", "mode_label", "source", "pipeline", "detections", "business_detections", "location", "perception", "task_profile", "workflow_input", "scheduler_preview", "notes"],
        "perception_fields": ["need_clean", "confidence", "summary", "raw"],
        "task_profile_fields": list(TASK_PROFILE_FIELDS),
        "workflow_contract": "Phase 3 CleaningEvent seed; returned only as a preview and never persisted or dispatched by AI Lab.",
    }


def validate_ai_result_schema(result: dict[str, Any]) -> dict[str, Any]:
    """Reject mode-specific response drift before an AI Lab result leaves backend."""
    contract = perception_schema()
    missing = set(contract["required_top_level"]) - set(result)
    if missing:
        raise ValueError(f"AI Lab result misses required fields: {', '.join(sorted(missing))}")
    perception = result.get("perception")
    if not isinstance(perception, dict) or not set(contract["perception_fields"]).issubset(perception):
        raise ValueError("AI Lab perception object does not match ai-lab.v1.")
    task_profile = result.get("task_profile")
    if not isinstance(task_profile, dict) or set(TASK_PROFILE_FIELDS) != set(task_profile):
        raise ValueError("AI Lab TaskProfile does not match the Phase 3 contract.")
    return result
