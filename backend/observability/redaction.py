"""API allow-list projection. Raw documents are never sent to the inspector."""
import re
import os
from math import isfinite

ALLOWED_FIELDS = {
    "event_id", "trace_id", "task_id", "robot_id", "selected_robot_id", "state", "status", "mode", "source",
    "camera_id", "role", "url", "model", "provider", "request_id", "phase", "kind", "code", "type",
    "confidence", "decision_confidence", "need_action", "need_clean", "event_type", "evidence_sufficient", "ambiguity_type",
    "severity", "surface_type", "surface", "object_type", "pollution_form", "estimated_area", "required_capabilities",
    "verification_pass", "issue_remaining", "next_action", "image_count", "elapsed_ms", "historical_elapsed_ms", "score",
    "edge_confidence", "cloud_confidence", "factors", "selected_cameras", "iteration_count", "decision", "candidate_count",
    "name", "eligible", "reject_reasons", "scores", "score_breakdown", "ranked_candidates", "evaluations", "hard_filter_results",
    "capability_fit", "eta_distance", "battery", "workload", "zone_fitness", "floor_elevator_cost", "cross_building_cost", "noise_public_space",
    "map_id", "x", "y", "u", "v", "pixel", "bbox", "x1", "y1", "x2", "y2", "building", "floor", "zone",
    "mapping_method", "representative_point", "calibration_points", "slam", "coordinate_unit", "method",
    "start_map", "target_map", "node_path", "display_path", "total_cost", "segments", "from", "to", "cost",
    "task_profile", "location", "assignment_decision", "navigation_plan", "verification", "evidence_fusion",
    "origin", "destination", "label", "poi_id", "origin_poi", "destination_poi", "resource", "id",
    "policy", "ok", "error_type", "duration_ms", "started_at", "finished_at", "created_at", "updated_at", "timestamp",
    "tool_enabled", "trigger_source", "schema", "evidence_key", "source_event_id", "recorded_at", "record_id",
    "historical_provider", "replay_source_event_id", "replay_record_id", "response_source", "candidate_ids",
    "total", "source_counts", "RUNTIME", "DEMO_HISTORY", "limit", "offset", "summary", "independent_second_review",
    "candidates", "robot_name", "selected_robot_name", "score_components", "final_score", "route", "weights", "components", "formula",
    "second_raw_cloud_confidence", "yolo_category_consistency", "camera_location_time_mapping_consistency", "multi_view_consistency",
    "class_name", "evidence_summary", "recommended_capabilities", "interference_factors", "roi", "roi_source", "evidence_status",
    "final_confidence", "evidence_source", "result_state", "span_id", "tool_duration_ms",
    "first_review", "independent_roi_review",
}


def text(value):
    if not isinstance(value, str):
        return value
    configured_key = os.getenv("DASHSCOPE_API_KEY", "")
    if configured_key and configured_key in value:
        return "[REDACTED]"
    # Free strings are still untrusted. Refuse obvious secret/path/data-URI
    # carriers, rather than relying only on sensitive key names.
    if re.search(r"(?i)(bearer\s|\bsk-[a-z0-9]|(?:api[_ -]?key|token|password|secret|authorization)\s*[:=]|data:[^ ]*base64|/Users/|/home/|BEGIN .*PRIVATE KEY|chain.of.thought|reasoning_content|<think>)", value):
        return "[REDACTED]"
    return value[:500]


def safe(value, depth=0):
    if depth > 7:
        return None
    if isinstance(value, dict):
        return {key: safe(item, depth + 1) for key, item in value.items() if key in ALLOWED_FIELDS}
    if isinstance(value, (list, tuple)):
        return [safe(item, depth + 1) for item in value[:40]]
    if isinstance(value, str):
        return text(value)
    if isinstance(value, float) and not isfinite(value):
        return None
    return value if isinstance(value, (bool, int, float)) or value is None else None


def pick(value, *fields):
    if not isinstance(value, dict):
        return {}
    return safe({key: value[key] for key in fields if key in value})
