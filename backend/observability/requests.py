"""Persist model request metadata, never request bodies, keys or reasoning."""
from datetime import datetime, timezone
from functools import wraps
import json
from time import perf_counter
from uuid import uuid4

from database.connection import database_session
from observability.context import CURRENT_TRACE


def _save(value):
    with database_session() as connection:
        connection.execute("INSERT INTO runtime_requests(request_id,trace_id,payload) VALUES(?,?,?) "
                           "ON CONFLICT(request_id) DO UPDATE SET payload=excluded.payload",
                           (value["request_id"], value["trace_id"], json.dumps(value, ensure_ascii=False)))


def traced_model_request(function):
    @wraps(function)
    def traced(content, model, **kwargs):
        trace_id = CURRENT_TRACE.get()
        # Legacy independent AI Lab callers may have no event/session trace.
        # Do not fabricate linkage or change their existing lifecycle.
        if trace_id is None:
            return function(content, model, **kwargs)
        record = {"request_id": f"request-{uuid4().hex}", "trace_id": trace_id, "provider": "DashScope",
                  "model": model, "source": "LIVE MODEL", "started_at": datetime.now(timezone.utc).isoformat(),
                  "status": "RUNNING", "duration_ms": None, "tool_enabled": bool(kwargs.get("tools"))}
        started = perf_counter()
        _save(record)
        try:
            result = function(content, model, **kwargs)
            record["status"] = "SUCCESS"
            return result
        except Exception:
            record.update(status="FAILED", error={"type": "MODEL_ERROR", "code": "MODEL_REQUEST_FAILED", "message": "Cloud request failed; inspect the provider configuration and structured event error."})
            raise
        finally:
            record["duration_ms"] = round((perf_counter() - started) * 1000)
            record["finished_at"] = datetime.now(timezone.utc).isoformat()
            _save(record)
    return traced


def execute_stage(function, event_id, *args, **kwargs):
    """Actual stage timing, distinct from model latency or transition timestamp."""
    trace_id = CURRENT_TRACE.get()
    if trace_id is None:
        return function(event_id, *args, **kwargs)
    record = {"span_id": f"span-{uuid4().hex}", "trace_id": trace_id, "name": function.__name__,
              "event_id": event_id, "trigger_source": "USER_ACTION" if function.__name__ == "complete_demo04_manual" else "SYSTEM_WORKFLOW",
              "started_at": datetime.now(timezone.utc).isoformat(), "duration_ms": None, "status": "RUNNING"}
    def persist():
        with database_session() as connection:
            connection.execute("INSERT INTO runtime_spans VALUES(?,?,?) ON CONFLICT(span_id) DO UPDATE SET payload=excluded.payload",
                               (record["span_id"], trace_id, json.dumps(record)))
    started = perf_counter()
    persist()
    try:
        result = function(event_id, *args, **kwargs)
        record.update(status="COMPLETED", result_state=result.get("state"))
        return result
    except Exception:
        record["status"] = "FAILED"
        raise
    finally:
        record["duration_ms"] = round((perf_counter() - started) * 1000)
        persist()
