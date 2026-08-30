"""Event archive read model. No workflow/model/Fleet writes or second event store.

Classification is derived from saved transitions and event-time snapshots.
Completed human work remains in All (not Autonomous Closed or Human Pending).
Counts reflect the search/time/type/handling filters before the category tab.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

from database.connection import database_session


CATEGORIES = {"all", "in_progress", "autonomous_closed", "human_pending", "exception"}
HANDLING_MODES = {"robot", "human_fallback", "human_review", "system_error"}
BUSINESS_REVIEW_CODES = {
    "unrecoverable_ambiguity", "no_legal_supporting_camera", "final_evidence_insufficient",
    "final_evidence_or_confidence_gate", "no_evidence_acquired", "model_turn_limit",
}
TECHNICAL_REASON_CODES = {
    "cloud_error", "cloud_not_configured", "simulated_cloud_unavailable", "replay_record_unavailable",
    "replay_execution_mismatch", "evidence_fetch_failed", "primary_asset_unavailable",
}


def utc_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def read_archived_events() -> list[dict]:
    """One SQLite read snapshot; never enrich history with the current Fleet."""
    with database_session() as connection:
        connection.execute("BEGIN")
        rows = connection.execute(
            "SELECT event_id,payload,created_at,updated_at FROM cleaning_events ORDER BY created_at DESC,event_id DESC"
        ).fetchall()
        transitions = connection.execute(
            "SELECT event_id,id,state,detail,created_at FROM event_transitions ORDER BY id"
        ).fetchall()
    by_event: dict[str, list] = {}
    for row in transitions:
        by_event.setdefault(row["event_id"], []).append({
            "id": row["id"], "state": row["state"], "detail": json.loads(row["detail"]), "created_at": row["created_at"],
        })
    return [{**json.loads(row["payload"]), "created_at": row["created_at"], "updated_at": row["updated_at"],
             "transitions": by_event.get(row["event_id"], [])} for row in rows]


def _system_failure(event: dict, snapshot: dict) -> bool:
    error = snapshot.get("error") or event.get("error") or {}
    if isinstance(error, dict) and error.get("error_type"):
        return error.get("code") not in BUSINESS_REVIEW_CODES
    for transition in event.get("transitions", []):
        detail = transition.get("detail") or {}
        if detail.get("error_type") or str(detail.get("reason")) in TECHNICAL_REASON_CODES or detail.get("error"):
            return True
    return False


def project_event(event: dict, now: datetime) -> dict:
    snapshot = event.get("demo_v1") or event
    state = str(event.get("state", "UNKNOWN"))
    transitions = event.get("transitions", [])
    states = {item["state"] for item in transitions} | {state}
    assignment = event.get("assignment_decision") or snapshot.get("assignment_decision") or {}
    robot_id = assignment.get("selected_robot_id")
    verification = snapshot.get("verification") or {}
    manual = "HUMAN_FALLBACK" in states
    reviewed = "HUMAN_REVIEW" in states
    failed = _system_failure(event, snapshot)
    autonomous = (state == "CLOSED" and bool(robot_id) and not manual and not reviewed
                  and verification.get("verification_pass") is True)
    if state == "CLOSED":
        category = "autonomous_closed" if autonomous else "human_closed" if manual or reviewed else "other_closed"
        status_label = "已自主闭环" if autonomous else "人工处置后闭环" if manual or reviewed else "已闭环 · 待核对执行记录"
    elif failed:
        category, status_label = "exception", "系统/流程异常"
    elif state in {"HUMAN_FALLBACK", "HUMAN_REVIEW"}:
        category = "human_pending"
        status_label = "待人工搬运" if state == "HUMAN_FALLBACK" else "待人工复核"
    else:
        category, status_label = "in_progress", "处理中"
    handling_mode = "system_error" if failed else "human_fallback" if manual else "human_review" if reviewed else "robot" if robot_id else None
    executor = assignment.get("selected_robot_name")
    if not executor and robot_id:
        executor = next((robot.get("name") for robot in snapshot.get("fleet_snapshot", []) if robot.get("id") == robot_id), robot_id)
    executor = executor or ("人工搬运" if manual else "人工复核" if reviewed else "尚未派单")
    location = event.get("location") or snapshot.get("location") or {}
    primary = next((asset for asset in snapshot.get("asset_manifest", {}).get("assets", []) if asset.get("role") == "before"), {})
    profile = event.get("task_profile") or snapshot.get("task_profile") or {}
    first_transition = next((item for item in transitions if item["state"] in {"DETECTED", "DISCOVERED"}), None)
    discovered_at = (first_transition or {}).get("created_at") or event.get("created_at")
    start = utc_time(discovered_at)
    end = utc_time(event.get("updated_at")) if state in {"CLOSED", "HUMAN_REVIEW"} else now
    duration = max(0, int((end - start).total_seconds())) if start and end else None
    return {
        "event_id": event["event_id"], "event_type": profile.get("object_type", "unknown"),
        "camera_id": primary.get("camera_id") or event.get("camera_id"),
        "location": {key: location.get(key) for key in ("building", "floor", "zone", "map_id", "x", "y")},
        "discovered_at": discovered_at, "updated_at": event.get("updated_at"),
        "status": state, "status_label": status_label, "category": category,
        "handling_mode": handling_mode, "executor": executor, "duration_seconds": duration,
        "mode": snapshot.get("mode", event.get("mode", "UNRECORDED")),
    }


def archive_index(*, category: str = "all", q: str = "", event_type: str | None = None,
                  handling_mode: str | None = None, since: str | None = None, until: str | None = None,
                  map_id: str | None = None, offset: int = 0, limit: int = 50,
                  now: datetime | None = None) -> dict:
    if category not in CATEGORIES or handling_mode and handling_mode not in HANDLING_MODES:
        raise ValueError("Unknown archive category or handling mode.")
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError("Archive pagination is out of range.")
    begin, end = utc_time(since), utc_time(until)
    if (since and begin is None) or (until and end is None) or (begin and end and begin > end):
        raise ValueError("Archive time range must be valid ISO dates with since <= until.")
    now = now or datetime.now(timezone.utc)
    terms = q.casefold().split()
    rows = []
    for event in read_archived_events():
        row = project_event(event, now)
        stamp = utc_time(row["discovered_at"])
        if begin and (stamp is None or stamp < begin) or end and (stamp is None or stamp > end):
            continue
        if event_type and row["event_type"] != event_type or handling_mode and row["handling_mode"] != handling_mode:
            continue
        if map_id and row["location"].get("map_id") != map_id:
            continue
        labels = {"small_litter": "其他小型垃圾 纸巾", "liquid": "液体污渍 奶茶", "can": "易拉罐", "large_object": "大件物品 纸箱", "leaf": "树叶", "unknown": "待研判"}
        location = row["location"]
        searchable = " ".join(str(value or "") for value in (
            row["event_id"], row["event_type"], labels.get(row["event_type"]), row["camera_id"], row["executor"],
            location.get("building"), location.get("floor"), location.get("zone"), location.get("map_id"),
            f"{location.get('building', '')}栋{location.get('floor', '')}",
        )).casefold()
        if not all(term in searchable for term in terms):
            continue
        rows.append(row)
    rows.sort(key=lambda row: (utc_time(row["discovered_at"]) or datetime.min.replace(tzinfo=timezone.utc), row["event_id"]), reverse=True)
    counts = {key: len(rows) if key == "all" else sum(row["category"] == key for row in rows) for key in sorted(CATEGORIES)}
    filtered = rows if category == "all" else [row for row in rows if row["category"] == category]
    return {"items": filtered[offset:offset + limit], "total": len(filtered), "counts": counts,
            "generated_at": now.isoformat()}
