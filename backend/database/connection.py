"""SQLite setup for Phase 1 read APIs.

The database intentionally stores a tiny snapshot only. Workflow history and
event records are deferred to later phases.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from data.mock_data import PARK, ROBOTS

DATABASE_PATH = Path(__file__).resolve().parents[1] / "ai_cleaning_v2.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
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


def read_snapshot(snapshot_key: str) -> dict | list:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT payload FROM system_snapshots WHERE snapshot_key = ?", (snapshot_key,)
        ).fetchone()
    if row is None:
        raise KeyError(f"Snapshot '{snapshot_key}' is unavailable")
    return json.loads(row["payload"])

