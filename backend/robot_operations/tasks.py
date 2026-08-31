"""Backend PoC task machines, with shared Fleet and short atomic transitions.

No hardware/third-party completion is fabricated: an operator explicitly advances
the PoC driver. Cleaning delegates exclusively to the integrated event workflow.
"""
from uuid import uuid4
from datetime import datetime
from threading import Lock, Thread
from time import sleep
import sqlite3

from database.connection import get_event, get_fleet_state, get_transitions, record_transition, runtime_transaction, save_event, update_fleet_robot
from spatial.route_planner import plan_route
from scheduling.config import MIN_BATTERY_PERCENT
from scheduling.profiles import ROBOT_CAPABILITIES
from robot_operations import repository as repo
from robot_operations.catalog import poi, DELIVERY_DEPLOYMENT_POLICY
from robot_operations.coordination import task_lease
from observability.context import new_trace_id

TERMINAL = {"CLOSED", "CANCELLED", "FAILED", "HUMAN_REVIEW"}
_AUTONOMOUS_TASKS: set[str] = set()
_AUTONOMOUS_TASKS_LOCK = Lock()
DELIVERY_STATES = ["ASSIGNED", "TO_PICKUP", "ARRIVED_PICKUP", "PICKED_UP", "ELEVATOR_TRANSIT", "TO_DESTINATION", "DELIVERED", "CLOSED"]
RELOCATION_STATES = ["ASSIGNED", "NAVIGATING", "ARRIVED", "CLOSED"]


def robot(robot_id):
    value = next((item for item in get_fleet_state() if item["id"] == robot_id), None)
    if value is None:
        raise ValueError("Unknown Fleet robot.")
    return value


def position(value):
    return {"label": value["location"], "map_id": value["map_id"], **value["coordinates"], "building": value["building"], "floor": value["floor"]}


def _transition(task, state, detail=None):
    task.update(status=state, updated_at=repo.now())
    task["transitions"].append({"state": state, "created_at": task["updated_at"], "detail": detail or {}})
    repo.save("task", task)
    return task


def get_task(task_id):
    task = repo.get("task", task_id)
    if task["kind"] == "cleaning" and task["status"] not in {"CREATED", "PAUSED", "CANCELLED", "FAILED"}:
        event = get_event(task["event_id"])
        task["status"] = event["state"]
        task["robot_id"] = (event.get("assignment_decision") or {}).get("selected_robot_id")
        task["destination"] = {"label": event["location"]["zone"], **event["location"]}
        task["workflow_transitions"] = get_transitions(task["event_id"])
        assignment = next((row for row in task["workflow_transitions"] if row["state"] == "ASSIGNED"), None)
        if assignment and assignment.get("detail", {}).get("fleet_robot"):
            task["origin"] = position(assignment["detail"]["fleet_robot"])
    return task


