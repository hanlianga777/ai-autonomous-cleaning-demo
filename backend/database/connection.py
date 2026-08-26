"""SQLite snapshots plus Phase 3 event and decision audit storage."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from data.mock_data import PARK, ROBOTS

DATABASE_PATH = Path(__file__).resolve().parents[1] / "ai_cleaning_demo.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database_session():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with database_session() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS system_snapshots (
                snapshot_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO system_snapshots (snapshot_key, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            [("park", json.dumps(PARK, ensure_ascii=False)), ("robots", json.dumps(ROBOTS, ensure_ascii=False))],
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cleaning_events (
                event_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS event_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                state TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assignment_decisions (
                event_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS human_fallback_work_orders (
                work_order_id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def read_snapshot(snapshot_key: str) -> dict | list:
    with database_session() as connection:
        row = connection.execute(
            "SELECT payload FROM system_snapshots WHERE snapshot_key = ?", (snapshot_key,)
        ).fetchone()
    if row is None:
        raise KeyError(f"Snapshot '{snapshot_key}' is unavailable")
    return json.loads(row["payload"])


def save_event(event: dict) -> None:
    payload = json.dumps(event, ensure_ascii=False, default=str)
    with database_session() as connection:
        connection.execute(
            """
            INSERT INTO cleaning_events (event_id, state, payload, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(event_id) DO UPDATE SET state = excluded.state, payload = excluded.payload, updated_at = CURRENT_TIMESTAMP
            """,
            (event["event_id"], str(event["state"]), payload),
        )


def get_event(event_id: str) -> dict | None:
    with database_session() as connection:
        row = connection.execute("SELECT payload, created_at, updated_at FROM cleaning_events WHERE event_id = ?", (event_id,)).fetchone()
    if row is None:
        return None
    event = json.loads(row["payload"])
    event["created_at"] = row["created_at"]
    event["updated_at"] = row["updated_at"]
    return event


def list_events(limit: int = 20) -> list[dict]:
    with database_session() as connection:
        rows = connection.execute("SELECT payload, created_at, updated_at FROM cleaning_events ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
    result = []
    for row in rows:
        event = json.loads(row["payload"])
        event["created_at"] = row["created_at"]
        event["updated_at"] = row["updated_at"]
        result.append(event)
    return result


def record_transition(event_id: str, state: str, detail: dict) -> int:
    with database_session() as connection:
        cursor = connection.execute(
            "INSERT INTO event_transitions (event_id, state, detail) VALUES (?, ?, ?)",
            (event_id, state, json.dumps(detail, ensure_ascii=False, default=str)),
        )
        return int(cursor.lastrowid)


def get_transitions(event_id: str) -> list[dict]:
    with database_session() as connection:
        rows = connection.execute("SELECT id, state, detail, created_at FROM event_transitions WHERE event_id = ? ORDER BY id", (event_id,)).fetchall()
    return [{"id": row["id"], "state": row["state"], "detail": json.loads(row["detail"]), "created_at": row["created_at"]} for row in rows]


def get_transitions_after(after_id: int = 0) -> list[dict]:
    with database_session() as connection:
        rows = connection.execute("SELECT id, event_id, state, detail, created_at FROM event_transitions WHERE id > ? ORDER BY id", (after_id,)).fetchall()
    return [{"id": row["id"], "event_id": row["event_id"], "state": row["state"], "detail": json.loads(row["detail"]), "created_at": row["created_at"]} for row in rows]


def save_assignment_decision(event_id: str, decision: dict) -> None:
    with database_session() as connection:
        connection.execute("INSERT OR REPLACE INTO assignment_decisions (event_id, payload) VALUES (?, ?)", (event_id, json.dumps(decision, ensure_ascii=False, default=str)))


def save_human_work_order(work_order: dict) -> None:
    with database_session() as connection:
        connection.execute("INSERT OR REPLACE INTO human_fallback_work_orders (work_order_id, event_id, payload) VALUES (?, ?, ?)", (work_order["work_order_id"], work_order["event_id"], json.dumps(work_order, ensure_ascii=False, default=str)))
