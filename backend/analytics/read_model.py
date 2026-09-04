"""Read-only event/transition analytics. Missing observations remain unknown."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from math import isfinite, ceil
from statistics import mean
from urllib.parse import urlencode

from analytics.history_seed import LOCAL_ZONE
from database.connection import ROBOT_PRESENTATION
from customer_data import customer_events
from event_archive.service import project_event, read_archived_events, utc_time, TIME_SLOTS

ROBOT_LABELS = {key: value["name"] for key, value in ROBOT_PRESENTATION.items() if key != "robot-d"}
ACTIVE_STATES = {"NAVIGATING", "ARRIVED", "CLEANING"}
TYPE_LABELS = {"small_litter": "其他小型垃圾", "liquid": "液体污渍", "large_object": "大件物品", "can": "易拉罐", "unknown": "待研判"}
METRIC_DEFINITIONS = {
    "autonomous_closure_rate": "分子：无人工介入、机器人完成且验收通过的CLOSED；分母：已形成业务处置结论的CLOSED/HUMAN_FALLBACK/HUMAN_REVIEW，排除系统异常与仍在自动处理中。",
    "human_intervention_rate": "分子：有效业务结论中曾进入人工兜底/复核；同一业务处置结论分母，不为凑100%补造结果。",
    "first_pass_success_rate": "分子：第一次主验收通过；分母：保存了第一次验收明确布尔结果的非系统异常事件。独立ROI二审通过不覆盖主验收失败。",
    "average_response_time_minutes": "从首次CLOUD_REVIEW确认到首次NAVIGATING或明确HUMAN_STARTED/HUMAN_WORK_STARTED。人工完成不是开始；缺观察记录排除并公开样本数。",
    "average_closure_time_minutes": "发现DETECTED到CLOSED，仅有效闭环且两个时间均存在的事件。",
    "robot_utilization": "事件时点NAVIGATING/ARRIVED/CLEANING区间取并集并裁剪统计窗口，除以PoC假定连续可用窗口(00–24)。这是分析归一化假设，不是已观测uptime或生产遥测；后续可用实际可用区间替换。FlashBot Max不参与清洁排名。",
}


def first_time(transitions, states):
    return next((stamp for row in transitions if row["state"] in states and (stamp := utc_time(row.get("created_at")))), None)


def minutes(start, end):
    return (end - start).total_seconds() / 60 if start and end and end >= start else None


def first_verification(event, snapshot):
    def primary_value(value):
        if isinstance(value, dict):
            # A same-attempt independent ROI review can close an event, but it
            # is remediation evidence, not a rewrite of the primary verdict.
            first = value.get("first_review")
            if isinstance(first, dict) and type(first.get("verification_pass")) is bool:
                return first["verification_pass"]
            value = value.get("verification_pass")
        return value if type(value) is bool else None

    transitions = event.get("transitions", [])
    saved_verification = snapshot.get("verification") if isinstance(snapshot, dict) else None
    # Persisted new-runtime provenance is authoritative for a single
    # verification attempt even if an older transition projection only carries
    # its final verdict.
    if (sum(item.get("state") == "VERIFYING" for item in transitions) == 1
            and isinstance(saved_verification, dict)
            and isinstance(saved_verification.get("first_review"), dict)):
        return primary_value(saved_verification)
    for index, row in enumerate(transitions):
        if row["state"] != "VERIFYING":
            continue
        for outcome in transitions[index + 1:]:
            if outcome["state"] == "VERIFYING":
                return None
            detail = outcome.get("detail") or {}
            value = primary_value(detail.get("verification"))
            if value is None:
                value = primary_value(detail.get("verification_pass"))
            if value is not None:
                return value
            if outcome["state"] in {"CLOSED", "HUMAN_REVIEW"}:
                value = primary_value(detail.get("verification"))
                if value is not None:
                    return value
                # Final snapshot is first-pass evidence only for one attempt.
                if sum(item["state"] == "VERIFYING" for item in transitions) == 1:
                    return primary_value(snapshot.get("verification"))
                return None
    return None


def record(event, now):
    row = project_event(event, now)
    snapshot = event.get("demo_v1") or event
    transitions = event.get("transitions", [])
    states = {item["state"] for item in transitions}
    error = row["handling_mode"] == "system_error"
    disposition = event["state"] in {"CLOSED", "HUMAN_FALLBACK", "HUMAN_REVIEW"} and not error
    assignment = event.get("assignment_decision") or snapshot.get("assignment_decision") or {}
    multi = snapshot.get("multi_view") or {}
    return {**row, "source": "DEMO_HISTORY" if event.get("source") == "DEMO_HISTORY" else "RUNTIME",
        "timestamp": row["discovered_at"], "zone_id": event.get("zone_id"), **row["location"],
        "robot_id": assignment.get("selected_robot_id"), "severity": (event.get("task_profile") or {}).get("severity"),
        "business_disposition": disposition, "system_error": error,
        "autonomously_closed": row["category"] == "autonomous_closed" and not error,
        "human_intervention": bool(states & {"HUMAN_FALLBACK", "HUMAN_REVIEW"}) and disposition,
        "verification_first_pass": None if error else first_verification(event, snapshot),
        "response_time_minutes": None if error else minutes(first_time(transitions, {"CLOUD_REVIEW"}), first_time(transitions, {"NAVIGATING", "HUMAN_STARTED", "HUMAN_WORK_STARTED"})),
        "closure_time_minutes": None if error or event["state"] != "CLOSED" else minutes(utc_time(row["discovered_at"]), first_time(transitions, {"CLOSED"})),
        "multi_view_triggered": bool(multi.get("audit")), "multi_view_recovered": bool(multi.get("audit")) and event["state"] == "CLOSED",
        "transitions": transitions}


def window(now, since=None, until=None):
    start, end = utc_time(since) if since else now - timedelta(days=30), utc_time(until) if until else now
    if start is None or end is None or start > end or end > now or (end - start).days > 366:
        raise ValueError("Analytics requires valid ISO dates: since <= until <= now, at most 366 days.")
    return start, end


def history(now, start, end, event_type=None, hour=None, raw_events=None, time_slot=None):
    if hour is not None and not 0 <= hour <= 23:
        raise ValueError("Hour must be 0..23 in Asia/Shanghai.")
    if time_slot and time_slot not in TIME_SLOTS:
        raise ValueError("Unknown time slot.")
    rows = []
    for event in customer_events(read_archived_events() if raw_events is None else raw_events):
        row = record(event, now)
        stamp = utc_time(row["timestamp"])
        if not stamp or not start <= stamp <= end:
            continue
        if event_type and row["event_type"] != event_type:
            continue
        if hour is not None and stamp.astimezone(LOCAL_ZONE).hour != hour:
            continue
        if time_slot and not TIME_SLOTS[time_slot][0] <= stamp.astimezone(LOCAL_ZONE).hour < TIME_SLOTS[time_slot][1]:
            continue
        rows.append(row)
    return rows


def percentage(numerator, denominator):
    return round(numerator / denominator * 100, 1) if denominator else None


def calculate_kpis(rows):
    effective = [row for row in rows if row["business_disposition"]]
    verified = [row for row in rows if type(row["verification_first_pass"]) is bool]
    responded = [row["response_time_minutes"] for row in rows if row["response_time_minutes"] is not None]
    closed = [row["closure_time_minutes"] for row in rows if row["closure_time_minutes"] is not None]
    multi = [row for row in rows if row["multi_view_triggered"]]
    denominators = {"autonomous_closure_rate": len(effective), "human_intervention_rate": len(effective),
        "first_pass_success_rate": len(verified), "average_response_time_minutes": len(responded), "average_closure_time_minutes": len(closed)}
    return {"period_days": 30, "total_events": len(rows), "denominators": denominators,
        "excluded": {"system_errors": sum(row["system_error"] for row in rows),
                     "no_business_disposition": sum(not row["business_disposition"] and not row["system_error"] for row in rows)},
        "autonomous_closure_rate": percentage(sum(row["autonomously_closed"] for row in effective), len(effective)),
        "human_intervention_rate": percentage(sum(row["human_intervention"] for row in effective), len(effective)),
        "first_pass_success_rate": percentage(sum(row["verification_first_pass"] for row in verified), len(verified)),
        "average_response_time_minutes": round(mean(responded), 2) if responded else None,
        "average_closure_time_minutes": round(mean(closed), 2) if closed else None,
        "multi_view_recovery_rate": percentage(sum(row["multi_view_recovered"] for row in multi), len(multi))}


def spatial_points(rows, start, end, hour=None, time_slot=None):
    grouped = defaultdict(list)
    for row in rows:
        x, y = row.get("x"), row.get("y")
        if not row.get("map_id") or not all(type(value) in {int, float} and isfinite(value) for value in (x, y)):
            continue
        # Pre-locate template coordinates are not observed SLAM coordinates.
        if row["source"] != "DEMO_HISTORY" and not any(item["state"] == "LOCATED" for item in row["transitions"]):
            continue
        grouped[(row["map_id"], x, y, row["event_type"])].append(row)
    result = []
    for (map_id, x, y, event_type), records in grouped.items():
        sample = records[0]
        query = {"map_id": map_id, "event_type": event_type, "since": start.isoformat(), "until": end.isoformat(), "x": x, "y": y}
        if hour is not None:
            query["hour"] = hour
        if time_slot:
            query["time_slot"] = time_slot
        closed = [row["closure_time_minutes"] for row in records if row["closure_time_minutes"] is not None]
        result.append({"zone_id": sample.get("zone_id") or f"{map_id}:{x}:{y}:{event_type}", "label": sample.get("zone") or map_id,
            "map_id": map_id, "building": sample.get("building"), "floor": sample.get("floor"), "x": x, "y": y,
            "event_type": event_type, "count": len(records), "high_severity_count": sum(row["severity"] == "high" for row in records),
            "time_slot": time_slot or "all", "average_closure_time_minutes": round(mean(closed), 2) if closed else None,
            "drilldown_url": "/events?" + urlencode(query)})
    return sorted(result, key=lambda point: point["count"], reverse=True)


def union_seconds(intervals):
    total, previous_start, previous_end = 0.0, None, None
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if previous_end is not None and start <= previous_end:
            previous_end = max(previous_end, end)
        else:
            if previous_end is not None:
                total += (previous_end - previous_start).total_seconds()
            previous_start, previous_end = start, end
    return total + ((previous_end - previous_start).total_seconds() if previous_end is not None else 0)


def availability(start, end):
    # There is no observed roster/uptime provider yet. Declare the PoC
    # normalization assumption instead of inventing daytime shifts which
    # exclude the seed's observed evening task activity.
    return [(start, end)] if end > start else []


def utilization(rows, start, end):
    available = availability(start, end)
    available_seconds = union_seconds(available)
    result = []
    for robot_id, name in ROBOT_LABELS.items():
        tasks = [row for row in rows if row["robot_id"] == robot_id]
        intervals = []
        carried_tasks = 0
        for row in tasks:
            transitions = row["transitions"]
            row_active = False
            for index, transition in enumerate(transitions):
                if transition["state"] not in ACTIVE_STATES:
                    continue
                left = utc_time(transition.get("created_at"))
                right = utc_time(transitions[index + 1].get("created_at")) if index + 1 < len(transitions) else end
                if not left or not right:
                    continue
                for shift_start, shift_end in available:
                    a, b = max(left, shift_start), min(right, shift_end)
                    if b > a:
                        intervals.append((a, b))
                        row_active = True
            carried_tasks += bool(row_active and utc_time(row["timestamp"]) < start)
        active_seconds = union_seconds(intervals)
        result.append({"robot_id": robot_id, "robot_name": name, "tasks": sum(start <= utc_time(row["timestamp"]) <= end for row in tasks),
            "carried_tasks": carried_tasks,
            "active_minutes": round(active_seconds / 60, 2), "available_minutes": round(available_seconds / 60, 2),
            "utilization": percentage(active_seconds, available_seconds), "availability_policy": "POC ASSUMED CONTINUOUS AVAILABILITY 00:00–24:00; NOT OBSERVED UPTIME"})
    return sorted(result, key=lambda row: row["utilization"] or 0, reverse=True)


def prediction_plan():
    return {
        "source": "FIXED_DEMO_SCENARIO",
        "disclaimer": "固定演示预案：基于过去 30 天热点与端侧 RGB-D 占用趋势样例；非实时天气、实机遥测或自动派单。",
        "prepositioning": [
            {"signal": "华南初秋落叶窗口", "risk": "外围道路落叶与果实污染", "time": "05:40 前", "robot_id": "robot-a", "robot_name": "赛特净界 S5", "location": "园区东侧道路", "action": "前置吸扫，轮组避压"},
            {"signal": "强降雨风险", "risk": "入口与主大堂积水", "time": "降雨前", "robot_id": "robot-b", "robot_name": "高仙 Omnie", "location": "A栋1F入口及主大堂", "action": "强吸水 + 高压拖洗"},
            {"signal": "高峰通行预测", "risk": "入口响应距离增加", "time": "高峰前", "robot_id": "robot-b", "robot_name": "高仙 Omnie", "location": "A栋1F入口", "action": "待命并保持通行区"},
        ],
        "cleaning_playbooks": [
            {"object": "易拉罐", "action": "先强吸回收", "guardrail": "不切换拖地"},
            {"object": "未压碎榕树果实", "action": "前置吸扫，轮组避压", "guardrail": "避免压碎污染"},
            {"object": "已污染残留", "action": "刷洗 + 高压拖洗", "guardrail": "加强去污"},
        ],
    }


def analytics_overview(*, event_type=None, since=None, until=None, hour=None, now=None, time_slot=None):
    now = now or datetime.now(timezone.utc)
    start, end = window(now, since, until)
    raw_events = customer_events(read_archived_events())
    rows = history(now, start, end, event_type, hour, raw_events, time_slot)
    carried = history(now, datetime.min.replace(tzinfo=timezone.utc), end, event_type, hour, raw_events, time_slot)
    metrics = calculate_kpis(rows)
    period_days = ceil((end - start).total_seconds() / 86400)
    metrics["period_days"] = period_days
    hours = Counter(utc_time(row["timestamp"]).astimezone(LOCAL_ZONE).hour for row in rows)
    structure = Counter(row["event_type"] for row in rows)
    points = spatial_points(rows, start, end, hour, time_slot)
    return {"source": "DEMO_HISTORY + RUNTIME", "period": {"days": period_days, "start": start.isoformat(), "end": end.isoformat(), "ending": end.date().isoformat()},
        "kpis": metrics, "denominators": metrics["denominators"], "metric_definitions": METRIC_DEFINITIONS,
        "source_counts": {source: sum(row["source"] == source for row in rows) for source in ("DEMO_HISTORY", "RUNTIME")},
        "heatmap": points, "unlocated_events": len(rows) - sum(point["count"] for point in points),
        "time_distribution": [{"hour": hour, "label": f"{hour:02d}:00", "count": hours[hour]} for hour in range(24)],
        "event_structure": [{"event_type": key, "label": TYPE_LABELS.get(key, "待研判"), "count": count} for key, count in structure.items()],
        "robot_utilization": utilization(carried, start, end), "top_hotspots": points[:3], "prediction_plan": prediction_plan()}
