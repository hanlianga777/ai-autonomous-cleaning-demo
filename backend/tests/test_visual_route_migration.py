import tempfile
import unittest
from pathlib import Path

from database import connection
from spatial.spatial_data import VISUAL_ROUTE_VERSION


class VisualRouteMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.previous_path = connection.DATABASE_PATH
        connection.DATABASE_PATH = Path(self.temp.name) / "visual-route-migration.sqlite"
        connection.initialize_database()

    def tearDown(self) -> None:
        connection.DATABASE_PATH = self.previous_path
        self.temp.cleanup()

    def test_legacy_navigation_snapshot_is_backfilled_without_changing_business_route(self) -> None:
        event_id = "integrated-demo03-legacy"
        legacy_plan = {
            "robot_id": "robot-c",
            "start_map": "B_1F",
            "target_map": "A_2F",
            "node_path": ["B_1F", "B_ELEVATOR_1F", "B_ELEVATOR_2F", "B_2F", "SKYBRIDGE_B", "SKYBRIDGE_A", "A_2F"],
            "segments": [{"from": "B_ELEVATOR_1F", "to": "B_ELEVATOR_2F", "type": "elevator"}, {"from": "SKYBRIDGE_B", "to": "SKYBRIDGE_A", "type": "skybridge"}],
        }
        connection.save_event({"event_id": event_id, "state": "CLOSED", "demo_v1": {}})
        connection.record_transition(event_id, "NAVIGATING", {"navigation_plan": legacy_plan})

        connection.initialize_database()

        transition = connection.get_transitions(event_id)[0]["detail"]["navigation_plan"]
        stored = connection.get_event(event_id)["demo_v1"]["navigation_plan"]
        self.assertEqual(transition, stored)
        self.assertEqual(transition["visual_route_version"], VISUAL_ROUTE_VERSION)
        self.assertEqual(transition["visual_style"]["planned"], "#ef4444")
        self.assertEqual([point["node_id"] for point in transition["visual_path"]], ["B_1F", "B_ELEVATOR_1F", "B_ELEVATOR_2F", "SKYBRIDGE_B", "A_2F"])
        self.assertEqual(transition["node_path"], legacy_plan["node_path"])
        self.assertEqual(transition["segments"], legacy_plan["segments"])


if __name__ == "__main__":
    unittest.main()
