from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import urlparse, parse_qs

from analytics.history_seed import seed_history
from analytics.read_model import analytics_overview, union_seconds, utilization, record
from database import connection as db
from event_archive.service import archive_index
from demo_v1.service import edge_review

NOW = datetime(2026, 8, 30, 4, tzinfo=timezone.utc)


def fixture(event_id="e1", *, human=False, closed=True, error=False, active=False):
    start = NOW - timedelta(hours=1)
    rows = [("DETECTED", 0, {}), ("CLOUD_REVIEW", 1, {}), ("LOCATED", 2, {})]
    rows += [("HUMAN_FALLBACK" if human else "ASSIGNED", 3, {})]
    if human:
        rows += [("HUMAN_COMPLETED", 18, {})]
    else:
        rows += [("NAVIGATING", 6, {}), ("ARRIVED", 8, {})]
    if not active:
        rows += [("CLEANING_COMPLETED", 18, {}), ("VERIFYING", 19, {}),
                 ("CLOSED" if closed else "HUMAN_REVIEW", 20, {"verification_pass": closed})]
    return {"event_id": event_id, "state": rows[-1][0], "camera_id": "CAM-A1-01", "mode": "LIVE",
            "location": {"building": "A", "floor": "1F", "zone": "Main Lobby", "map_id": "A_1F", "x": 29, "y": 27},
            "task_profile": {"object_type": "large_object" if human else "liquid"},
            "assignment_decision": {"selected_robot_id": None if human else "robot-b"},
            "verification": {"verification_pass": closed},
            "error": {"error_type": "SPATIAL_ERROR", "code": "CALIBRATION_MISSING"} if error else None,
            "transitions": [{"state": state, "created_at": (start + timedelta(minutes=minute)).isoformat(), "detail": detail} for state, minute, detail in rows],
            "created_at": start.isoformat(), "updated_at": (start + timedelta(minutes=rows[-1][1])).isoformat()}


class AnalyticsReadModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.original = db.DATABASE_PATH
        db.DATABASE_PATH = Path(self.temp.name) / "analytics.sqlite"
        db.initialize_database()

    def tearDown(self):
        db.DATABASE_PATH = self.original
        self.temp.cleanup()

    def store(self, event):
        with db.database_session() as connection:
            connection.execute("INSERT INTO cleaning_events(event_id,state,payload,created_at,updated_at) VALUES(?,?,?,?,?)",
                               (event["event_id"], event["state"], json.dumps(event), event["created_at"], event["updated_at"]))
            connection.executemany("INSERT INTO event_transitions(event_id,state,detail,created_at) VALUES(?,?,?,?)",
                                  [(event["event_id"], t["state"], json.dumps(t["detail"]), t["created_at"]) for t in event["transitions"]])

    def test_seed_is_idempotent_same_archive_source_and_never_mutates_fleet(self):
        fleet = deepcopy(db.get_fleet_state())
        self.assertEqual(seed_history(NOW), 300)
        self.assertEqual(seed_history(NOW), 0)
        self.assertEqual(db.get_fleet_state(), fleet)
        archive = archive_index(now=NOW)
        self.assertEqual(archive["total"], 300)
        self.assertEqual({row["mode"] for row in archive["items"]}, {"DEMO_HISTORY"})
        overview = analytics_overview(now=NOW)
        self.assertGreater(overview["source_counts"]["DEMO_HISTORY"], 280)
        self.assertEqual(overview["source_counts"]["RUNTIME"], 0)
        self.assertEqual(sum(row["count"] for row in overview["time_distribution"]), overview["kpis"]["total_events"])
        with self.assertRaises(ValueError):
            edge_review(archive["items"][0]["event_id"])
        with db.database_session() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM model_records").fetchone()[0], 0)

    def test_business_denominators_do_not_misclassify_manual_closed_or_system_error(self):
        for event in (fixture("robot"), fixture("manual", human=True), fixture("review", closed=False), fixture("error", closed=False, error=True), fixture("active", active=True)):
            self.store(event)
        result = analytics_overview(now=NOW)
        metrics = result["kpis"]
        self.assertEqual(metrics["denominators"]["autonomous_closure_rate"], 3)
        self.assertEqual(metrics["autonomous_closure_rate"], 33.3)
        self.assertEqual(metrics["human_intervention_rate"], 66.7)
        self.assertEqual(metrics["first_pass_success_rate"], 66.7)
        self.assertEqual(metrics["average_response_time_minutes"], 5)
        self.assertEqual(metrics["average_closure_time_minutes"], 20)
        self.assertEqual(metrics["excluded"], {"system_errors": 1, "no_business_disposition": 1})
        self.assertEqual(metrics["denominators"]["average_response_time_minutes"], 3)

    def test_manual_completion_is_not_response_start_and_retry_not_first_pass(self):
        manual = fixture(human=True)
        self.assertIsNone(record(manual, NOW)["response_time_minutes"])
        retry = fixture(closed=False)
        retry["transitions"] += [{"state": "VERIFYING", "created_at": NOW.isoformat(), "detail": {}},
                                  {"state": "CLOSED", "created_at": NOW.isoformat(), "detail": {"verification_pass": True}}]
        retry["state"] = "CLOSED"
        retry["verification"]["verification_pass"] = True
        self.assertIs(record(retry, NOW)["verification_first_pass"], False)

    def test_independent_roi_pass_does_not_rewrite_first_primary_verification_failure(self):
        event = fixture("roi-remediated", closed=True)
        event["verification"] = {
            "verification_pass": True,
            "confidence": .96,
            "next_action": "close",
            "independent_roi_review": True,
            "first_review": {"verification_pass": False, "confidence": .95, "next_action": "human_review"},
        }
        event["transitions"][-1]["detail"] = {"verification": event["verification"]}
        self.store(event)
        overview = analytics_overview(now=NOW)
        self.assertIs(record(event, NOW)["verification_first_pass"], False)
        self.assertEqual(overview["kpis"]["denominators"]["first_pass_success_rate"], 1)
        self.assertEqual(overview["kpis"]["first_pass_success_rate"], 0.0)

    def test_empty_and_unobserved_metrics_are_null_not_fake_success(self):
        overview = analytics_overview(now=NOW)
        self.assertEqual(overview["kpis"]["total_events"], 0)
        for key in overview["denominators"]:
            self.assertIsNone(overview["kpis"][key])
        self.assertEqual(overview["heatmap"], [])

    def test_heatmap_uses_actual_coordinates_and_drilldown_matches_exact_point(self):
        self.store(fixture("one"))
        other = fixture("other")
        other["location"]["x"] = 42
        self.store(other)
        unlocated = fixture("unlocated", error=True, closed=False)
        unlocated["transitions"] = [unlocated["transitions"][0]]
        self.store(unlocated)
        result = analytics_overview(now=NOW)
        self.assertEqual(result["unlocated_events"], 1)
        self.assertEqual({p["x"] for p in result["heatmap"]}, {29, 42})
        point = result["heatmap"][0]
        query = {key: values[0] for key, values in parse_qs(urlparse(point["drilldown_url"]).query).items()}
        query["x"], query["y"] = float(query["x"]), float(query["y"])
        matching = archive_index(**query, now=NOW)
        self.assertEqual(matching["total"], point["count"])
        self.assertEqual([row["event_id"] for row in matching["items"]], ["one" if point["x"] == 29 else "other"])

    def test_utilization_unions_overlap_clips_declared_window_and_excludes_delivery(self):
        left = datetime(2026, 8, 30, 1, tzinfo=timezone.utc)  # 09:00 Shanghai
        end = left + timedelta(hours=8)
        self.assertEqual(union_seconds([(left, left + timedelta(hours=2)), (left + timedelta(hours=1), left + timedelta(hours=3))]), 10800)
        sample = record(fixture(), NOW)
        sample["transitions"] = [{"state": "NAVIGATING", "created_at": (left - timedelta(hours=1)).isoformat()}, {"state": "CLEANING_COMPLETED", "created_at": (left + timedelta(hours=2)).isoformat()}]
        rows = utilization([sample, sample, {**sample, "robot_id": "robot-d"}], left, end)
        robot = next(row for row in rows if row["robot_id"] == "robot-b")
        self.assertEqual((robot["active_minutes"], robot["available_minutes"], robot["utilization"]), (120, 480, 25))
        self.assertNotIn("robot-d", [row["robot_id"] for row in rows])
        whole_day = utilization([sample], left, left + timedelta(days=1))
        robot_day = next(row for row in whole_day if row["robot_id"] == "robot-b")
        self.assertEqual((robot_day["active_minutes"], robot_day["available_minutes"]), (120, 1440))
        self.assertIn("NOT OBSERVED UPTIME", robot_day["availability_policy"])

    def test_filters_and_read_only_aggregation_preserve_rows_and_fleet(self):
        self.store(fixture())
        before, fleet = deepcopy(db.get_event("e1")), deepcopy(db.get_fleet_state())
        result = analytics_overview(now=NOW, hour=11, event_type="liquid")
        self.assertEqual(result["kpis"]["total_events"], 1)
        self.assertEqual(analytics_overview(now=NOW, hour=12)["kpis"]["total_events"], 0)
        self.assertEqual(db.get_event("e1"), before)
        self.assertEqual(db.get_fleet_state(), fleet)
        for args in ({"since": "invalid"}, {"hour": 24}, {"until": (NOW + timedelta(days=1)).isoformat()}):
            with self.assertRaises(ValueError):
                analytics_overview(now=NOW, **args)

    def test_locked_time_buckets_and_hotspot_summary_drilldown_are_consistent(self):
        seed_history(NOW)
        result = analytics_overview(now=NOW, time_slot="18-22", event_type="liquid")
        self.assertGreater(result["kpis"]["total_events"], 0)
        self.assertEqual(sum(bucket["count"] for bucket in result["time_distribution"] if 18 <= bucket["hour"] < 22), result["kpis"]["total_events"])
        for point in result["heatmap"]:
            self.assertEqual(point["time_slot"], "18-22")
            self.assertIsNotNone(point["average_closure_time_minutes"])
            query = {key: values[0] for key, values in parse_qs(urlparse(point["drilldown_url"]).query).items()}
            query["x"], query["y"] = float(query["x"]), float(query["y"])
            self.assertEqual(archive_index(**query, now=NOW)["total"], point["count"])
        with self.assertRaises(ValueError):
            analytics_overview(now=NOW, time_slot="09-17")
        custom = analytics_overview(now=NOW, since=(NOW - timedelta(days=2)).isoformat())
        self.assertEqual(custom["period"]["days"], 2)

    def test_cross_window_task_contributes_only_clipped_activity_not_new_task_count(self):
        event = fixture()
        row = record(event, NOW)
        start = NOW - timedelta(minutes=52)
        result = next(robot for robot in utilization([row], start, NOW) if robot["robot_id"] == "robot-b")
        self.assertEqual(result["tasks"], 0)
        self.assertEqual(result["carried_tasks"], 1)
        self.assertEqual(result["active_minutes"], 10)
