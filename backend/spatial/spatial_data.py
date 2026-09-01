"""Deterministic spatial dataset for the Phase 2 demonstration.

Coordinates are local 2D SLAM coordinates in metres. They are deliberately
hand-authored demo geometry, not a replacement for production SLAM maps.
"""

from copy import deepcopy

MAPS = [
    {
        "map_id": "OUTDOOR", "label": "Outdoor", "building": "OUTDOOR", "floor": "Outdoor", "width": 100, "height": 60,
        "zones": [
            {"zone_id": "OUT-EAST-ROAD", "name": "East Road", "surface_type": "asphalt", "crowd_level": "medium", "cleaning_priority": "medium", "x": 8, "y": 31, "w": 37, "h": 18},
            {"zone_id": "OUT-PLAZA", "name": "Central Plaza", "surface_type": "granite", "crowd_level": "high", "cleaning_priority": "high", "x": 51, "y": 12, "w": 35, "h": 24},
            {"zone_id": "OUT-PERIMETER", "name": "Building Perimeter", "surface_type": "granite", "crowd_level": "low", "cleaning_priority": "low", "x": 51, "y": 42, "w": 38, "h": 9},
        ],
        "obstacles": [{"x": 11, "y": 12, "w": 28, "h": 8}, {"x": 58, "y": 42, "w": 22, "h": 5}],
        "entrances": [{"id": "OUT-A-ENTRY", "label": "A Entrance", "x": 42, "y": 25}, {"id": "OUT-B-ENTRY", "label": "B Entrance", "x": 88, "y": 25}],
        "navigation_nodes": [{"id": "OUT-N1", "x": 24, "y": 40}, {"id": "OUT-N2", "x": 68, "y": 28}],
    },
    {
        "map_id": "A_B1", "label": "A · B1", "building": "A", "floor": "B1", "width": 100, "height": 60,
        "zones": [{"zone_id": "A-B1-PARKING", "name": "Parking Aisle", "surface_type": "epoxy", "crowd_level": "low", "cleaning_priority": "medium", "x": 8, "y": 11, "w": 50, "h": 36}, {"zone_id": "A-B1-CORE", "name": "Lift Lobby", "surface_type": "tile", "crowd_level": "low", "cleaning_priority": "high", "x": 64, "y": 18, "w": 23, "h": 21}],
        "obstacles": [{"x": 14, "y": 19, "w": 35, "h": 5}, {"x": 14, "y": 34, "w": 35, "h": 5}],
        "elevators": [{"id": "A-ELEVATOR-B1", "label": "A Elevator", "x": 76, "y": 29}], "entrances": [{"id": "A-B1-RAMP", "label": "Vehicle Ramp", "x": 8, "y": 48}], "navigation_nodes": [{"id": "A-B1-N1", "x": 59, "y": 29}],
    },
    {
        "map_id": "A_1F", "label": "A · 1F", "building": "A", "floor": "1F", "width": 100, "height": 60,
        "zones": [{"zone_id": "A-1F-LOBBY", "name": "Main Lobby", "surface_type": "tile", "crowd_level": "high", "cleaning_priority": "high", "x": 8, "y": 10, "w": 43, "h": 34}, {"zone_id": "A-1F-CORRIDOR", "name": "East Corridor", "surface_type": "tile", "crowd_level": "medium", "cleaning_priority": "medium", "x": 57, "y": 15, "w": 29, "h": 22}],
        "obstacles": [{"x": 20, "y": 22, "w": 13, "h": 7}, {"x": 61, "y": 25, "w": 14, "h": 4}],
        "elevators": [{"id": "A-ELEVATOR-1F", "label": "A Elevator", "x": 85, "y": 27}], "entrances": [{"id": "A-1F-ENTRY", "label": "Main Entry", "x": 8, "y": 47}], "navigation_nodes": [{"id": "A-1F-N1", "x": 52, "y": 29}],
    },
    {
        "map_id": "A_2F", "label": "A · 2F", "building": "A", "floor": "2F", "width": 100, "height": 60,
        "zones": [{"zone_id": "A-2F-CORRIDOR", "name": "East Corridor", "surface_type": "tile", "crowd_level": "medium", "cleaning_priority": "medium", "x": 12, "y": 15, "w": 45, "h": 20}, {"zone_id": "A-2F-BRIDGE-LOBBY", "name": "Skybridge Lobby", "surface_type": "tile", "crowd_level": "medium", "cleaning_priority": "high", "x": 62, "y": 16, "w": 25, "h": 20}],
        "obstacles": [{"x": 18, "y": 23, "w": 18, "h": 4}],
        "elevators": [{"id": "A-ELEVATOR-2F", "label": "A Elevator", "x": 17, "y": 43}], "entrances": [{"id": "A-SKYBRIDGE", "label": "Skybridge", "x": 87, "y": 26}], "navigation_nodes": [{"id": "A-2F-N1", "x": 57, "y": 26}],
    },
    {
        "map_id": "B_1F", "label": "B · 1F", "building": "B", "floor": "1F", "width": 100, "height": 60,
        "zones": [{"zone_id": "B-1F-WEST-LOBBY", "name": "West Lobby", "surface_type": "carpet", "crowd_level": "high", "cleaning_priority": "high", "x": 8, "y": 12, "w": 43, "h": 30}, {"zone_id": "B-1F-EAST-CORRIDOR", "name": "East Corridor", "surface_type": "tile", "crowd_level": "medium", "cleaning_priority": "medium", "x": 57, "y": 16, "w": 27, "h": 19}],
        "obstacles": [{"x": 20, "y": 25, "w": 13, "h": 5}],
        "elevators": [{"id": "B-ELEVATOR-1F", "label": "B Elevator", "x": 85, "y": 27}], "entrances": [{"id": "B-1F-ENTRY", "label": "Main Entry", "x": 8, "y": 47}], "navigation_nodes": [{"id": "B-1F-N1", "x": 51, "y": 28}],
    },
    {
        "map_id": "B_2F", "label": "B · 2F", "building": "B", "floor": "2F", "width": 100, "height": 60,
        "zones": [{"zone_id": "B-2F-CORRIDOR", "name": "West Corridor", "surface_type": "tile", "crowd_level": "medium", "cleaning_priority": "medium", "x": 12, "y": 15, "w": 44, "h": 20}, {"zone_id": "B-2F-BRIDGE-LOBBY", "name": "Skybridge Lobby", "surface_type": "tile", "crowd_level": "medium", "cleaning_priority": "high", "x": 62, "y": 16, "w": 25, "h": 20}],
        "obstacles": [{"x": 20, "y": 23, "w": 17, "h": 4}],
        "elevators": [{"id": "B-ELEVATOR-2F", "label": "B Elevator", "x": 17, "y": 43}], "entrances": [{"id": "B-SKYBRIDGE", "label": "Skybridge", "x": 87, "y": 26}], "navigation_nodes": [{"id": "B-2F-N1", "x": 57, "y": 26}],
    },
]