@runtime_transaction()
def create_task(session_id, kind, *, event_id=None, robot_id=None, origin_poi=None, destination_poi=None, autonomous=False):
    repo.get("session", session_id)
    origin = destination = None
    if kind == "cleaning":
        event = get_event(event_id or "")
        if not event or "demo_v1" not in event or event["state"] not in {"DETECTED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATED"}:
            raise ValueError("Cleaning requires an eligible persisted camera event; no synthetic profile or bypass is allowed.")
        if any(item["event_id"] == event_id and item["status"] != "CANCELLED" for item in repo.tasks()):
            raise ValueError("This event already has an Operations task. Read the existing task instead.")
        if robot_id is not None or destination_poi is not None:
            raise ValueError("Cleaning robot and position are exclusively determined by the existing workflow.")
    elif kind in {"delivery", "relocation"}:
        robot_id = "robot-d" if kind == "delivery" else robot_id
        current = robot(robot_id)
        destination = poi(destination_poi)
        origin = poi(origin_poi) if kind == "delivery" else position(current)
        if (robot_id == "robot-a") != (destination["map_id"] == "OUTDOOR"):
            raise ValueError("Approved relocation must preserve the robot's indoor/outdoor operating domain.")
        if robot_id == "robot-b" and destination["building"] != "A":
            raise ValueError("Omnie remains limited to A building by the existing capability policy.")
        if kind == "delivery" and origin["map_id"] == "OUTDOOR":
            raise ValueError("FlashBot delivery is indoor PoC only.")
    else:
        raise ValueError("Unsupported task kind.")
    task = {"task_id": f"task-{uuid4().hex[:16]}", "session_id": session_id, "kind": kind,
            "trace_id": event.get("trace_id") if kind == "cleaning" else new_trace_id(),
            "event_trace_id": event.get("trace_id") if kind == "cleaning" else None,
            "session_trace_id": repo.get("session", session_id).get("trace_id"),
            "origin_request_trace_id": repo.get("session", session_id).get("active_request_trace_id"),
            "robot_id": robot_id, "origin": origin, "destination": destination, "event_id": event_id,
            "source": "POC_SIMULATION", "created_at": repo.now(), "status": "CREATED", "transitions": [], "route": None}
    created = _transition(task, "CREATED", {"source": "operator_requested_task"})
    if autonomous and kind in {"delivery", "relocation"}:
        # A complete natural-language task is not an invitation for a second
        # model turn or customer button.  Validate and reserve inside this
        # durable transaction, then let the backend worker own progression.
        _reserve(task)
        return _transition(task, "ASSIGNED", {"route": task["route"], "source": "agent_autonomous_dispatch"})
    if kind == "cleaning":
        event["operations_task_id"] = task["task_id"]
        event["demo_v1"]["operations_task_id"] = task["task_id"]
        save_event(event)
    return created


def _reserve(task):
    current = robot(task["robot_id"])
    if current.get("active_event_id") or current.get("active_task_id") or current["status"] != "idle":
        raise ValueError("Robot is busy; its current task will not be overwritten.")
    if current["battery"] < MIN_BATTERY_PERCENT:
        raise ValueError("Robot battery is below the existing operational minimum.")
    target = task["origin"] if task["kind"] == "delivery" else task["destination"]
    task["route"] = {"to_origin": plan_route(current["map_id"], target["map_id"]),
                     "to_destination": plan_route(target["map_id"], task["destination"]["map_id"])}
    profile = ROBOT_CAPABILITIES.get(current["id"]) or DELIVERY_DEPLOYMENT_POLICY.get(current["id"])
    if not profile:
        raise ValueError("Robot deployment policy is not configured; route cannot be authorized.")
    segment_types = {segment["type"] for route in task["route"].values() for segment in route["segments"]}
    if any(kind in segment_types and profile.get(kind) is not True for kind in ("elevator", "skybridge")):
        raise ValueError("Route exceeds the robot's existing elevator/skybridge permission.")
    if task["kind"] == "relocation":
        task["origin"] = position(current)
    update_fleet_robot(current["id"], status="assigned", active_task_id=task["task_id"])


def _move(task, target):
    update_fleet_robot(task["robot_id"], map_id=target["map_id"], coordinates={"x": target["x"], "y": target["y"]},
                       building=target["building"], floor=target["floor"], zone=target["label"], location=target["label"])


def _release(task, completed=False):
    if not task.get("robot_id"):
        return
    current = robot(task["robot_id"])
    if current.get("active_task_id") == task["task_id"]:
        update_fleet_robot(current["id"], status="idle", active_task_id=None,
                           battery=max(0, current["battery"] - (1 if completed else 0)))


