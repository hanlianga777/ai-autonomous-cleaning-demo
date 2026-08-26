"""A transparent, bounded optimization recommendation layer over analytics."""

from __future__ import annotations

from analytics.service import heatmap, robot_utilization, task_history


def heatmap_tool() -> dict:
    points = heatmap()
    return {"tool": "Heatmap Tool", "top_hotspot": points[0], "points_considered": len(points)}


def robot_utilization_tool() -> dict:
    utilization = robot_utilization()
    return {"tool": "Robot Utilization Tool", "lowest_utilization": min(utilization, key=lambda row: row["utilization"]), "robots_considered": len(utilization)}


def task_history_tool() -> dict:
    history = task_history()
    evening_a1 = sum(record["zone_id"] == "a1-east-entrance" and 17 <= int(record["timestamp"][11:13]) <= 19 for record in history)
    return {"tool": "Task History Tool", "records_considered": len(history), "a1_evening_events": evening_a1}


def generate_recommendations() -> dict:
    """Return actions only; it never alters CV confidence, capabilities, or scheduling."""
    calls = [heatmap_tool(), robot_utilization_tool(), task_history_tool()]
    return {
        "source": "DEMO MOCK MODE", "tool_calls": calls,
        "recommendations": [
            {"type": "STANDBY_POINT", "priority": "high", "title": "Robot B 傍晚前置到 A 栋 1F 服务区", "rationale": "A 栋 1F 东入口为 30 天最高热点，且重污事件集中在 17:00–19:00。", "expected_effect": "缩短重度液体清洁的响应距离。"},
            {"type": "PROACTIVE_PATROL", "priority": "medium", "title": "17:00–19:00 增加 A 栋 1F 东入口巡检", "rationale": "任务历史显示该时段稳定高发；建议在不改变模型阈值的前提下提升现场发现频率。", "expected_effect": "降低污染扩散和人工介入概率。"},
            {"type": "RESOURCE_CONFIGURATION", "priority": "medium", "title": "将 Robot C 的低利用率班次用于室内轻量预巡检", "rationale": "Robot C 利用率最低；仅安排其能力范围内的纸屑 / 纸杯巡检，不替代 Robot B 的湿洗任务。", "expected_effect": "提高闲置时段覆盖，不改变既有 Capability Engine。"},
        ],
        "guardrails": ["不修改 YOLO / VLM confidence threshold", "不修改 Capability Engine、Scheduler 或 Robot-first + Human Fallback", "建议需经人工确认后才可转化为运营配置"],
    }
