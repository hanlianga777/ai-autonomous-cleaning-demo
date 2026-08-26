from __future__ import annotations

from data.mock_data import ROBOTS
from spatial.spatial_data import ROBOT_POSITIONS


class MockRobotAdapter:
    """Vendor-neutral mock preserving the real adapter surface."""

    def get_status(self, robot_id: str) -> dict:
        return next(robot for robot in ROBOTS if robot["id"] == robot_id)

    def get_position(self, robot_id: str) -> dict:
        return ROBOT_POSITIONS[robot_id]

    def assign_task(self, robot_id: str, task_id: str) -> dict:
        return {"robot_id": robot_id, "task_id": task_id, "accepted": True, "adapter": "mock"}

    def navigate(self, robot_id: str, navigation_plan: dict) -> dict:
        return {"robot_id": robot_id, "accepted": True, "route_cost": navigation_plan["total_cost"], "adapter": "mock"}

    def start_cleaning(self, robot_id: str, task_profile: dict) -> dict:
        return {"robot_id": robot_id, "accepted": True, "cleaning_mode": task_profile["pollution_form"], "adapter": "mock"}

    def cancel_task(self, robot_id: str, task_id: str) -> dict:
        return {"robot_id": robot_id, "task_id": task_id, "cancelled": True, "adapter": "mock"}
