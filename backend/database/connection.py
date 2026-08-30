"""SQLite snapshots plus Phase 3 event and decision audit storage."""

from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from data.mock_data import PARK, ROBOTS

DATABASE_PATH = Path(__file__).resolve().parents[1] / "ai_cleaning_demo.db"
_TRANSACTION: ContextVar[sqlite3.Connection | None] = ContextVar("runtime_transaction", default=None)


# Customer-facing naming is projection data.  Internal IDs remain the stable
# scheduler/runtime contract and must never be rewritten in persisted tasks.
ROBOT_PRESENTATION = {
    "robot-a": {"name": "赛特净界 S5", "short_name": "赛特净界 S5", "model": "Outdoor Sweeper", "role": "室外道路与广场清扫", "product_capability": "室外道路 / 广场类清扫产品定位", "demo_configuration": "仅处理室外道路、广场、其他小型干垃圾和树叶。"},
    "robot-b": {"name": "高仙 Omnie", "short_name": "高仙 Omnie", "model": "Heavy Scrubber", "role": "室内重清洁", "product_capability": "高能力洗扫 / 室内重清洁产品定位", "demo_configuration": "优先处理液体污渍与较重室内清洁。"},
    "robot-c": {"name": "蜗小白 SC50", "short_name": "蜗小白 SC50", "model": "Indoor Light Cleaner", "role": "楼宇室内轻量清洁", "product_capability": "楼宇室内清洁产品定位", "demo_configuration": "本 PoC 配置支持地毯区域轻量垃圾；不是厂商公开能力宣称。"},
    "robot-d": {"name": "普渡 FlashBot Max", "short_name": "普渡 FlashBot Max", "model": "闪电匣 · 楼宇配送机器人", "role": "楼宇配送（PoC）", "product_capability": "楼宇配送产品定位", "demo_configuration": "cleaning capability = none；不参与 Cleaning Scheduler。"},
}


def _baseline_fleet() -> list[dict]:
    """Create the one resettable PoC fleet baseline without mutating ROBOTS."""
    fleet = deepcopy(ROBOTS)
    for robot in fleet:
        robot.update(ROBOT_PRESENTATION[robot["id"]])
        robot["map_id"] = {"robot-a": "OUTDOOR", "robot-b": "A_1F", "robot-c": "B_1F"}[robot["id"]]
        robot["coordinates"] = {"robot-a": {"x": 24, "y": 40}, "robot-b": {"x": 78, "y": 29}, "robot-c": {"x": 24, "y": 26}}[robot["id"]]
        robot["source"] = "POC_SIMULATION"
    fleet.append({
        "id": "robot-d", "code": "R-D04", "status": "idle", "battery": 86,
        "location": "A 栋 1F · 配送待命点", "zone": "A1 Delivery Bay", "building": "A", "floor": "1F",
        "last_seen": "刚刚", "capabilities": ["楼宇配送"], "map_id": "A_1F",
        "coordinates": {"x": 72, "y": 30}, "source": "POC_SIMULATION", **ROBOT_PRESENTATION["robot-d"],
    })
    return fleet


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database_session():
    current = _TRANSACTION.get()
    if current is not None:
        yield current
        return
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


@contextmanager
def runtime_transaction():
    """One SQLite write transaction for task + fleet + transition mutations.

    Nested repository calls share the connection. Never hold this across Cloud
    requests: only deterministic, short state changes belong here.
    """
    if _TRANSACTION.get() is not None:
        yield
        return
    with database_session() as connection:
        connection.execute("BEGIN IMMEDIATE")
        token = _TRANSACTION.set(connection)
        try:
            yield
        finally:
            _TRANSACTION.reset(token)


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
        # Fleet is intentionally a separate, mutable runtime fact.  Do not
        # overwrite it on every start: completed events must retain their
        # robot's terminal location until an explicit reset.
        connection.execute(
            "INSERT OR IGNORE INTO system_snapshots (snapshot_key, payload, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            ("fleet_state", json.dumps(_baseline_fleet(), ensure_ascii=False)),
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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS model_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_event_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                mode TEXT NOT NULL,
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


def get_fleet_state() -> list[dict]:
    return list(read_snapshot("fleet_state"))


def save_fleet_state(fleet: list[dict]) -> None:
    with database_session() as connection:
        connection.execute(
            "INSERT INTO system_snapshots (snapshot_key, payload, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(snapshot_key) DO UPDATE SET payload = excluded.payload, updated_at = excluded.updated_at",
            ("fleet_state", json.dumps(fleet, ensure_ascii=False, default=str)),
        )


@runtime_transaction()
def reset_fleet_state() -> list[dict]:
    if any(robot.get("active_task_id") for robot in get_fleet_state()):
        raise ValueError("Cancel active Operations tasks before resetting the Fleet baseline.")
    fleet = _baseline_fleet()
    save_fleet_state(fleet)
    return fleet


@runtime_transaction()
def update_fleet_robot(robot_id: str, **updates: object) -> dict:
    fleet = get_fleet_state()
    robot = next((item for item in fleet if item["id"] == robot_id), None)
    if robot is None:
        raise KeyError(f"Unknown fleet robot: {robot_id}")
    robot.update(updates)
    save_fleet_state(fleet)
    return robot


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


def save_model_record(source_event_id: str, phase: str, mode: str, payload: dict) -> None:
    """Persist a structured external-AI result for opt-in Stable Replay."""
    with database_session() as connection:
        connection.execute(
            "INSERT INTO model_records (source_event_id, phase, mode, payload) VALUES (?, ?, ?, ?)",
            (source_event_id, phase, mode, json.dumps(payload, ensure_ascii=False, default=str)),
        )


def get_latest_model_record(source_event_id: str, phase: str) -> dict | None:
    with database_session() as connection:
        row = connection.execute(
            "SELECT payload, created_at FROM model_records WHERE source_event_id = ? AND phase = ? AND mode = 'LIVE' ORDER BY id DESC LIMIT 1",
            (source_event_id, phase),
        ).fetchone()
    if row is None:
        return None
    record = json.loads(row["payload"])
    record["recorded_at"] = row["created_at"]
    return record


def list_model_records(source_event_id: str, phase: str) -> list[dict]:
    """Only external LIVE responses are eligible as replay evidence."""
    with database_session() as connection:
        rows = connection.execute(
            "SELECT id, payload, created_at FROM model_records "
            "WHERE source_event_id = ? AND phase = ? AND mode = 'LIVE' ORDER BY id DESC",
            (source_event_id, phase),
        ).fetchall()
    records = []
    for row in rows:
        try:
            payload = json.loads(row["payload"])
        except (ValueError, TypeError):
            continue
        if isinstance(payload, dict):
            records.append({"id": row["id"], "recorded_at": row["created_at"], "payload": payload})
    return records
