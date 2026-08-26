from __future__ import annotations

from uuid import uuid4

from database.connection import (
    get_event,
    get_transitions,
    record_transition,
    save_assignment_decision,
    save_event,
    save_human_work_order,
)
from data.mock_data import ROBOTS
from robots.mock_adapters import MockRobotAdapter
from scheduling.capability_engine import evaluate_capabilities
from scheduling.scheduler import make_assignment_decision
from verification.mock_verification import verify_after_cleaning
from workflow.fixtures import EVENT_TEMPLATES
from workflow.models import ALLOWED_TRANSITIONS, TERMINAL_STATES, WorkflowState, new_event


class WorkflowError(ValueError):
    pass


def create_mock_event(template_name: str) -> dict:
    template = EVENT_TEMPLATES.get(template_name)
    if template is None:
        raise WorkflowError(f"Unknown mock event template: {template_name}")
    event = new_event(f"evt-{uuid4().hex[:10]}", template)
    save_event(event)
    _record(event, WorkflowState.DETECTED, {"message": "Mock perception event created", "template": template_name})
    return event_detail(event["event_id"])


def event_detail(event_id: str) -> dict:
    event = get_event(event_id)
    if event is None:
        raise WorkflowError("Event not found")
    event["transitions"] = get_transitions(event_id)
    return event


def _record(event: dict, next_state: WorkflowState, detail: dict) -> None:
    current_state = WorkflowState(event["state"])
    if next_state != current_state and next_state not in ALLOWED_TRANSITIONS.get(current_state, set()):
        raise WorkflowError(f"Invalid transition: {current_state} -> {next_state}")
    event["state"] = next_state
    save_event(event)
    record_transition(event["event_id"], next_state, detail)


def evaluate_event(event_id: str) -> dict:
    event = get_event(event_id)
    if event is None:
        raise WorkflowError("Event not found")
    evaluations = evaluate_capabilities(event["task_profile"], event["location"], ROBOTS)
    decision = make_assignment_decision(event["task_profile"], evaluations)
    event["assignment_decision"] = decision
    save_event(event)
    save_assignment_decision(event_id, decision)
    return decision


def run_event(event_id: str) -> dict:
    event = get_event(event_id)
    if event is None:
        raise WorkflowError("Event not found")
    if WorkflowState(event["state"]) in TERMINAL_STATES:
        return event_detail(event_id)
    if event["state"] != WorkflowState.DETECTED:
        raise WorkflowError("Only a newly detected mock event can be run automatically")

    _record(event, WorkflowState.JUDGING, {"mode": "MOCK", "message": "Mock confidence judgement completed", "confidence": event["confidence"]})
    _record(event, WorkflowState.CONFIRMED, {"message": "Mock event confirmed; Phase 3 does not invoke Multi-view Agent"})
    _record(event, WorkflowState.LOCATING, {"location": event["location"], "message": "Phase 2 Camera → SLAM location accepted"})
    _record(event, WorkflowState.PROFILING, {"task_profile": event["task_profile"], "message": "Cleaning Task Profile created"})
    _record(event, WorkflowState.CAPABILITY_CHECK, {"message": "Applying deterministic hard constraints"})
    decision = evaluate_event(event_id)
    event = get_event(event_id)
    assert event is not None

    if decision["status"] == "HUMAN_FALLBACK":
        _record(event, WorkflowState.HUMAN_FALLBACK, {"message": decision["reason"], "candidate_count": 0})
        work_order = {"work_order_id": f"wo-{uuid4().hex[:8]}", "event_id": event_id, "status": "OPEN", "reason": decision["reason"], "task_profile": event["task_profile"], "location": event["location"]}
        event["human_fallback"] = work_order
        save_event(event)
        save_human_work_order(work_order)
        _record(event, WorkflowState.VERIFYING, {"mode": "MOCK", "message": "Mock manual work order marked handled for workflow demonstration"})
        verification = verify_after_cleaning(event)
        event["verification"] = verification
        save_event(event)
        _record(event, WorkflowState.CLOSED, verification)
        return event_detail(event_id)

    _record(event, WorkflowState.SCHEDULING, {"message": "Scoring eligible robot candidates", "decision": decision})
    selected_id = decision["selected_robot_id"]
    adapter = MockRobotAdapter()
    assignment = adapter.assign_task(selected_id, event_id)
    _record(event, WorkflowState.ASSIGNED, {"assignment": assignment, "selected_robot": decision["selected_robot_name"], "reason": decision["reason"]})
    navigation_plan = next(candidate["route"] for candidate in decision["candidates"] if candidate["robot_id"] == selected_id)
    event["navigation_plan"] = navigation_plan
    save_event(event)
    _record(event, WorkflowState.NAVIGATING, {"navigation": adapter.navigate(selected_id, navigation_plan), "display_path": navigation_plan["display_path"]})
    for segment in navigation_plan["segments"]:
        if segment["type"] == "elevator":
            _record(event, WorkflowState.WAITING_ELEVATOR, {"segment": segment, "message": "Mock elevator wait"})
            _record(event, WorkflowState.IN_ELEVATOR, {"segment": segment, "message": "Mock elevator transit"})
            _record(event, WorkflowState.NAVIGATING, {"segment": segment, "message": "Resuming local navigation"})
        elif segment["type"] == "skybridge":
            _record(event, WorkflowState.SKYBRIDGE, {"segment": segment, "message": "Mock skybridge transit"})
            _record(event, WorkflowState.NAVIGATING, {"segment": segment, "message": "Resuming local navigation"})
    _record(event, WorkflowState.ARRIVED, {"message": "Mock robot reached SLAM target", "location": event["location"]})
    _record(event, WorkflowState.CLEANING, {"cleaning": adapter.start_cleaning(selected_id, event["task_profile"])})
    _record(event, WorkflowState.VERIFYING, {"mode": "MOCK", "message": "Mock post-clean verification running"})
    verification = verify_after_cleaning(event)
    event["verification"] = verification
    save_event(event)
    _record(event, WorkflowState.CLOSED, verification)
    return event_detail(event_id)
