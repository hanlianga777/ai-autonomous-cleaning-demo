"""Stable 30-day operational history for the Phase 6 demo."""

from __future__ import annotations

from datetime import datetime, timedelta


ZONE_PROFILES = [
    {"zone_id": "a1-east-entrance", "label": "A 栋 1F · 东入口", "building": "A", "floor": "1F", "map_id": "A_1F", "x": 43.0, "y": 25.0, "hours": [17, 18, 19], "robot_id": "robot-b", "object_type": "beverage_spill", "pollution_form": "liquid", "severity": "high"},
    {"zone_id": "a1-main-lobby", "label": "A 栋 1F · 主大堂", "building": "A", "floor": "1F", "map_id": "A_1F", "x": 29.5, "y": 27.0, "hours": [12, 13], "robot_id": "robot-c", "object_type": "paper_cup", "pollution_form": "solid", "severity": "medium"},
    {"zone_id": "b1-west-lobby", "label": "B 栋 1F · 西侧大堂", "building": "B", "floor": "1F", "map_id": "B_1F", "x": 18.0, "y": 21.0, "hours": [9, 17], "robot_id": "robot-c", "object_type": "paper_scraps", "pollution_form": "solid", "severity": "low"},
    {"zone_id": "outdoor-east-road", "label": "园区室外 · 东入口道路", "building": "OUTDOOR", "floor": None, "map_id": "OUTDOOR", "x": 58.0, "y": 18.0, "hours": [8, 16], "robot_id": "robot-a", "object_type": "small_litter", "pollution_form": "solid", "severity": "medium"},
    {"zone_id": "a2-corridor", "label": "A 栋 2F · 北侧走廊", "building": "A", "floor": "2F", "map_id": "A_2F", "x": 16.0, "y": 18.0, "hours": [10], "robot_id": "robot-c", "object_type": "paper_scraps", "pollution_form": "solid", "severity": "low"},
]


def generate_history(days: int = 30) -> list[dict]:
    """Generate reproducible records ending on the fixed demo date, no database mutation."""
    end_date = datetime(2026, 8, 26, 8, 0, 0)
    records: list[dict] = []
    for day_offset in range(days):
        date = end_date - timedelta(days=(days - 1 - day_offset))
        for profile_index, profile in enumerate(ZONE_PROFILES):
            repeats = 3 if profile_index == 0 else 2 if profile_index in {1, 2, 3} else 1
            for repeat in range(repeats):
                human_intervention = profile_index == 0 and (day_offset + repeat) % 13 == 0
                multi_view_triggered = profile_index == 0 and (day_offset + repeat) % 4 == 0
                multi_view_recovered = multi_view_triggered and (day_offset + repeat) % 11 != 0
                hour = profile["hours"][(day_offset + repeat) % len(profile["hours"])]
                response = 5 + (day_offset * 3 + profile_index * 2 + repeat) % 11
                closure = response + 10 + (day_offset + profile_index * 4 + repeat) % 18
                record = {
                    "event_id": f"hist-{day_offset + 1:02d}-{profile_index}-{repeat}",
                    "timestamp": date.replace(hour=hour, minute=(profile_index * 11 + repeat * 7) % 60).isoformat(),
                    "zone_id": profile["zone_id"], "zone": profile["label"], "building": profile["building"], "floor": profile["floor"],
                    "map_id": profile["map_id"], "x": profile["x"], "y": profile["y"], "object_type": profile["object_type"],
                    "pollution_form": profile["pollution_form"], "severity": profile["severity"], "robot_id": None if human_intervention else profile["robot_id"],
                    "response_time_minutes": response, "closure_time_minutes": closure, "verification_first_pass": not ((day_offset + profile_index + repeat) % 12 == 0),
                    "human_intervention": human_intervention, "multi_view_triggered": multi_view_triggered, "multi_view_recovered": multi_view_recovered,
                    "autonomously_closed": not human_intervention,
                }
                records.append(record)
    return records
