from __future__ import annotations

from spatial.spatial_data import CAMERAS, MAPS, ROBOT_POSITIONS


def spatial_overview() -> dict:
    return {"maps": MAPS, "cameras": CAMERAS, "robot_positions": ROBOT_POSITIONS}


def get_map(map_id: str) -> dict | None:
    map_data = next((item for item in MAPS if item["map_id"] == map_id), None)
    if map_data is None:
        return None
    result = dict(map_data)
    result["cameras"] = [camera for camera in CAMERAS if camera["map_id"] == map_id]
    result["robots"] = [{"robot_id": robot_id, **position} for robot_id, position in ROBOT_POSITIONS.items() if position["map_id"] == map_id]
    return result
