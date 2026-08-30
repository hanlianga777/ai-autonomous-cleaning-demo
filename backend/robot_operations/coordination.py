"""Durable task lease shared by Agent and original Workbench stage endpoints."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

from database.connection import get_event, runtime_transaction
from robot_operations import repository as repo

_OWNER = ContextVar("operations_task_owner", default=None)


@contextmanager
def task_lease(task_id):
    if _OWNER.get() == task_id:
        yield
        return
    with runtime_transaction():
        task = repo.get("task", task_id)
        if task.get("busy"):
            raise ValueError("An operation is already running on this task.")
        if task["status"] in {"CREATED", "PAUSED", "CANCELLED", "FAILED", "CLOSED", "HUMAN_REVIEW"}:
            raise ValueError("Task is paused or terminal.")
        task["busy"] = True
        repo.save("task", task)
    token = _OWNER.set(task_id)
    try:
        yield
    finally:
        _OWNER.reset(token)
        with runtime_transaction():
            task = repo.get("task", task_id)
            task["busy"] = False
            repo.save("task", task)


def event_stage(function):
    @wraps(function)
    def guarded(event_id, *args, **kwargs):
        event = get_event(event_id)
        task_id = (event or {}).get("operations_task_id")
        if not task_id:
            return function(event_id, *args, **kwargs)
        with task_lease(task_id):
            return function(event_id, *args, **kwargs)
    return guarded