CAMERAS = [
    {"camera_id": "CAM-OUT-01", "name": "Outdoor East Gate", "map_id": "OUTDOOR", "building": "OUTDOOR", "floor": "Outdoor", "zone": "East Road", "camera_position": {"x": 13, "y": 39}, "coverage_polygon": [{"x": 8, "y": 30}, {"x": 39, "y": 29}, {"x": 45, "y": 50}, {"x": 9, "y": 52}], "calibration_points": [{"pixel": {"u": 100, "v": 100}, "slam": {"x": 8, "y": 30}}, {"pixel": {"u": 900, "v": 100}, "slam": {"x": 45, "y": 30}}, {"pixel": {"u": 900, "v": 700}, "slam": {"x": 45, "y": 50}}, {"pixel": {"u": 100, "v": 700}, "slam": {"x": 8, "y": 50}}], "neighbor_cameras": ["CAM-A1-01"]},
    {"camera_id": "CAM-A-B1-01", "name": "A Parking Core", "map_id": "A_B1", "building": "A", "floor": "B1", "zone": "Lift Lobby", "camera_position": {"x": 69, "y": 22}, "coverage_polygon": [{"x": 62, "y": 16}, {"x": 88, "y": 16}, {"x": 88, "y": 42}, {"x": 62, "y": 42}], "calibration_points": [], "neighbor_cameras": ["CAM-A1-01"]},
    {"camera_id": "CAM-A1-01", "name": "A Lobby North", "map_id": "A_1F", "building": "A", "floor": "1F", "zone": "Main Lobby", "camera_position": {"x": 10, "y": 14}, "coverage_polygon": [{"x": 8, "y": 10}, {"x": 45, "y": 10}, {"x": 51, "y": 44}, {"x": 8, "y": 44}], "calibration_points": [{"pixel": {"u": 100, "v": 100}, "slam": {"x": 8, "y": 10}}, {"pixel": {"u": 900, "v": 100}, "slam": {"x": 51, "y": 10}}, {"pixel": {"u": 900, "v": 700}, "slam": {"x": 51, "y": 44}}, {"pixel": {"u": 100, "v": 700}, "slam": {"x": 8, "y": 44}}], "neighbor_cameras": ["CAM-A-B1-01", "CAM-A2-01", "CAM-A1-02", "CAM-A1-03"]},
    {"camera_id": "CAM-A1-02", "name": "A Lobby East", "map_id": "A_1F", "building": "A", "floor": "1F", "zone": "Main Lobby", "camera_position": {"x": 48, "y": 16}, "coverage_polygon": [{"x": 18, "y": 12}, {"x": 51, "y": 12}, {"x": 51, "y": 42}, {"x": 18, "y": 42}], "calibration_points": [], "neighbor_cameras": ["CAM-A1-01", "CAM-A1-03"]},
    {"camera_id": "CAM-A1-03", "name": "A Lobby South", "map_id": "A_1F", "building": "A", "floor": "1F", "zone": "Main Lobby", "camera_position": {"x": 18, "y": 40}, "coverage_polygon": [{"x": 8, "y": 20}, {"x": 40, "y": 20}, {"x": 40, "y": 44}, {"x": 8, "y": 44}], "calibration_points": [], "neighbor_cameras": ["CAM-A1-01", "CAM-A1-02"]},
    {"camera_id": "CAM-A2-01", "name": "A Skybridge Lobby", "map_id": "A_2F", "building": "A", "floor": "2F", "zone": "Skybridge Lobby", "camera_position": {"x": 76, "y": 20}, "coverage_polygon": [{"x": 60, "y": 14}, {"x": 90, "y": 14}, {"x": 90, "y": 39}, {"x": 60, "y": 39}], "calibration_points": [], "neighbor_cameras": ["CAM-A1-01", "CAM-B2-01"]},
    {"camera_id": "CAM-A1-04", "name": "A Lobby Reception", "map_id": "A_1F", "building": "A", "floor": "1F", "zone": "Main Lobby", "camera_position": {"x": 34, "y": 42}, "coverage_polygon": [{"x": 15, "y": 15}, {"x": 51, "y": 15}, {"x": 51, "y": 44}, {"x": 15, "y": 44}], "calibration_points": [], "neighbor_cameras": ["CAM-A1-01", "CAM-A1-02"]},
    {"camera_id": "CAM-A2-08", "name": "A 2F Corridor South", "map_id": "A_2F", "building": "A", "floor": "2F", "zone": "East Corridor", "camera_position": {"x": 18, "y": 18}, "coverage_polygon": [{"x": 12, "y": 15}, {"x": 57, "y": 15}, {"x": 57, "y": 35}, {"x": 12, "y": 35}], "calibration_points": [{"pixel": {"u": 100, "v": 100}, "slam": {"x": 12, "y": 15}}, {"pixel": {"u": 900, "v": 100}, "slam": {"x": 57, "y": 15}}, {"pixel": {"u": 900, "v": 700}, "slam": {"x": 57, "y": 35}}, {"pixel": {"u": 100, "v": 700}, "slam": {"x": 12, "y": 35}}], "neighbor_cameras": ["CAM-A2-11", "CAM-A2-01"]},
    {"camera_id": "CAM-A2-11", "name": "A 2F Recycling Point", "map_id": "A_2F", "building": "A", "floor": "2F", "zone": "East Corridor", "camera_position": {"x": 27, "y": 31}, "coverage_polygon": [{"x": 12, "y": 15}, {"x": 57, "y": 15}, {"x": 57, "y": 35}, {"x": 12, "y": 35}], "calibration_points": [{"pixel": {"u": 100, "v": 100}, "slam": {"x": 12, "y": 15}}, {"pixel": {"u": 900, "v": 100}, "slam": {"x": 57, "y": 15}}, {"pixel": {"u": 900, "v": 700}, "slam": {"x": 57, "y": 35}}, {"pixel": {"u": 100, "v": 700}, "slam": {"x": 12, "y": 35}}], "neighbor_cameras": ["CAM-A2-08", "CAM-A2-01"]},
    {"camera_id": "CAM-B1-01", "name": "B Lobby West", "map_id": "B_1F", "building": "B", "floor": "1F", "zone": "West Lobby", "camera_position": {"x": 11, "y": 15}, "coverage_polygon": [{"x": 8, "y": 10}, {"x": 50, "y": 10}, {"x": 50, "y": 43}, {"x": 8, "y": 43}], "calibration_points": [], "neighbor_cameras": ["CAM-B2-01"]},
    {"camera_id": "CAM-B2-01", "name": "B Skybridge Lobby", "map_id": "B_2F", "building": "B", "floor": "2F", "zone": "Skybridge Lobby", "camera_position": {"x": 76, "y": 20}, "coverage_polygon": [{"x": 60, "y": 14}, {"x": 90, "y": 14}, {"x": 90, "y": 39}, {"x": 60, "y": 39}], "calibration_points": [], "neighbor_cameras": ["CAM-B1-01", "CAM-A2-01"]},
]

