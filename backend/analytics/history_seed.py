"""Explicit synthetic history, stored once as ordinary archived CleaningEvents.

No model records, real AI confidence, Fleet updates or runtime execution are
invented here. Seed events carry DEMO_HISTORY at event and transition level.
"""
from datetime import datetime, timedelta, timezone
import json

from analytics.mock_history import ZONE_PROFILES
from database.connection import database_session, ROBOT_PRESENTATION

LOCAL_ZONE = timezone(timedelta(hours=8))
SEED_VERSION = "p1e-history-v1"


def history_events(now: datetime | None = None, days: int = 30) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    last_day = now.astimezone(LOCAL_ZONE).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    events = []
    for offset in range(days):
        day = last_day - timedelta(days=offset)
        ordinal = day.date().toordinal()
        for index, profile in enumerate(ZONE_PROFILES):
            for repeat in range(3 if index == 0 else 1 if index == 4 else 2):
                stamp = day.replace(hour=profile["hours"][(ordinal + repeat) % len(profile["hours"])], minute=index * 7 + repeat * 13)
                event_id = f"{SEED_VERSION}-{day.date().isoformat()}-{index}-{repeat}"
                manual = index == 0 and (ordinal + repeat) % 13 == 0
                first_pass = (ordinal + index + repeat) % 12 != 0
                robot_id = None if manual else profile["robot_id"]
                response_minutes = 5 + (ordinal * 3 + index * 2 + repeat) % 11
                work_minutes = 10 + (ordinal + index * 4 + repeat) % 18
                location = {key: profile.get(key) for key in ("building", "floor", "map_id", "x", "y")}
                location["zone"] = profile["label"]
                assignment = {"selected_robot_id": robot_id, "selected_robot_name": ROBOT_PRESENTATION[robot_id]["name"] if robot_id else None,
                              "candidate_count": 0 if manual else 1, "source": "DEMO_HISTORY"}
                transitions = []

                def add(state, minutes, **detail):
                    transitions.append({"state": state, "created_at": (stamp + timedelta(minutes=minutes)).astimezone(timezone.utc).isoformat(),
                                        "detail": {"source": "DEMO_HISTORY", **detail}})

                add("DETECTED", 0)
                add("CLOUD_REVIEW", 1)
                add("LOCATED", 1.1, **location)
                add("HUMAN_FALLBACK" if manual else "ASSIGNED", 1.2, assignment_decision=assignment)
                add("HUMAN_STARTED" if manual else "NAVIGATING", 1 + response_minutes)
                if not manual:
                    add("ARRIVED", 3 + response_minutes)
                add("HUMAN_COMPLETED" if manual else "CLEANING_COMPLETED", 1 + response_minutes + work_minutes)
                add("VERIFYING", 1 + response_minutes + work_minutes)
                add("CLOSED" if first_pass else "HUMAN_REVIEW", 2 + response_minutes + work_minutes,
                    verification_pass=first_pass, manual_completion=manual)
                events.append({"event_id": event_id, "state": transitions[-1]["state"], "source": "DEMO_HISTORY", "mode": "DEMO_HISTORY",
                    "seed_version": SEED_VERSION, "camera_id": {0: "CAM-A1-02", 1: "CAM-A1-01", 2: "CAM-B1-01", 3: "CAM-OUT-01", 4: "CAM-A2-08"}[index],
                    "location": location, "zone_id": profile["zone_id"],
                    "task_profile": {"object_type": "large_object" if manual else "liquid" if profile["pollution_form"] == "liquid" else "small_litter", "severity": profile["severity"]},
                    "assignment_decision": assignment, "verification": {"verification_pass": first_pass, "source": "DEMO_HISTORY"},
                    "created_at": transitions[0]["created_at"], "updated_at": transitions[-1]["created_at"], "transitions": transitions})
    return events


def seed_history(now: datetime | None = None) -> int:
    """Startup-only idempotent insertion. Never overwrite a user's event/Fleet."""
    inserted = 0
    with database_session() as connection:
        for event in history_events(now):
            cursor = connection.execute("INSERT OR IGNORE INTO cleaning_events(event_id,state,payload,created_at,updated_at) VALUES(?,?,?,?,?)",
                (event["event_id"], event["state"], json.dumps(event, ensure_ascii=False), event["created_at"], event["updated_at"]))
            if cursor.rowcount != 1:
                continue
            inserted += 1
            connection.executemany("INSERT INTO event_transitions(event_id,state,detail,created_at) VALUES(?,?,?,?)",
                [(event["event_id"], row["state"], json.dumps(row["detail"], ensure_ascii=False), row["created_at"]) for row in event["transitions"]])
    return inserted
