"""Compatibility API over the shared, read-only P1-E analytics model."""
from datetime import datetime, timedelta, timezone
from analytics.read_model import analytics_overview, history

def task_history() -> list[dict]:
    now = datetime.now(timezone.utc)
    return history(now, now - timedelta(days=30), now)

def heatmap() -> list[dict]:
    return analytics_overview()["heatmap"]

def kpis() -> dict:
    return analytics_overview()["kpis"]

def robot_utilization() -> list[dict]:
    return analytics_overview()["robot_utilization"]

def time_distribution() -> list[dict]:
    return analytics_overview()["time_distribution"]
