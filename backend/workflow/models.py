"""Phase 3 domain types. These are deterministic business records, not LLM output."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class WorkflowState(StrEnum):
    DETECTED = "DETECTED"
    JUDGING = "JUDGING"
    MULTI_VIEW = "MULTI_VIEW"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    LOCATING = "LOCATING"
    PROFILING = "PROFILING"
    CAPABILITY_CHECK = "CAPABILITY_CHECK"
    SCHEDULING = "SCHEDULING"
    ASSIGNED = "ASSIGNED"
    NAVIGATING = "NAVIGATING"
    WAITING_ELEVATOR = "WAITING_ELEVATOR"
    IN_ELEVATOR = "IN_ELEVATOR"
    SKYBRIDGE = "SKYBRIDGE"
    ARRIVED = "ARRIVED"
    CLEANING = "CLEANING"
    VERIFYING = "VERIFYING"
    RETRY = "RETRY"
    HUMAN_FALLBACK = "HUMAN_FALLBACK"
    CLOSED = "CLOSED"
    FAILED = "FAILED"


TERMINAL_STATES = {WorkflowState.CLOSED, WorkflowState.REJECTED, WorkflowState.FAILED}

ALLOWED_TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.DETECTED: {WorkflowState.JUDGING},
    WorkflowState.JUDGING: {WorkflowState.CONFIRMED, WorkflowState.MULTI_VIEW, WorkflowState.REJECTED},
    WorkflowState.MULTI_VIEW: {WorkflowState.CONFIRMED, WorkflowState.REJECTED},
    WorkflowState.CONFIRMED: {WorkflowState.LOCATING},
    WorkflowState.LOCATING: {WorkflowState.PROFILING},
    WorkflowState.PROFILING: {WorkflowState.CAPABILITY_CHECK},
    WorkflowState.CAPABILITY_CHECK: {WorkflowState.SCHEDULING, WorkflowState.HUMAN_FALLBACK},
    WorkflowState.SCHEDULING: {WorkflowState.ASSIGNED},
    WorkflowState.ASSIGNED: {WorkflowState.NAVIGATING},
    WorkflowState.NAVIGATING: {WorkflowState.WAITING_ELEVATOR, WorkflowState.SKYBRIDGE, WorkflowState.ARRIVED},
    WorkflowState.WAITING_ELEVATOR: {WorkflowState.IN_ELEVATOR},
    WorkflowState.IN_ELEVATOR: {WorkflowState.NAVIGATING},
    WorkflowState.SKYBRIDGE: {WorkflowState.NAVIGATING},
    WorkflowState.ARRIVED: {WorkflowState.CLEANING},
    WorkflowState.CLEANING: {WorkflowState.VERIFYING},
    WorkflowState.VERIFYING: {WorkflowState.CLOSED, WorkflowState.RETRY},
    WorkflowState.RETRY: {WorkflowState.CLEANING, WorkflowState.CAPABILITY_CHECK, WorkflowState.HUMAN_FALLBACK},
    WorkflowState.HUMAN_FALLBACK: {WorkflowState.VERIFYING, WorkflowState.CLOSED},
}


def new_event(event_id: str, template: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "state": WorkflowState.DETECTED,
        "source": "MOCK_PERCEPTION",
        "confidence": template["confidence"],
        "camera_id": template["camera_id"],
        "location": template["location"],
        "task_profile": template["task_profile"],
        "template": template["template"],
        "assignment_decision": None,
        "navigation_plan": None,
        "verification": None,
        "human_fallback": None,
    }
