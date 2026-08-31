"""Customer-data boundary for all interview-demo read projections.

Engineering fixtures, acceptance diagnostics and retired workflow records may
share the local SQLite database, but they are never customer-facing facts.
Keep the allowlist small and explicit so new writers must opt in deliberately.
"""
from __future__ import annotations

from typing import Any


CUSTOMER_SOURCES = frozenset({"DEMO_HISTORY", "INTERVIEW_RUNTIME"})


def is_customer_event(event: dict[str, Any]) -> bool:
    return event.get("source") in CUSTOMER_SOURCES


def customer_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if is_customer_event(event)]
