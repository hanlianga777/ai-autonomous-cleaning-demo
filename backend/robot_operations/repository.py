"""Durable sessions, action audit and task state. No process-local task truth."""
import json
from datetime import datetime, timezone
from uuid import uuid4

from database.connection import database_session


def now():
    return datetime.now(timezone.utc).isoformat()


def initialize():
    with database_session() as connection:
        for table in ("ops_sessions", "ops_tasks"):
            connection.execute(f"CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS ops_audit (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, payload TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS ops_advice (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)")


def recover_interrupted_requests():
    """Single-backend-worker startup recovery; never reruns model/action calls."""
    with database_session() as connection:
        sessions = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM ops_sessions")]
        pending_tasks = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM ops_tasks")]
    for session in sessions:
        if session.get("busy"):
            session.update(busy=False, error={"code": "AGENT_INTERRUPTED", "message": "Backend restarted during a request. Inspect persisted tasks before retrying."})
            save("session", session)
            audit(session["id"], phase="recovery", final_status="INTERRUPTED", error=session["error"])
    for task in pending_tasks:
        if task.get("busy"):
            task["busy"] = False
            task["error"] = {"code": "TASK_STEP_INTERRUPTED", "message": "Inspect the linked event before explicitly retrying."}
            save("task", task)


def save(kind, value):
    table = {"session": "ops_sessions", "task": "ops_tasks"}[kind]
    key = value["id"] if kind == "session" else value["task_id"]
    payload = {key: item for key, item in value.items() if key != "workflow_transitions"} if kind == "task" else value
    with database_session() as connection:
        connection.execute(f"INSERT INTO {table}(id,payload) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                           (key, json.dumps(payload, ensure_ascii=False)))
    return value


def get(kind, key):
    table = {"session": "ops_sessions", "task": "ops_tasks"}[kind]
    with database_session() as connection:
        row = connection.execute(f"SELECT payload FROM {table} WHERE id=?", (key,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown {kind}: {key}")
    return json.loads(row["payload"])


def tasks(session_id=None):
    with database_session() as connection:
        rows = connection.execute("SELECT payload FROM ops_tasks ORDER BY rowid DESC").fetchall()
    values = [json.loads(row["payload"]) for row in rows]
    return [task for task in values if session_id is None or task["session_id"] == session_id]


def new_session():
    return save("session", {"id": f"ops-{uuid4().hex}", "created_at": now(), "messages": [], "page_context": {}, "busy": False})


def audit(session_id, **fields):
    entry = {"created_at": now(), **fields}
    with database_session() as connection:
        cursor = connection.execute("INSERT INTO ops_audit(session_id,payload) VALUES(?,?)", (session_id, json.dumps(entry, ensure_ascii=False)))
    return {"id": cursor.lastrowid, **entry}


def snapshot(session_id):
    value = get("session", session_id)
    with database_session() as connection:
        rows = connection.execute("SELECT id,payload FROM ops_audit WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    value["audits"] = [{"id": row["id"], **json.loads(row["payload"])} for row in rows]
    value["tasks"] = tasks(session_id)
    value["asr"] = {"available": False, "reason": "语音服务未配置"}
    return value


def message(session, role, content):
    session["messages"].append({"id": uuid4().hex, "role": role, "content": content, "created_at": now()})
    save("session", session)


def advice_snapshot():
    with database_session() as connection:
        row = connection.execute("SELECT payload FROM ops_advice WHERE id=1").fetchone()
    return {"snapshot": json.loads(row["payload"]) if row else None}


def save_advice(value):
    with database_session() as connection:
        connection.execute("INSERT INTO ops_advice VALUES(1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (json.dumps(value, ensure_ascii=False),))
    return {"snapshot": value}
