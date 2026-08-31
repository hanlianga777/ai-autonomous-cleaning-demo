"""P1-D archive is a read-only projection of real SQLite event snapshots."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from database import connection as db
from event_archive.service import archive_index, project_event


NOW = datetime(2026, 8, 30, 12, tzinfo=timezone.utc)


def event_fixture(event_id="evt-1", state="CLOSED", *, human=False, error=None):
    states = ["DETECTED", "LOCATED", "HUMAN_FALLBACK" if human else "ASSIGNED", state]
    return {
        "event_id": event_id, "source": "INTERVIEW_RUNTIME", "state": state,
        "created_at": "2026-08-30 10:00:00", "updated_at": "2026-08-30 10:01:00",
        "location": {"building": "A", "floor": "2F", "zone": "East Corridor", "map_id": "A_2F", "x": 10, "y": 20},
        "task_profile": {"object_type": "large_object" if human else "can"},
        "assignment_decision": {"selected_robot_id": None if human else "robot-c", "selected_robot_name": None if human else "蜗小白 SC50"},
        "transitions": [{"state": state, "created_at": "2026-08-30 10:00:00", "detail": {}} for state in states],
        "demo_v1": {"mode": "LIVE", "error": error, "verification": {"verification_pass": state == "CLOSED"},
                    "asset_manifest": {"assets": [{"camera_id": "CAM-A2-11" if human else "CAM-A2-08", "role": "before"}]},
                    "fleet_snapshot": [{"id": "robot-c", "name": "蜗小白 SC50", "battery": 87, "coordinates": {"x": 10, "y": 20}}]},
    }


class EventArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.original = db.DATABASE_PATH
        db.DATABASE_PATH = Path(self.temp.name) / "archive.sqlite"
        db.initialize_database()

    def tearDown(self):
        db.DATABASE_PATH = self.original
        self.temp.cleanup()

    def store(self, event):
        db.save_event(event)
        for transition in event["transitions"]:
            db.record_transition(event["event_id"], transition["state"], transition["detail"])
        with db.database_session() as connection:
            connection.execute("UPDATE cleaning_events SET created_at=?,updated_at=? WHERE event_id=?",
                               (event["created_at"], event["updated_at"], event["event_id"]))
            connection.execute("UPDATE event_transitions SET created_at=? WHERE event_id=?", (event["created_at"], event["event_id"]))

    def test_human_fallback_is_normal_and_manual_closure_is_not_autonomous(self):
        pending = project_event(event_fixture(state="HUMAN_FALLBACK", human=True), NOW)
        self.assertEqual((pending["category"], pending["handling_mode"]), ("human_pending", "human_fallback"))
        closed = project_event(event_fixture(human=True), NOW)
        self.assertEqual(closed["category"], "human_closed")
        self.assertEqual(closed["executor"], "人工搬运")

    def test_business_review_and_system_error_are_distinct(self):
        event = event_fixture(state="HUMAN_REVIEW")
        event["demo_v1"]["error"] = {"error_type": "PERCEPTION_ERROR", "code": "final_evidence_or_confidence_gate"}
        self.assertEqual(project_event(event, NOW)["category"], "human_pending")
        for error in ({"error_type": "SPATIAL_ERROR", "code": "CAMERA_MAPPING_FAILED"}, {"error_type": "PERCEPTION_ERROR", "code": "cloud_error"}):
            event["demo_v1"]["error"] = error
            row = project_event(event, NOW)
            self.assertEqual((row["category"], row["handling_mode"]), ("exception", "system_error"))

    def test_cancelled_task_is_terminal_all_only_and_duration_stops(self):
        event = event_fixture(state="CANCELLED")
        self.store(event)
        row = project_event(event, NOW)
        self.assertEqual((row["category"], row["status_label"], row["duration_seconds"]), ("cancelled", "已取消", 60))
        self.assertNotEqual(row["handling_mode"], "system_error")
        index = archive_index(now=NOW)
        self.assertEqual(index["total"], 1)
        self.assertEqual(index["counts"]["all"], 1)
        self.assertEqual(set(index["counts"]), {"all", "in_progress", "autonomous_closed", "human_pending", "exception"})
        for category in ("in_progress", "autonomous_closed", "human_pending", "exception"):
            self.assertEqual(archive_index(category=category, now=NOW)["total"], 0)

    def test_autonomous_closed_requires_robot_verification_and_no_human_intervention(self):
        event = event_fixture()
        self.assertEqual(project_event(event, NOW)["category"], "autonomous_closed")
        event["demo_v1"]["verification"]["verification_pass"] = False
        self.assertNotEqual(project_event(event, NOW)["category"], "autonomous_closed")
        event["demo_v1"]["verification"]["verification_pass"] = True
        event["transitions"].append({"state": "HUMAN_REVIEW", "detail": {}})
        self.assertNotEqual(project_event(event, NOW)["category"], "autonomous_closed")

    def test_discovery_order_does_not_follow_latest_update_and_paginates(self):
        old = event_fixture("old")
        old["created_at"] = "2026-08-29 10:00:00"
        old["updated_at"] = "2026-08-30 11:59:00"
        self.store(old)
        self.store(event_fixture("new", state="HUMAN_FALLBACK", human=True))
        index = archive_index(limit=1, now=NOW)
        self.assertEqual(index["items"][0]["event_id"], "new")
        self.assertEqual(index["total"], 2)
        self.assertEqual(index["counts"]["human_pending"], 1)
        self.assertEqual(archive_index(offset=1, now=NOW)["items"][0]["event_id"], "old")

    def test_search_time_type_location_and_handling_filters(self):
        self.store(event_fixture("robot-event"))
        self.store(event_fixture("manual-event", human=True))
        for query in ("蜗小白", "CAM-A2-08", "A栋2F", "易拉罐", "robot-event", "A_2F"):
            with self.subTest(query=query):
                result = archive_index(q=query, event_type="can", handling_mode="robot", map_id="A_2F", since="2026-08-30T00:00:00Z", until="2026-08-30T12:00:00Z", now=NOW)
                self.assertEqual([row["event_id"] for row in result["items"]], ["robot-event"])
        self.assertEqual(archive_index(since="2026-08-31", now=NOW)["total"], 0)
        self.assertEqual(archive_index(category="autonomous_closed", now=NOW)["total"], 1)
        self.assertEqual(archive_index(handling_mode="human_fallback", now=NOW)["total"], 1)

    def test_invalid_filter_is_not_silently_treated_as_all(self):
        for args in ({"category": "made-up"}, {"since": "bad"}, {"since": "2026-09-01", "until": "2026-01-01"}, {"handling_mode": "delete"}, {"limit": 101}, {"offset": -1}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                archive_index(**args)

    def test_read_only_archive_preserves_event_time_snapshot_and_never_reads_current_fleet(self):
        self.store(event_fixture())
        before = deepcopy(db.get_event("evt-1"))
        transitions = db.get_transitions("evt-1")
        db.update_fleet_robot("robot-c", battery=1, coordinates={"x": 99, "y": 99})
        with patch.object(db, "get_fleet_state", side_effect=AssertionError("archive must not load live fleet")):
            row = archive_index(now=NOW)["items"][0]
        self.assertEqual(row["duration_seconds"], 60)
        self.assertEqual(row["location"]["x"], 10)
        self.assertEqual(db.get_event("evt-1"), before)
        self.assertEqual(db.get_transitions("evt-1"), transitions)

    def test_customer_boundary_excludes_engineering_records_without_deleting_them(self):
        customer = event_fixture("customer-event")
        engineering = event_fixture("test-event")
        engineering["source"] = "TEST"
        self.store(customer)
        self.store(engineering)
        self.assertEqual([item["event_id"] for item in archive_index(now=NOW)["items"]], ["customer-event"])
        self.assertIsNotNone(db.get_event("test-event"))
