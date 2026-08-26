import os
import tempfile
import unittest

from database import connection
from perception.multiview.agent import run_multi_view_agent
from perception.multiview.config import MAX_ADDITIONAL_CAMERAS, MAX_AGENT_ITERATIONS
from workflow.engine import run_scenario_02


class MultiViewAgentTests(unittest.TestCase):
    location = {"building": "A", "floor": "1F", "zone": "Main Lobby", "map_id": "A_1F", "x": 29.5, "y": 27.0}

    @classmethod
    def setUpClass(cls):
        cls._database_path = connection.DATABASE_PATH
        cls._temp_dir = tempfile.TemporaryDirectory()
        connection.DATABASE_PATH = os.path.join(cls._temp_dir.name, "multiview-test.db")
        connection.initialize_database()

    @classmethod
    def tearDownClass(cls):
        connection.DATABASE_PATH = cls._database_path
        cls._temp_dir.cleanup()

    def test_only_gray_zone_triggers_agent(self):
        high_confidence = run_multi_view_agent(0.85, "CAM-A1-01", self.location)
        low_confidence = run_multi_view_agent(0.54, "CAM-A1-01", self.location)
        self.assertFalse(high_confidence["triggered"])
        self.assertFalse(low_confidence["triggered"])
        self.assertEqual(high_confidence["tool_calls"], [])
        self.assertEqual(low_confidence["tool_calls"], [])
        self.assertIsNone(high_confidence["decision"])
        self.assertIsNone(low_confidence["decision"])

    def test_scenario_02_uses_only_allowed_tools_with_bounded_calls(self):
        result = run_multi_view_agent(0.67, "CAM-A1-01", self.location, "scenario02")
        self.assertTrue(result["triggered"])
        self.assertEqual(result["decision"], "CONFIRM")
        self.assertGreaterEqual(result["final_confidence"], 0.85)
        self.assertLessEqual(len(result["selected_cameras"]), MAX_ADDITIONAL_CAMERAS)
        self.assertLessEqual(result["iteration_count"], MAX_AGENT_ITERATIONS)
        self.assertEqual({call["tool"] for call in result["tool_calls"]}, {"Camera Coverage Tool", "Frame Fetch Tool", "VLM Tool"})
        self.assertNotIn("chain_of_thought", str(result).lower())

    def test_scenario_02_confirms_then_uses_existing_robot_b_scheduler_path(self):
        event = run_scenario_02()
        trace = event["multi_view_trace"]
        self.assertEqual(trace["decision"], "CONFIRM")
        self.assertEqual(event["assignment_decision"]["selected_robot_name"], "Robot B")
        self.assertEqual(event["state"], "CLOSED")
        states = [transition["state"] for transition in event["transitions"]]
        self.assertIn("MULTI_VIEW", states)
        self.assertIn("CONFIRMED", states)


if __name__ == "__main__":
    unittest.main()
