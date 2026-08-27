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
    "multiview_heavy_spill": {
        "label": "Scenario 02 · 多视角奶茶重污 · Robot B",
        "template": "multiview_heavy_spill", "confidence": 0.67, "camera_id": "CAM-A1-01",
        "location": {"building": "A", "floor": "1F", "zone": "Main Lobby", "map_id": "A_1F", "x": 29.5, "y": 27.0},
        "task_profile": {"object_type": "beverage_spill", "pollution_form": "liquid", "severity": "high", "estimated_area": 3.5, "surface": "tile", "required_capabilities": ["wet_cleaning", "strong_suction", "scrubbing"], "priority": "high", "crowd_level": "high"},
        "multi_view_scenario": "scenario02",
    },
    "cross_building_debris": {
        "label": "跨楼栋纸杯 · Robot C",
        "template": "cross_building_debris", "confidence": 0.91, "camera_id": "CAM-A1-01",
        "location": {"building": "A", "floor": "1F", "zone": "East Corridor", "map_id": "A_1F", "x": 66.0, "y": 30.0},
        "task_profile": {"object_type": "paper_cup", "pollution_form": "dry_debris", "severity": "low", "estimated_area": 0.15, "surface": "tile", "required_capabilities": ["dry_debris"], "priority": "normal", "crowd_level": "high"},
    },
    "indoor_can": {
        "label": "A 栋 2F 易拉罐 · Robot C",
        "template": "indoor_can", "confidence": 0.93, "camera_id": "CAM-A2-08",
        "location": {"building": "A", "floor": "2F", "zone": "East Corridor", "map_id": "A_2F", "x": 37.0, "y": 25.0},
        "task_profile": {"object_type": "aluminum_can", "pollution_form": "dry_debris", "severity": "low", "estimated_area": 0.08, "surface": "carpet", "required_capabilities": ["dry_debris", "light_cleaning"], "priority": "normal", "crowd_level": "medium"},
    },
    "oversized_object": {
        "label": "大型纸箱 · Human Fallback",
        "template": "oversized_object", "confidence": 0.97, "camera_id": "CAM-A1-01",
        "location": {"building": "A", "floor": "1F", "zone": "Main Lobby", "map_id": "A_1F", "x": 23.0, "y": 25.0},
        "task_profile": {"object_type": "large_cardboard_box", "pollution_form": "large_object", "severity": "medium", "estimated_area": 2.0, "surface": "tile", "required_capabilities": ["large_object_pickup"], "priority": "normal", "crowd_level": "high"},
    },
    "oversized_object_a2": {
        "label": "A 栋 2F 大型纸箱 · Human Fallback",
        "template": "oversized_object_a2", "confidence": 0.97, "camera_id": "CAM-A2-11",
        "location": {"building": "A", "floor": "2F", "zone": "East Corridor", "map_id": "A_2F", "x": 20.0, "y": 26.0},
        "task_profile": {"object_type": "large_cardboard_box", "pollution_form": "large_object", "severity": "medium", "estimated_area": 2.0, "surface": "carpet", "required_capabilities": ["large_object_pickup"], "priority": "normal", "crowd_level": "medium"},
    },
}
