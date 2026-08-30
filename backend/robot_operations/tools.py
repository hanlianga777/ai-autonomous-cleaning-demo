"""Code-level tool policy. Models cannot obtain configuration-write tools."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from analytics.read_model import analytics_overview
from database.connection import get_event, get_fleet_state, get_transitions, ROBOT_PRESENTATION
from event_archive.service import archive_index
from spatial.spatial_data import CAMERAS
from scheduling.profiles import ROBOT_CAPABILITIES
from robot_operations import repository as repo, tasks
from robot_operations.catalog import POIS, poi, DELIVERY_ADAPTERS
from demo_v1.service import available_evidence_manifest


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Read(Arguments):
    resource: Literal["events", "event", "analytics", "fleet", "robot", "capability", "pois", "task", "tasks", "camera_evidence", "delivery_state"]
    id: str = Field(default="", max_length=100)


class Cleaning(Arguments):
    event_id: str = Field(min_length=1, max_length=100)


class Delivery(Arguments):
    origin_poi: str = Field(description="Approved POI: " + "; ".join(f"{key}={value['label']}" for key, value in POIS.items()), json_schema_extra={"enum": list(POIS)})
    destination_poi: str = Field(description="Approved POI: " + "; ".join(f"{key}={value['label']}" for key, value in POIS.items()), json_schema_extra={"enum": list(POIS)})


class Relocation(Arguments):
    robot_id: Literal["robot-a", "robot-b", "robot-c", "robot-d"]
    destination_poi: str = Field(description="Approved POI: " + "; ".join(f"{key}={value['label']}" for key, value in POIS.items()), json_schema_extra={"enum": list(POIS)})


class Task(Arguments):
    task_id: str = Field(min_length=1, max_length=100)


class Evidence(Arguments):
    event_id: str = Field(min_length=1, max_length=100)


SCHEMAS = {"read_operations": Read, "create_cleaning_task": Cleaning, "create_delivery_task": Delivery,
           "create_relocation_task": Relocation, "dispatch_task": Task, "pause_task": Task,
           "resume_task": Task, "cancel_task": Task, "request_camera_evidence": Evidence}
DESCRIPTIONS = {
    "read_operations": "Read authoritative Event/Analytics/Fleet/Robot/Capability/approved POI/Task/Camera Evidence/Delivery adapter facts. Use id for singular resources. Never executes tasks.",
    "create_cleaning_task": "Create one task linked to an existing eligible integrated camera event. Does not choose a robot or bypass Cloud. Read events first if no ID is supplied.",
    "create_delivery_task": "Create native POC SIMULATION delivery by FlashBot Max, approved pickup and destination POIs only. Not a Meituan/Eleme/JD/Taobao external order.",
    "create_relocation_task": "Create standby relocation for the robot explicitly named by the user, to an approved POI only.",
    "dispatch_task": "Dispatch a CREATED task. Backend validates reservation, capability scope and Dijkstra routing; cleaning delegates to its existing workflow.",
    "pause_task": "Pause a non-terminal task without losing position/reservation.",
    "resume_task": "Resume a PAUSED task from persisted state.",
    "cancel_task": "Cancel a task, retaining observed position and releasing its own reservation only.",
    "request_camera_evidence": "Fetch the saved, controlled evidence asset references for an existing event. Not a live production camera snapshot.",
}


def tool_definitions(read_only=False):
    return [{"type": "function", "function": {"name": name, "description": DESCRIPTIONS[name], "parameters": schema.model_json_schema()}}
            for name, schema in SCHEMAS.items() if not read_only or name == "read_operations"]


def camera_evidence(event_id):
    event = get_event(event_id)
    if not event or not event.get("demo_v1"):
        raise ValueError("No supported camera evidence for this event.")
    assets = available_evidence_manifest(
        event["demo_v1"], str(event.get("state", "DETECTED")),
        # Agent reads need the event's durable transition history too; a
        # missing list is safely treated as no future evidence release.
        get_transitions(event_id),
    )["assets"]
    return {"event_id": event_id, "source": "CONTROLLED_EVIDENCE_ASSETS", "assets": [
        {key: asset.get(key) for key in ("camera_id", "role", "filename", "url")} for asset in assets]}


def read(resource, id=""):
    if resource == "fleet":
        return get_fleet_state()
    if resource == "robot":
        return tasks.robot(id)
    if resource == "pois":
        return [poi(key) for key in POIS]
    if resource == "capability":
        return {key: {name: sorted(item) if isinstance(item, set) else item for name, item in value.items()} for key, value in ROBOT_CAPABILITIES.items()}
    if resource == "events":
        return archive_index(limit=20)
    if resource == "event":
        value = get_event(id)
        if not value:
            raise ValueError("Event not found.")
        snapshot = value.get("demo_v1") or value
        public_assets = available_evidence_manifest(snapshot, str(value.get("state", "DETECTED")), get_transitions(id))
        return {"event_id": id, "state": value["state"], "location": value.get("location"), "task_profile": value.get("task_profile"),
                "assignment_decision": value.get("assignment_decision"), "verification": snapshot.get("verification"),
                "evidence_availability": public_assets.get("availability"),
                "error": snapshot.get("error"), "source": value.get("source", snapshot.get("mode"))}
    if resource == "analytics":
        return analytics_overview()
    if resource == "task":
        return tasks.get_task(id)
    if resource == "tasks":
        return [tasks.get_task(item["task_id"]) for item in repo.tasks()[:30]]
    if resource == "camera_evidence":
        return camera_evidence(id)
    if resource == "delivery_state":
        return {"tasks": [tasks.get_task(item["task_id"]) for item in repo.tasks() if item["kind"] == "delivery"],
                "platforms": [adapter.status() for adapter in DELIVERY_ADAPTERS.values()]}
    raise ValueError("Unknown read resource.")


def execute(name, arguments, *, session_id, instruction, read_only=False):
    if name not in SCHEMAS or (read_only and name != "read_operations"):
        raise ValueError("POLICY_REJECTED: tool is not in the operation whitelist.")
    args = SCHEMAS[name].model_validate(arguments).model_dump()
    if name == "read_operations":
        return read(**args)
    if name == "request_camera_evidence":
        return camera_evidence(**args)
    if name == "create_relocation_task":
        aliases = {"robot-a": ["赛特", "S5"], "robot-b": ["高仙", "Omnie"], "robot-c": ["蜗小白", "SC50"], "robot-d": ["普渡", "FlashBot"]}
        if not any(alias.casefold() in instruction.casefold() for alias in [args["robot_id"], *aliases[args["robot_id"]]]):
            raise ValueError("POLICY_REJECTED: relocation requires the user's explicit robot, not an LLM-selected cleaner.")
    if name.startswith("create_"):
        return tasks.create_task(session_id, name.removeprefix("create_").removesuffix("_task"), **args)
    task = repo.get("task", args["task_id"])
    if task["session_id"] != session_id:
        raise ValueError("POLICY_REJECTED: task belongs to another session.")
    return tasks.control(args["task_id"], name.removesuffix("_task"))
