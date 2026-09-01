import unittest

from spatial.calibration import map_pixel_to_slam
from spatial.route_planner import plan_route
from spatial.spatial_data import (
    ROBOT_POSITIONS,
    ROBOT_ROUTE_STYLES,
    ROBOT_ROUTE_VISUALS,
    VISUAL_ROUTE_VERSION,
    calibrated_visual_route,
    robot_visual_endpoint,
    robot_visual_standby,
)
from demo_v1.service import DEMO_STAGE_PAUSES, stage_pause_seconds


class SpatialEngineTests(unittest.TestCase):
    def test_a_building_cross_floor_route(self):
        route = plan_route("A_2F", "A_B1")
        self.assertEqual(route["display_path"], ["A-2F", "A Elevator", "A-1F", "A Elevator", "A-B1"])

    def test_cross_building_route(self):
        route = plan_route("B_1F", "A_1F")
        self.assertEqual(route["display_path"], ["B-1F", "B Elevator", "B-2F", "Skybridge", "A-2F", "A Elevator", "A-1F"])

    def test_four_point_calibration_is_stable(self):
        first = map_pixel_to_slam("CAM-A1-01", 500, 400)
        second = map_pixel_to_slam("CAM-A1-01", 500, 400)
        self.assertEqual(first, second)
        self.assertEqual(first["location"], {"building": "A", "floor": "1F", "zone": "Main Lobby", "map_id": "A_1F", "x": 29.5, "y": 27.0})

    def test_cleaning_route_calibration_preserves_requested_starts_and_cross_building_connectors(self):
        self.assertEqual(ROBOT_POSITIONS["robot-a"], {"map_id": "OUTDOOR", "x": 30, "y": 26})
        self.assertEqual(ROBOT_POSITIONS["robot-b"], {"map_id": "A_1F", "x": 10, "y": 10})
        self.assertEqual(ROBOT_POSITIONS["robot-c"], {"map_id": "B_1F", "x": 24, "y": 45})
        self.assertEqual(len(ROBOT_ROUTE_VISUALS["robot-a"]), 2)
        self.assertEqual(ROBOT_ROUTE_VISUALS["robot-a"][0]["label"], "B栋侧道路待命点")
        self.assertEqual(ROBOT_ROUTE_VISUALS["robot-a"][-1]["label"], "A栋侧道路终点")
        self.assertEqual(len(ROBOT_ROUTE_VISUALS["robot-b"]), 2)
        self.assertEqual(ROBOT_ROUTE_VISUALS["robot-b"][0]["label"], "A栋1F内部起点")
        self.assertEqual(ROBOT_ROUTE_VISUALS["robot-b"][-1]["label"], "B栋方向终点")
        path = ROBOT_ROUTE_VISUALS["robot-c"]
        self.assertEqual(len(path), 5)
        self.assertEqual(path[0]["node_id"], "B_1F")
        self.assertEqual([point["node_id"] for point in path[1:-1]], ["B_ELEVATOR_1F", "B_ELEVATOR_2F", "SKYBRIDGE_B"])
        self.assertEqual(path[-1]["node_id"], "A_2F")
        self.assertEqual(VISUAL_ROUTE_VERSION, 5)
        self.assertEqual(set(tuple(style.items()) for style in ROBOT_ROUTE_STYLES.values()), {
            (("route", "#b91c1c"), ("opacity", 0.45), ("stroke_width", 5), ("dasharray", "7 5")),
        })
        self.assertEqual(robot_visual_standby("robot-a"), ROBOT_ROUTE_VISUALS["robot-a"][0])
        self.assertEqual(robot_visual_standby("robot-b"), ROBOT_ROUTE_VISUALS["robot-b"][0])
        self.assertEqual(robot_visual_standby("robot-c"), ROBOT_ROUTE_VISUALS["robot-c"][0])
        self.assertIsNone(robot_visual_standby("robot-d"))
        self.assertEqual(robot_visual_endpoint("robot-a"), ROBOT_ROUTE_VISUALS["robot-a"][-1])
        self.assertEqual(robot_visual_endpoint("robot-c"), path[-1])
        self.assertEqual(path[1]["x"], path[2]["x"], "Demo03 elevator remains vertically aligned")
        self.assertEqual(ROBOT_ROUTE_VISUALS["robot-a"][-1]["y"], 63.7)
        self.assertAlmostEqual(
            (ROBOT_ROUTE_VISUALS["robot-a"][0]["y"] - ROBOT_ROUTE_VISUALS["robot-a"][-1]["y"])
            / (ROBOT_ROUTE_VISUALS["robot-a"][0]["x"] - ROBOT_ROUTE_VISUALS["robot-a"][-1]["x"]),
            16.3 / 34.4,
            msg="Demo01 remains parallel to the white-model road center dashes",
        )
        self.assertEqual(path[-1]["y"], 27.4)
        self.assertAlmostEqual((path[-1]["y"] - path[-2]["y"]) / (path[-1]["x"] - path[-2]["x"]), 9.1 / 23)
        route = calibrated_visual_route("robot-c", ["B_1F", "B_ELEVATOR_1F", "B_ELEVATOR_2F", "B_2F", "SKYBRIDGE_B", "SKYBRIDGE_A", "A_2F"])
        self.assertEqual(route["visual_route_version"], VISUAL_ROUTE_VERSION)
        self.assertEqual(route["visual_path"], path)
        self.assertIsNone(calibrated_visual_route("unknown-robot", ["B_1F"]))

    def test_realistic_stage_pacing_uses_longer_cross_building_navigation(self):
        self.assertEqual(DEMO_STAGE_PAUSES, {
            "DETECTED": 2.0, "EDGE_DETECTED": 3.0, "SINGLE_VIEW_REVIEW": 2.0,
            "CLOUD_REVIEW": 3.0, "LOCATED": 4.0, "ASSIGNED": 2.0,
            "ARRIVED": 3.0, "CLEANING_COMPLETED": 3.0, "VERIFYING": 2.0,
        })
        self.assertEqual(stage_pause_seconds({"state": "EDGE_DETECTED"}), 3.0)
        self.assertEqual(stage_pause_seconds({"state": "LOCATED"}), 4.0)
        self.assertEqual(stage_pause_seconds({"state": "NAVIGATING", "demo_v1": {"navigation_plan": {"segments": []}}}), 8.0)
        self.assertEqual(stage_pause_seconds({"state": "NAVIGATING", "demo_v1": {"navigation_plan": {"segments": [{"type": "skybridge"}]}}}), 10.0)


if __name__ == "__main__":
    unittest.main()
