"""Project existing workflow audit into an explicit, simulated operations view.

The Phase 3 workflow remains the only source of business transitions.  This
module deliberately does not dispatch robots, choose robots, calculate routes
or perform Camera-to-SLAM mapping.  It only projects one completed, audited
mock run over time so the customer UI can visibly replay fleet telemetry and
work-order progress without claiming it is live device telemetry.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from time import monotonic
from typing import Any
from uuid import uuid4

from data.mock_data import ROBOTS
from spatial.spatial_data import ROBOT_POSITIONS
from workbench.service import list_scenario_assets, run_workbench_event, run_workbench_upload


OPERATIONS_CONTRACT = "operations.v1"
PLAYBACK_MODE = "DEMO_PLAYBACK"

# Each checkpoint points to an already-recorded Phase 3 transition.  Timings
# are presentation-only and never alter the canonical workflow event.
AUTONOMOUS_STATES = [
    ("DETECTED", 0.0), ("JUDGING", 1.0), ("LOCATING", 2.0),
    ("CAPABILITY_CHECK", 3.0), ("SCHEDULING", 4.0), ("ASSIGNED", 5.0),
    ("NAVIGATING", 6.0), ("ARRIVED", 8.0), ("CLEANING", 9.0),
    ("VERIFYING", 11.0), ("CLOSED", 12.0),
]
HUMAN_FALLBACK_STATES = [
    ("DETECTED", 0.0), ("JUDGING", 1.0), ("LOCATING", 2.0),
    ("CAPABILITY_CHECK", 3.0), ("HUMAN_FALLBACK", 4.0),
]


@dataclass
class DemoRun:
    run_id: str
    started_at: float
    result: dict[str, Any]


_RUNS: dict[str, DemoRun] = {}
_ACTIVE_RUN_ID: str | None = None


def _record(result: dict[str, Any]) -> DemoRun:
    global _ACTIVE_RUN_ID
    run = DemoRun(run_id=f"run-{uuid4().hex[:10]}", started_at=monotonic(), result=result)
    _RUNS[run.run_id] = run
    _ACTIVE_RUN_ID = run.run_id
    return run


def start_scenario(event_id: str) -> dict[str, Any]:
    return _snapshot(_record(run_workbench_event(event_id)))


def start_upload(filename: str, content: bytes) -> dict[str, Any]:
    return _snapshot(_record(run_workbench_upload(filename, content)))


def operations_snapshot(run_id: str | None = None) -> dict[str, Any]:
    run = _RUNS.get(run_id or _ACTIVE_RUN_ID or "")
    return _snapshot(run) if run else _idle_snapshot()


def _idle_snapshot() -> dict[str, Any]:
    return {
        "schema_version": OPERATIONS_CONTRACT,
        "telemetry_mode": PLAYBACK_MODE,
        "message": "当前没有活跃演示工单。选择一个场景或上传受控清洁前图以开始可审计回放。",
        "fleet": _fleet(None, "IDLE", 0.0),
        "active_work_order": None,
        "catalog": list_scenario_assets(),
    }


def _snapshot(run: DemoRun) -> dict[str, Any]:
    result = run.result
    manifest = result["asset_manifest"]
    event = result["workflow_event"]
    elapsed = max(0.0, monotonic() - run.started_at)
    human = manifest["verification_mode"] == "HUMAN_REQUIRED"
    display_state, progress = _checkpoint(elapsed, human)
    return {
        "schema_version": OPERATIONS_CONTRACT,
        "telemetry_mode": PLAYBACK_MODE,
        "run_id": run.run_id,
        "elapsed_seconds": round(elapsed, 1),
        "fleet": _fleet(event, display_state, progress),
        "active_work_order": _work_order(result, display_state, progress, human),
        "catalog": list_scenario_assets(),
    }


def _checkpoint(elapsed: float, human: bool) -> tuple[str, float]:
    checkpoints = HUMAN_FALLBACK_STATES if human else AUTONOMOUS_STATES
    state, started = checkpoints[0]
    for candidate_state, candidate_started in checkpoints:
        if elapsed >= candidate_started:
            state, started = candidate_state, candidate_started
        else:
            break
    finish = checkpoints[-1][1]
    return state, min(1.0, elapsed / finish) if finish else 1.0


def _fleet(event: dict[str, Any] | None, display_state: str, progress: float) -> list[dict[str, Any]]:
    fleet = []
    selected_id = event.get("assignment_decision", {}).get("selected_robot_id") if event and event.get("assignment_decision") else None
    for source in ROBOTS:
        robot = deepcopy(source)
        position = deepcopy(ROBOT_POSITIONS[source["id"]])
        robot.update({"telemetry_mode": PLAYBACK_MODE, "position": position, "activity": "待命"})
        if source["id"] == selected_id:
            robot.update(_selected_robot_projection(event, display_state, progress, position))
        fleet.append(robot)
    return fleet


def _selected_robot_projection(event: dict[str, Any], state: str, progress: float, origin: dict[str, Any]) -> dict[str, Any]:
    target = event["location"]
    update: dict[str, Any] = {"activity": "已分配工单", "active_event_id": event["event_id"]}
    if state in {"ASSIGNED", "NAVIGATING"}:
        update.update({"status": "navigating", "activity": "正在前往清洁点", "battery": 60})
        if origin["map_id"] == target["map_id"]:
            local_progress = min(1.0, max(0.0, (progress - 0.42) / 0.25))
            update["position"] = {"map_id": origin["map_id"], "x": round(origin["x"] + (target["x"] - origin["x"]) * local_progress, 2), "y": round(origin["y"] + (target["y"] - origin["y"]) * local_progress, 2)}
        else:
            update["route_progress"] = event["navigation_plan"]["display_path"] if event.get("navigation_plan") else []
    elif state == "ARRIVED":
        update.update({"status": "arrived", "activity": "已到达清洁点", "position": {"map_id": target["map_id"], "x": target["x"], "y": target["y"]}})
    elif state == "CLEANING":
        update.update({"status": "cleaning", "activity": "正在执行清洁", "battery": 59, "position": {"map_id": target["map_id"], "x": target["x"], "y": target["y"]}})
    elif state == "VERIFYING":
        update.update({"status": "verifying", "activity": "等待固定摄像头验收", "battery": 58, "position": {"map_id": target["map_id"], "x": target["x"], "y": target["y"]}})
    elif state == "CLOSED":
        update.update({"status": "idle", "activity": "任务完成，已回到待命", "battery": 58, "position": {"map_id": target["map_id"], "x": target["x"], "y": target["y"]}})
    return update


def _work_order(result: dict[str, Any], display_state: str, progress: float, human: bool) -> dict[str, Any]:
    event = result["workflow_event"]
    decision = event["assignment_decision"]
    status = "HUMAN_ACTION_REQUIRED" if human and display_state == "HUMAN_FALLBACK" else display_state
    return {
        "work_order_id": result.get("upload_match", {}).get("sha256", event["event_id"])[:18],
        "event_id": event["event_id"],
        "display_state": status,
        "progress": round(progress, 2),
        "event": event,
        "initial_ai_result": result["initial_ai_result"],
        "multi_view": result.get("multi_view"),
        "asset_manifest": result["asset_manifest"],
        "assignment_decision": decision,
        "verification_pending": human,
        "human_work_order": event.get("human_fallback"),
        "audit_transitions": _customer_transitions(event.get("transitions", []), human),
    }


def _customer_transitions(transitions: list[dict[str, Any]], human: bool) -> list[dict[str, Any]]:
    if not human:
        return transitions
    # Phase 3's mock workflow contains a handled-manual-work-order placeholder.
    # Customer presentation must not represent that placeholder as real evidence.
    return [item for item in transitions if item["state"] not in {"VERIFYING", "CLOSED"}]
