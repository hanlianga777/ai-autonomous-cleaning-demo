"""Stable Phase 3 fixtures. They do not make any real AI request."""

EVENT_TEMPLATES = {
    "outdoor_debris": {
        "label": "室外普通垃圾 · Robot A",
        "template": "outdoor_debris", "confidence": 0.94, "camera_id": "CAM-OUT-01",
        "location": {"building": "OUTDOOR", "floor": "Outdoor", "zone": "East Road", "map_id": "OUTDOOR", "x": 29.0, "y": 40.0},
        "task_profile": {"object_type": "small_litter", "pollution_form": "dry_debris", "severity": "low", "estimated_area": 0.2, "surface": "asphalt", "required_capabilities": ["outdoor", "dry_debris"], "priority": "normal", "crowd_level": "medium"},
    },
    "heavy_spill": {
        "label": "A 栋重度液体污渍 · Robot B",
        "template": "heavy_spill", "confidence": 0.92, "camera_id": "CAM-A1-01",
        "location": {"building": "A", "floor": "1F", "zone": "Main Lobby", "map_id": "A_1F", "x": 29.5, "y": 27.0},
        "task_profile": {"object_type": "beverage_spill", "pollution_form": "liquid", "severity": "high", "estimated_area": 3.5, "surface": "tile", "required_capabilities": ["wet_cleaning", "strong_suction", "scrubbing"], "priority": "high", "crowd_level": "high"},
    },
    "cross_building_debris": {
        "label": "跨楼栋纸杯 · Robot C",
        "template": "cross_building_debris", "confidence": 0.91, "camera_id": "CAM-A1-01",
        "location": {"building": "A", "floor": "1F", "zone": "East Corridor", "map_id": "A_1F", "x": 66.0, "y": 30.0},
        "task_profile": {"object_type": "paper_cup", "pollution_form": "dry_debris", "severity": "low", "estimated_area": 0.15, "surface": "tile", "required_capabilities": ["dry_debris"], "priority": "normal", "crowd_level": "high"},
    },
    "oversized_object": {
        "label": "大型纸箱 · Human Fallback",
        "template": "oversized_object", "confidence": 0.97, "camera_id": "CAM-A1-01",
        "location": {"building": "A", "floor": "1F", "zone": "Main Lobby", "map_id": "A_1F", "x": 23.0, "y": 25.0},
        "task_profile": {"object_type": "large_cardboard_box", "pollution_form": "large_object", "severity": "medium", "estimated_area": 2.0, "surface": "tile", "required_capabilities": ["large_object_pickup"], "priority": "normal", "crowd_level": "high"},
    },
}
