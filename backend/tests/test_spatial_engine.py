import unittest

from spatial.calibration import map_pixel_to_slam
from spatial.route_planner import plan_route


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
        self.assertEqual(first["location"], {"building": "A", "floor": "1F", "zone": "Main Lobby", "x": 29.5, "y": 27.0})


if __name__ == "__main__":
    unittest.main()