ROBOT_POSITIONS = {
    "robot-a": {"map_id": "OUTDOOR", "x": 30, "y": 26},
    "robot-b": {"map_id": "A_1F", "x": 10, "y": 10},
    "robot-c": {"map_id": "B_1F", "x": 24, "y": 45},
}

# Calibrated overview geometry for the campus white-model. These points are
# part of the persisted navigation plan, while the canonical map_id/x/y and
# Dijkstra topology remain the operational routing source of truth.
ROBOT_ROUTE_VISUALS = {
    "robot-a": [
        {"x": 68.4, "y": 80.0, "node_id": "OUTDOOR", "label": "B栋侧道路待命点", "progress_label": "已从 B 栋侧道路待命点出发"},
        {"x": 34.0, "y": 63.7, "node_id": "OUTDOOR", "label": "A栋侧道路终点", "progress_label": "已抵达 A 栋侧道路终点"},
    ],
    "robot-b": [
        {"x": 16.0, "y": 44.1, "node_id": "A_1F", "label": "A栋1F内部起点", "progress_label": "已从 A 栋 1F 内侧清洁通道出发"},
        {"x": 31.8, "y": 49.4, "node_id": "A_1F", "label": "B栋方向终点", "progress_label": "已抵达 A 栋 1F 东侧作业终点"},
    ],
    "robot-c": [
        {"x": 80.0, "y": 63.3, "node_id": "B_1F", "label": "B栋1F内部起点", "progress_label": "已从 B 栋 1F 内侧清洁区出发"},
        {"x": 70.0, "y": 60.1, "node_id": "B_ELEVATOR_1F", "label": "B栋1F电梯口", "progress_label": "已到达 B 栋 1F 电梯口"},
        {"x": 70.0, "y": 38.5, "node_id": "B_ELEVATOR_2F", "label": "B栋2F电梯口", "progress_label": "已到达 B 栋 2F 电梯口"},
        {"x": 64.0, "y": 36.5, "node_id": "SKYBRIDGE_B", "label": "B栋2F连廊入口", "progress_label": "已到达 B 栋 2F 连廊入口"},
        {"x": 41.0, "y": 27.4, "node_id": "A_2F", "label": "A栋2F连廊入口", "progress_label": "已抵达 A 栋 2F 连廊入口"},
    ],
}