@runtime_transaction()
def control(task_id, action):
    task = get_task(task_id)
    state = task["status"]
    if state in TERMINAL or task.get("busy"):
        raise ValueError("Task is terminal or a stage is already running.")
    if action == "dispatch":
        if state != "CREATED":
            raise ValueError("Dispatch requires CREATED.")
        if task["kind"] == "cleaning":
            return _transition(task, get_event(task["event_id"])["state"], {"delegated_to": "integrated_cleaning_workflow"})
        _reserve(task)
        return _transition(task, "ASSIGNED", {"route": task["route"]})
    if action == "pause":
        if state in {"CREATED", "PAUSED", "HUMAN_FALLBACK", "VERIFYING"}:
            raise ValueError("This task state cannot be paused.")
        task["resume_state"] = state
        if task["kind"] == "cleaning":
            event = get_event(task["event_id"])
            event["operations_control"] = "PAUSED"
            if event["state"] == "NAVIGATING":
                event["operations_pause_started_at"] = repo.now()
            save_event(event)
            if task["robot_id"]:
                current = robot(task["robot_id"])
                if current.get("active_event_id") != task["event_id"]:
                    raise ValueError("Cleaning Fleet reservation no longer belongs to this event.")
                task["resume_fleet_status"] = current["status"]
                update_fleet_robot(task["robot_id"], status="paused")
        elif task["robot_id"]:
            update_fleet_robot(task["robot_id"], status="paused")
        return _transition(task, "PAUSED")
    if action == "resume":
        if state != "PAUSED":
            raise ValueError("Resume requires PAUSED.")
        if task["kind"] == "cleaning":
            event = get_event(task["event_id"])
            event["operations_control"] = None
            paused_at = event.pop("operations_pause_started_at", None)
            if paused_at:
                elapsed = (datetime.fromisoformat(repo.now()) - datetime.fromisoformat(paused_at)).total_seconds() * 1000
                event["operations_paused_ms"] = event.get("operations_paused_ms", 0) + max(0, round(elapsed))
            save_event(event)
            if task["robot_id"] and task.get("resume_fleet_status"):
                current = robot(task["robot_id"])
                if current.get("active_event_id") != task["event_id"]:
                    raise ValueError("Cleaning Fleet reservation no longer belongs to this event.")
                update_fleet_robot(task["robot_id"], status=task.pop("resume_fleet_status"))
        else:
            update_fleet_robot(task["robot_id"], status="assigned")
        return _transition(task, task.pop("resume_state"))
    if action == "cancel":
        if task["kind"] == "cleaning":
            event = get_event(task["event_id"])
            event["operations_control"] = "CANCELLED"
            event["state"] = "CANCELLED"
            save_event(event)
            record_transition(event["event_id"], "CANCELLED", {"source": "robot_operations", "task_id": task_id})
            assigned = (event.get("assignment_decision") or {}).get("selected_robot_id")
            if assigned and robot(assigned).get("active_event_id") == event["event_id"]:
                update_fleet_robot(assigned, status="idle", active_event_id=None, active_task_id=None)
        else:
            _release(task)
        return _transition(task, "CANCELLED")
    raise ValueError("Unknown task action.")


@runtime_transaction()
def _advance_motion(task_id):
    task = get_task(task_id)
    if task["status"] == "PAUSED" or task["status"] in TERMINAL:
        raise ValueError("Paused or terminal task cannot advance.")
    sequence = DELIVERY_STATES if task["kind"] == "delivery" else RELOCATION_STATES
    if task["status"] not in sequence[:-1]:
        raise ValueError("Dispatch the task before advancing its PoC execution.")
    current = robot(task["robot_id"])
    if current.get("active_task_id") != task_id or current.get("active_event_id"):
        raise ValueError("Fleet reservation no longer belongs to this task.")
    state = sequence[sequence.index(task["status"]) + 1]
    if state == "ELEVATOR_TRANSIT" and not any(segment["type"] == "elevator" for segment in task["route"]["to_destination"]["segments"]):
        state = "TO_DESTINATION"
    if state == "ARRIVED_PICKUP":
        _move(task, task["origin"])
    if state in {"DELIVERED", "ARRIVED"}:
        _move(task, task["destination"])
    if state == "CLOSED":
        _release(task, completed=True)
    else:
        update_fleet_robot(task["robot_id"], status=state.lower())
    return _transition(task, state, {"source": "POC_SIMULATION", "driver": "explicit_operator_step"})


