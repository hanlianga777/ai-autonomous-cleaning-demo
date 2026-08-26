"""PoC robot capability profiles. They are not vendor specifications."""

ROBOT_CAPABILITIES = {
    "robot-a": {"robot_id": "robot-a", "service_scope": "outdoor", "surfaces": {"asphalt", "granite"}, "capabilities": {"outdoor", "dry_debris", "road_sweeping"}, "elevator": False, "skybridge": False, "noise": "medium", "size": "large", "public_space_fitness": "medium"},
    "robot-b": {"robot_id": "robot-b", "service_scope": "a_indoor", "surfaces": {"tile", "epoxy"}, "capabilities": {"wet_cleaning", "strong_suction", "scrubbing", "heavy_stain", "dry_debris"}, "capability_quality": {"dry_debris": 0.45}, "elevator": True, "skybridge": False, "noise": "high", "size": "large", "public_space_fitness": "low"},
    "robot-c": {"robot_id": "robot-c", "service_scope": "indoor", "surfaces": {"tile", "carpet"}, "capabilities": {"dry_debris", "light_cleaning"}, "elevator": True, "skybridge": True, "noise": "low", "size": "compact", "public_space_fitness": "high"},
}