ROBOT_ROUTE_STYLES = {
    "robot-a": {"route": "#b91c1c", "opacity": 0.45, "stroke_width": 5, "dasharray": "7 5"},
    "robot-b": {"route": "#b91c1c", "opacity": 0.45, "stroke_width": 5, "dasharray": "7 5"},
    "robot-c": {"route": "#b91c1c", "opacity": 0.45, "stroke_width": 5, "dasharray": "7 5"},
}
VISUAL_ROUTE_VERSION = 5


def robot_visual_standby(robot_id: str) -> dict | None:
    """Return the fixed white-model standby position without changing fleet facts."""
    path = ROBOT_ROUTE_VISUALS.get(robot_id, [])
    return deepcopy(path[0]) if path else None


def robot_visual_endpoint(robot_id: str) -> dict | None:
    """Return the approved overview terminal position for a cleaning robot."""
    path = ROBOT_ROUTE_VISUALS.get(robot_id, [])
    return deepcopy(path[-1]) if path else None


def calibrated_visual_route(robot_id: str, _node_path: list[str] | tuple[str, ...] | None) -> dict | None:
    """Return the approved white-model route without changing operational topology.

    A robot can resume an event from a later operational topology node.  The
    calibrated overview remains the approved demonstration geometry, so it is
    intentionally independent from that mutable Dijkstra start node.
    """
    path = ROBOT_ROUTE_VISUALS.get(robot_id, [])
    if not path or any(point.get("node_id") not in GRAPH_NODES for point in path):
        return None
    return {
        "visual_route_version": VISUAL_ROUTE_VERSION,
        "visual_path": deepcopy(path),
        "visual_style": deepcopy(ROBOT_ROUTE_STYLES.get(robot_id, {})),
    }

