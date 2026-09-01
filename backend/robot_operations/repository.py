"""Durable sessions, action audit and task state. No process-local task truth."""
import json
from datetime import datetime, timezone
from uuid import uuid4

from database.connection import database_session, read_snapshot, save_fleet_state
from database.connection import _baseline_fleet
from observability.context import new_trace_id, CURRENT_TRACE


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
    return save("session", {"id": f"ops-{uuid4().hex}", "trace_id": new_trace_id(), "created_at": now(), "messages": [], "page_context": {}, "busy": False})


def current_show_session():
    """Return the one active customer-show session, if a launcher created it."""
    try:
        value = read_snapshot("show_session")
    except KeyError:
        return None
    return value if isinstance(value, dict) else None


def begin_show_session():
    """Start a new customer show without erasing historical business records.

    The active fleet projection and chat context are intentionally reset. Event
    archive, Analytics history and the persisted old task/audit rows remain
    intact, but cannot be reused by the new browser session.
    """
    session = new_session()
    show = {"id": f"show-{uuid4().hex}", "agent_session_id": session["id"], "created_at": now()}
    with database_session() as connection:
        connection.execute(
            "INSERT INTO system_snapshots(snapshot_key,payload,updated_at) VALUES(?,?,CURRENT_TIMESTAMP) "
            "ON CONFLICT(snapshot_key) DO UPDATE SET payload=excluded.payload,updated_at=CURRENT_TIMESTAMP",
            ("show_session", json.dumps(show, ensure_ascii=False)),
        )
    # Do not call reset_fleet_state: an interrupted old task must not prevent a
    # new show from opening.  The new Show Session owns a fresh baseline.
    save_fleet_state(_baseline_fleet())
    return show


def audit(session_id, **fields):
    session = get("session", session_id)
    request_trace_id = CURRENT_TRACE.get() or session.get("active_request_trace_id")
    trace_id = request_trace_id or session.get("trace_id")
    if fields.get("task_id"):
        trace_id = get("task", fields["task_id"]).get("trace_id") or trace_id
    entry = {"created_at": now(), "trace_id": trace_id, "request_trace_id": request_trace_id, "session_trace_id": session.get("trace_id"), **fields}
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


def session_history(session_id: str) -> dict:
    """Read-only customer chat projection; never exposes tasks, audits or page context."""
    session = get("session", session_id)
    return {
        "id": session["id"],
        "created_at": session.get("created_at"),
        "messages": [
            {key: message.get(key) for key in ("id", "role", "content", "created_at")}
            for message in session.get("messages", [])
        ],
    }


def session_history_index() -> dict:
    """Return all persisted chat sessions newest first with a compact preview."""
    with database_session() as connection:
        rows = connection.execute("SELECT payload FROM ops_sessions ORDER BY rowid DESC").fetchall()
    sessions = []
    for row in rows:
        value = json.loads(row["payload"])
        messages = value.get("messages", [])
        latest = messages[-1] if messages else {}
        sessions.append({
            "id": value.get("id"),
            "created_at": value.get("created_at"),
            "message_count": len(messages),
            "preview": str(latest.get("content", ""))[:80],
            "updated_at": latest.get("created_at") or value.get("created_at"),
        })
    sessions.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
    return {"sessions": sessions}


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