def advance(task_id):
    task = get_task(task_id)
    if task["kind"] != "cleaning":
        return _advance_motion(task_id)
    from demo_v1 import service as workflow
    handlers = {"DETECTED": workflow.edge_review, "EDGE_DETECTED": workflow.cloud_review,
                "CLOUD_REVIEW": workflow.locate_event, "LOCATED": workflow.assign_event,
                "ASSIGNED": workflow.start_navigation, "NAVIGATING": workflow.complete_navigation,
                "ARRIVED": workflow.complete_cleaning, "CLEANING_COMPLETED": workflow.verify_event}
    with task_lease(task_id):
        task = get_task(task_id)
        handler = handlers.get(task["status"])
        if not handler:
            raise ValueError("Task cannot advance here; human completion requires its explicit work-order action.")
        # Real model calls are outside SQLite's transaction, but the durable
        # lease excludes both Agent and original Workbench stage mutations.
        result = handler(task["event_id"])
        task.update(robot_id=(result.get("assignment_decision") or {}).get("selected_robot_id"),
                    destination={"label": result["location"]["zone"], **result["location"]})
        return _transition(task, result["state"], {"delegated_to": handler.__name__})


def start_autonomous_progression(task_id):
    """Finish an authorised delivery/relocation from persisted backend state.

    This is deliberately a backend worker rather than an UI timer. Pause,
    cancel and terminal state are checked before every durable transition, so
    closing Chat or changing pages cannot stop or manufacture task progress.
    Cleaning keeps its separate authoritative event workflow and never enters
    this generic motion worker.
    """
    task = get_task(task_id)
    if task["kind"] not in {"delivery", "relocation"}:
        return
    with _AUTONOMOUS_TASKS_LOCK:
        if task_id in _AUTONOMOUS_TASKS:
            return
        _AUTONOMOUS_TASKS.add(task_id)

    def progress():
        try:
            while True:
                current = get_task(task_id)
                if current["status"] in TERMINAL or current["status"] == "CLOSED":
                    return
                if current["status"] == "PAUSED":
                    sleep(0.2)
                    continue
                if current["status"] == "CREATED":
                    return
                advance(task_id)
                sleep(0.35)
        # A local demo can be shut down or a temporary test database removed
        # while the daemon is between durable stages.  There is no safe retry
        # target in that process, so stop quietly rather than leaking a worker
        # exception or inventing progress after the runtime has gone away.
        except (ValueError, KeyError, sqlite3.Error):
            return
        finally:
            with _AUTONOMOUS_TASKS_LOCK:
                _AUTONOMOUS_TASKS.discard(task_id)

    Thread(target=progress, name=f"operations-task-{task_id[-8:]}", daemon=True).start()


def complete_manual(task_id):
    """Run an operator-confirmed human clean-up for a task-owned event.

    It is intentionally separate from ``advance``: an Agent may progress the
    deterministic workflow, but cannot manufacture a human completion.
    """
    from demo_v1 import service as workflow

    with task_lease(task_id):
        task = get_task(task_id)
        if task["kind"] != "cleaning" or task["status"] != "HUMAN_FALLBACK":
            raise ValueError("Manual completion requires a task-owned cleaning HUMAN_FALLBACK.")
        # The legacy-named service keeps its existing zero-candidate guard and
        # follows the normal after-evidence verification path.
        result = workflow.complete_demo04_manual(task["event_id"])
        return _transition(task, result["state"], {
            "delegated_to": "complete_demo04_manual",
            "source": "EXPLICIT_OPERATOR_MANUAL_COMPLETION",
        })
