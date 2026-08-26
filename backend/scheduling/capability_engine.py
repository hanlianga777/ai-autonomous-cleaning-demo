from __future__ import annotations

from scheduling.config import MIN_BATTERY_PERCENT
from scheduling.profiles import ROBOT_CAPABILITIES
from spatial.route_planner import RouteNotFoundError, plan_route
from spatial.spatial_data import ROBOT_POSITIONS


def evaluate_capabilities(task_profile: dict, location: dict, robots: list[dict]) -> list[dict]:
    """Return every robot, including explicit hard-filter reject reasons."""
    evaluations = []
    target_map = location["map_id"]
    for robot in robots:
        profile = ROBOT_CAPABILITIES[robot["id"]]
        reject_reasons: list[str] = []
        if robot["battery"] < MIN_BATTERY_PERCENT:
            reject_reasons.append(f"battery below {MIN_BATTERY_PERCENT}%")
        if robot["status"] != "idle":
            reject_reasons.append(f"robot state is {robot['status']}")
        if task_profile["surface"] not in profile["surfaces"]:
            reject_reasons.append(f"surface {task_profile['surface']} unsupported")
        missing = set(task_profile["required_capabilities"]) - profile["capabilities"]
        if missing:
            reject_reasons.append(f"missing capabilities: {', '.join(sorted(missing))}")
        if location["building"] == "OUTDOOR" and profile["service_scope"] != "outdoor":
            reject_reasons.append("outdoor task requires outdoor robot")
        if location["building"] != "OUTDOOR" and profile["service_scope"] == "outdoor":
            reject_reasons.append("outdoor-only robot cannot enter building")
        if profile["service_scope"] == "a_indoor" and location["building"] != "A":
            reject_reasons.append("Robot B is limited to A building")
        route = None
        try:
            route = plan_route(ROBOT_POSITIONS[robot["id"]]["map_id"], target_map)
            segment_types = {segment["type"] for segment in route["segments"]}
            if "elevator" in segment_types and not profile["elevator"]:
                reject_reasons.append("required route uses elevator")
            if "skybridge" in segment_types and not profile["skybridge"]:
                reject_reasons.append("required route uses skybridge")
        except RouteNotFoundError:
            reject_reasons.append("target is not spatially reachable")
        evaluations.append({"robot": robot, "profile": profile, "route": route, "eligible": not reject_reasons, "reject_reasons": reject_reasons})
    return evaluations
