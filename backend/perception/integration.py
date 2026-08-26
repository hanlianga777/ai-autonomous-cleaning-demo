"""Explicit Phase 4 → Phase 3 handoff, without creating or dispatching events."""

from __future__ import annotations

from uuid import uuid4

from data.mock_data import ROBOTS
from perception.models import TASK_PROFILE_FIELDS, derive_required_capabilities
from scheduling.capability_engine import evaluate_capabilities
from scheduling.scheduler import make_assignment_decision
from workflow.models import WorkflowState


class WorkflowInputError(ValueError):
    pass


def to_cleaning_event_input(analysis: dict, event_id: str | None = None) -> dict:
    """Return a Phase 3 CleaningEvent seed; never persist or execute it here."""
    perception = analysis.get("perception", {})
    if not perception.get("need_clean"):
        raise WorkflowInputError("AI result does not request cleaning, so no CleaningEvent input is created.")
    mapping = analysis.get("location")
    if not isinstance(mapping, dict) or not isinstance(mapping.get("location"), dict):
        raise WorkflowInputError("AI result has no calibrated Camera → SLAM location.")
    location = mapping["location"]
    required_location_fields = {"building", "floor", "zone", "map_id", "x", "y"}
    if not required_location_fields.issubset(location):
        raise WorkflowInputError("Camera → SLAM location is missing Phase 3 location fields.")
    task_profile = derive_required_capabilities(analysis.get("task_profile", {}), location["building"])
    if any(field not in task_profile for field in TASK_PROFILE_FIELDS):
        raise WorkflowInputError("AI TaskProfile is missing required Phase 3 fields.")
    return {
        "event_id": event_id or f"ai-preview-{uuid4().hex[:10]}",
        "state": WorkflowState.DETECTED,
        "source": f"AI_LAB_{str(analysis.get('mode', 'mock')).upper()}",
        "confidence": float(perception.get("confidence", 0.0)),
        "camera_id": mapping["camera_id"],
        "location": location,
        "task_profile": task_profile,
        "template": "ai_lab_perception",
        "assignment_decision": None,
        "navigation_plan": None,
        "verification": None,
        "human_fallback": None,
    }


def scheduler_preview(analysis: dict) -> tuple[dict | None, dict | None]:
    """Run existing Phase 3 constraints/scoring as a non-persisting compatibility check."""
    try:
        event_input = to_cleaning_event_input(analysis)
    except WorkflowInputError as error:
        return None, {"status": "NOT_READY", "reason": str(error)}
    evaluations = evaluate_capabilities(event_input["task_profile"], event_input["location"], ROBOTS)
    return event_input, make_assignment_decision(event_input["task_profile"], evaluations)
