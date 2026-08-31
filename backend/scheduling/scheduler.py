from __future__ import annotations

from scheduling.config import SCORE_WEIGHTS


def _score(task: dict, candidate: dict) -> dict[str, float]:
    robot, profile, route = candidate["robot"], candidate["profile"], candidate["route"]
    required = set(task["required_capabilities"])
    fit_ratio = sum(profile.get("capability_quality", {}).get(capability, 1) for capability in required) / max(len(required), 1)
    route_cost = route["total_cost"] if route else 250
    segment_types = {segment["type"] for segment in (route or {"segments": []})["segments"]}
    high_crowd = task.get("crowd_level") == "high"
    capability = SCORE_WEIGHTS["capability_fit"] * fit_ratio
    eta = SCORE_WEIGHTS["eta_distance"] * max(0, 1 - route_cost / 300)
    battery = SCORE_WEIGHTS["battery"] * min(robot["battery"], 100) / 100
    workload = SCORE_WEIGHTS["workload"] if robot["status"] == "idle" else SCORE_WEIGHTS["workload"] * 0.55
    zone = SCORE_WEIGHTS["zone_fitness"] if task["surface"] in profile["surfaces"] else 0
    floor = SCORE_WEIGHTS["floor_elevator_cost"] * (0.4 if "elevator" in segment_types else 1)
    cross = SCORE_WEIGHTS["cross_building_cost"] * (0.35 if "skybridge" in segment_types else 1)
    noise = SCORE_WEIGHTS["noise_public_space"] * (0.2 if high_crowd and profile["noise"] == "high" else 1)
    return {"capability_fit": round(capability, 2), "eta_distance": round(eta, 2), "battery": round(battery, 2), "workload": round(workload, 2), "zone_fitness": round(zone, 2), "floor_elevator_cost": round(floor, 2), "cross_building_cost": round(cross, 2), "noise_public_space": round(noise, 2)}


def make_assignment_decision(task: dict, evaluations: list[dict]) -> dict:
    candidates = []
    for evaluation in evaluations:
        robot, profile = evaluation["robot"], evaluation["profile"]
        position = robot.get("coordinates") or {}
        entry = {
            "robot_id": robot["id"], "robot_name": robot["short_name"], "eligible": evaluation["eligible"], "reject_reasons": evaluation["reject_reasons"], "score_components": {}, "final_score": None, "route": evaluation["route"],
            "battery": robot.get("battery"), "capabilities": sorted(profile["capabilities"]), "surfaces": sorted(profile["surfaces"]), "service_scope": profile["service_scope"],
            "map_id": robot.get("map_id"), "current_location": robot.get("location") or f"{robot.get('building', '')}栋 {robot.get('floor', '')} · X {position.get('x', '—')} / Y {position.get('y', '—')}",
        }
        if evaluation["eligible"]:
            components = _score(task, evaluation)
            entry["score_components"] = components
            entry["final_score"] = round(sum(components.values()), 2)
        candidates.append(entry)
    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    if not eligible:
        return {"status": "HUMAN_FALLBACK", "selected_robot_id": None, "selected_robot_name": None, "candidate_count": 0, "reason": "No robot passes hard constraints; create manual work order.", "weights": SCORE_WEIGHTS, "candidates": candidates}
    selected = max(eligible, key=lambda candidate: candidate["final_score"])
    return {"status": "ASSIGNED", "selected_robot_id": selected["robot_id"], "selected_robot_name": selected["robot_name"], "candidate_count": len(eligible), "reason": f"{selected['robot_name']} is the highest eligible deterministic score ({selected['final_score']}).", "weights": SCORE_WEIGHTS, "candidates": candidates}
