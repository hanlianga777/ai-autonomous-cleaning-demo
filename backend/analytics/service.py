"""Aggregations for the Phase 6 operations dashboard."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from analytics.mock_history import generate_history
from database.connection import list_events


ROBOT_LABELS = {"robot-a": "Robot A", "robot-b": "Robot B", "robot-c": "Robot C"}
PATROL_MINUTES = {"robot-a": 6_800, "robot-b": 5_200, "robot-c": 3_300}
AVAILABLE_MINUTES = 30 * 8 * 60


def task_history() -> list[dict]:
    """30-day baseline plus every persisted integrated-demo event.

    The baseline remains explicit demo history; a run from the customer
    workbench becomes visible immediately rather than being a browser-only row.
    """
    history = generate_history()
    for event in list_events(100):
        if not str(event.get("event_id", "")).startswith("integrated-"):
            continue
        location = event.get("location", {})
        # Newly created stage-driven events have no TaskProfile until cloud
        # review completes; they must still be visible in operations safely.
        profile = event.get("task_profile") or {}
        decision = event.get("assignment_decision") or {}
        state = event.get("state", "HUMAN_REVIEW")
        history.append({
            "timestamp": event.get("updated_at", "2026-08-26 12:00:00"), "zone_id": f"live-{event['event_id']}",
            "zone": location.get("zone", "未定位区域"), "map_id": location.get("map_id", "outdoor-east"),
            "building": location.get("building", "OUTDOOR"), "floor": location.get("floor", "G"),
            "x": location.get("x", 30), "y": location.get("y", 30), "severity": profile.get("severity", "medium"),
            "robot_id": decision.get("selected_robot_id"), "autonomously_closed": state == "CLOSED",
            "human_intervention": state in {"HUMAN_REVIEW", "HUMAN_FALLBACK"},
            "verification_first_pass": state == "CLOSED", "multi_view_triggered": event.get("template") == "multiview_heavy_spill",
            "multi_view_recovered": state == "CLOSED" and event.get("template") == "multiview_heavy_spill",
            "response_time_minutes": 0.2, "closure_time_minutes": 1.0,
        })
    return history


def heatmap() -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in task_history():
        grouped[record["zone_id"]].append(record)
    points = []
    for zone_id, rows in grouped.items():
        sample = rows[0]
        points.append({"zone_id": zone_id, "label": sample["zone"], "map_id": sample["map_id"], "building": sample["building"], "floor": sample["floor"], "x": sample["x"], "y": sample["y"], "count": len(rows), "high_severity_count": sum(row["severity"] == "high" for row in rows)})
    return sorted(points, key=lambda point: point["count"], reverse=True)


def time_distribution() -> list[dict]:
    hours = Counter(int(record["timestamp"][11:13]) for record in task_history())
    # Stage-driven runs are persisted at their actual wall-clock time, rather
    # than the old 08:00–20:00 fixture window. Keep all events in the program
    # aggregate so operations totals do not silently discard a live run.
    return [{"hour": hour, "label": f"{hour:02d}:00", "count": hours[hour]} for hour in range(24)]


def robot_utilization() -> list[dict]:
    assigned = Counter(record["robot_id"] for record in task_history() if record["robot_id"])
    return [{"robot_id": robot_id, "robot_name": ROBOT_LABELS[robot_id], "tasks": assigned[robot_id], "active_minutes": PATROL_MINUTES[robot_id], "utilization": round(PATROL_MINUTES[robot_id] / AVAILABLE_MINUTES * 100, 1)} for robot_id in ROBOT_LABELS]


def kpis() -> dict:
    history = task_history()
    total = len(history)
    multi_view = [record for record in history if record["multi_view_triggered"]]
    return {
        "period_days": 30, "total_events": total,
        "autonomous_closure_rate": round(sum(record["autonomously_closed"] for record in history) / total * 100, 1),
        "human_intervention_rate": round(sum(record["human_intervention"] for record in history) / total * 100, 1),
        "first_pass_success_rate": round(sum(record["verification_first_pass"] for record in history) / total * 100, 1),
        "average_response_time_minutes": round(mean(record["response_time_minutes"] for record in history), 1),
        "average_closure_time_minutes": round(mean(record["closure_time_minutes"] for record in history), 1),
        "multi_view_recovery_rate": round(sum(record["multi_view_recovered"] for record in multi_view) / len(multi_view) * 100, 1) if multi_view else 0.0,
    }


def analytics_overview() -> dict:
    return {"source": "DEMO MOCK MODE", "period": {"days": 30, "ending": "2026-08-26"}, "kpis": kpis(), "heatmap": heatmap(), "time_distribution": time_distribution(), "robot_utilization": robot_utilization(), "top_hotspots": heatmap()[:3]}
