"""Thin HTTP boundary; all action results come from persisted backend state."""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, ConfigDict, Field

from robot_operations import repository as repo, tasks
from robot_operations.agent import send_message, regenerate_advice

router = APIRouter(prefix="/api/robot-operations", tags=["Robot Operations Agent"])


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=4000)
    page_context: dict = Field(default_factory=dict)


def guarded(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/sessions")
def create_session():
    return repo.snapshot(repo.new_session()["id"])


@router.get("/sessions/{session_id}")
def session(session_id: str):
    result = guarded(repo.snapshot, session_id)
    result["tasks"] = [tasks.get_task(task["task_id"]) for task in result["tasks"]]
    return result


@router.post("/sessions/{session_id}/messages")
def post_message(session_id: str, body: Message):
    return guarded(send_message, session_id, body.text, body.page_context)


@router.get("/tasks/{task_id}")
def task(task_id: str):
    return guarded(tasks.get_task, task_id)


@router.post("/tasks/{task_id}/{action}")
def action(task_id: str, action: str, session_id: str = Header(..., alias="X-Operations-Session")):
    task = guarded(tasks.get_task, task_id)
    try:
        if session_id != task["session_id"]:
            raise ValueError("POLICY_REJECTED: task belongs to another session.")
        if action not in {"advance", "dispatch", "pause", "resume", "cancel"}:
            raise ValueError("Unknown task action.")
        result = tasks.advance(task_id) if action == "advance" else tasks.control(task_id, action)
        repo.audit(task["session_id"], phase="operator_action", tool=action, task_id=task_id, robot=result.get("robot_id"),
                   policy="ALLOW", final_status=result["status"], source="EXPLICIT_UI_ACTION")
        return result
    except (ValueError, KeyError) as error:
        repo.audit(task["session_id"], phase="operator_action", tool=action, task_id=task_id, policy="REJECT", error=str(error))
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/advice")
def advice():
    return repo.advice_snapshot()


@router.post("/advice")
def generate_advice():
    return guarded(regenerate_advice)
