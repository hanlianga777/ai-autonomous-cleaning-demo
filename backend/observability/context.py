"""Independent trace correlation; IDs are never derived from Event IDs."""
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

CURRENT_TRACE = ContextVar("runtime_trace_id", default=None)


def new_trace_id():
    return f"trace-{uuid4().hex}"


@contextmanager
def trace_context(trace_id):
    token = CURRENT_TRACE.set(trace_id)
    try:
        yield
    finally:
        CURRENT_TRACE.reset(token)
