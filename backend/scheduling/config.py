"""Demo-only, explicitly configurable scheduler policy."""

MIN_BATTERY_PERCENT = 20
SCORE_WEIGHTS = {
    "capability_fit": 25,
    "eta_distance": 25,
    "battery": 15,
    "workload": 10,
    "zone_fitness": 10,
    "floor_elevator_cost": 5,
    "cross_building_cost": 5,
    "noise_public_space": 5,
}