# Edges are intentionally explicit. A production system would derive same-floor
# travel from a costmap; Phase 2 demonstrates the campus connector topology.
GRAPH_NODES = {
    "OUTDOOR": {"label": "Outdoor", "map_id": "OUTDOOR"},
    "A_B1": {"label": "A-B1", "map_id": "A_B1"}, "A_1F": {"label": "A-1F", "map_id": "A_1F"}, "A_2F": {"label": "A-2F", "map_id": "A_2F"},
    "B_1F": {"label": "B-1F", "map_id": "B_1F"}, "B_2F": {"label": "B-2F", "map_id": "B_2F"},
    "A_ELEVATOR_B1": {"label": "A Elevator", "kind": "elevator"}, "A_ELEVATOR_1F": {"label": "A Elevator", "kind": "elevator"}, "A_ELEVATOR_2F": {"label": "A Elevator", "kind": "elevator"},
    "B_ELEVATOR_1F": {"label": "B Elevator", "kind": "elevator"}, "B_ELEVATOR_2F": {"label": "B Elevator", "kind": "elevator"},
    "SKYBRIDGE_B": {"label": "Skybridge", "kind": "skybridge"}, "SKYBRIDGE_A": {"label": "Skybridge", "kind": "skybridge"},
}

GRAPH_EDGES = [
    # Each elevator transition deliberately lands on a floor map. This keeps
    # intermediate floors visible in an explainable cross-floor route.
    ("A_1F", "A_ELEVATOR_1F", 12, "local"), ("A_2F", "A_ELEVATOR_2F", 13, "local"),
    ("A_ELEVATOR_2F", "A_1F", 32, "elevator"), ("A_ELEVATOR_1F", "A_B1", 38, "elevator"),
    ("B_1F", "B_ELEVATOR_1F", 12, "local"), ("B_2F", "B_ELEVATOR_2F", 13, "local"), ("B_ELEVATOR_1F", "B_ELEVATOR_2F", 32, "elevator"),
    ("B_2F", "SKYBRIDGE_B", 11, "local"), ("SKYBRIDGE_B", "SKYBRIDGE_A", 42, "skybridge"), ("SKYBRIDGE_A", "A_2F", 11, "local"),
]
