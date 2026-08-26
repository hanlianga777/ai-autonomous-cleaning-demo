import os
import tempfile
import unittest

from database import connection


class WorkflowSchedulerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._database_path = connection.DATABASE_PATH
        cls._temp_dir = tempfile.TemporaryDirectory()
        connection.DATABASE_PATH = os.path.join(cls._temp_dir.name, "workflow-test.db")
        connection.initialize_database()

    @classmethod
    def tearDownClass(cls):
        connection.DATABASE_PATH = cls._database_path
        cls._temp_dir.cleanup()

    def test_heavy_spill_selects_heavy_scrubber_and_closes(self):
        from workflow.engine import create_mock_event, run_event

        event = create_mock_event("heavy_spill")
        result = run_event(event["event_id"])
        self.assertEqual(result["state"], "CLOSED")
        self.assertEqual(result["assignment_decision"]["selected_robot_id"], "robot-b")
        self.assertEqual(result["verification"]["result"], "PASS")

    def test_large_object_uses_human_fallback(self):
        from workflow.engine import create_mock_event, run_event

        event = create_mock_event("oversized_object")
        result = run_event(event["event_id"])
        self.assertEqual(result["state"], "CLOSED")
        self.assertEqual(result["assignment_decision"]["status"], "HUMAN_FALLBACK")
        self.assertIsNotNone(result["human_fallback"])

    def test_cross_building_event_preserves_connector_states(self):
        from workflow.engine import create_mock_event, run_event

        event = create_mock_event("cross_building_debris")
        result = run_event(event["event_id"])
        states = [transition["state"] for transition in result["transitions"]]
        self.assertEqual(result["assignment_decision"]["selected_robot_id"], "robot-c")
        self.assertIn("IN_ELEVATOR", states)
        self.assertIn("SKYBRIDGE", states)


if __name__ == "__main__":
    unittest.main()
