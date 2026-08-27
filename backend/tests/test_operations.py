import os
import tempfile
import unittest

from database import connection
from operations import service


class OperationsProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._database_path = connection.DATABASE_PATH
        cls._temp_dir = tempfile.TemporaryDirectory()
        connection.DATABASE_PATH = os.path.join(cls._temp_dir.name, "operations-test.db")
        connection.initialize_database()

    @classmethod
    def tearDownClass(cls):
        connection.DATABASE_PATH = cls._database_path
        cls._temp_dir.cleanup()

    def setUp(self):
        service._RUNS.clear()
        service._ACTIVE_RUN_ID = None

    def test_idle_snapshot_exposes_the_whole_fleet_and_approved_catalog(self):
        snapshot = service.operations_snapshot()
        self.assertEqual(snapshot["schema_version"], "operations.v1")
        self.assertEqual(snapshot["telemetry_mode"], "DEMO_PLAYBACK")
        self.assertEqual({robot["id"] for robot in snapshot["fleet"]}, {"robot-a", "robot-b", "robot-c"})
        self.assertEqual(len(snapshot["catalog"]), 4)

    def test_scenario_projection_reuses_robot_b_workflow_and_exposes_telemetry(self):
        snapshot = service.start_scenario("event-beverage-spill-002")
        order = snapshot["active_work_order"]
        self.assertEqual(order["event"]["assignment_decision"]["selected_robot_id"], "robot-b")
        self.assertEqual(order["initial_ai_result"]["schema_version"], "ai-lab.v1")
        self.assertEqual(order["event"]["location"]["map_id"], "A_1F")
        self.assertEqual(order["multi_view"]["decision"], "CONFIRM")
        self.assertTrue(all("position" in robot and "battery" in robot for robot in snapshot["fleet"]))

    def test_human_fallback_never_projects_a_robot_verification_closure(self):
        snapshot = service.start_scenario("event-oversized-box-004")
        run = service._RUNS[snapshot["run_id"]]
        run.started_at -= 5
        progressed = service.operations_snapshot(snapshot["run_id"])
        order = progressed["active_work_order"]
        self.assertEqual(order["display_state"], "HUMAN_ACTION_REQUIRED")
        self.assertTrue(order["verification_pending"])
        self.assertIsNone(order["assignment_decision"]["selected_robot_id"])
        self.assertFalse(any(item["state"] in {"VERIFYING", "CLOSED"} for item in order["audit_transitions"]))


if __name__ == "__main__":
    unittest.main()
