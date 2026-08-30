"""Unified technical error projection; business Human Fallback is not an error."""
from event_archive.service import BUSINESS_REVIEW_CODES

ERROR_TYPES = {"MODEL_ERROR", "TOOL_ERROR", "POLICY_REJECTED", "SPATIAL_ERROR", "SCHEDULER_ERROR", "ROUTE_ERROR", "VERIFICATION_ERROR", "EXTERNAL_ADAPTER_ERROR"}


def classify(error):
    if not error:
        return None
    raw = error if isinstance(error, dict) else {"code": str(error)}
    code = str(raw.get("code") or raw.get("error_type") or raw.get("type") or "UNKNOWN_FAILURE")
    if code in BUSINESS_REVIEW_CODES:
        return None
    kind = raw.get("error_type") or raw.get("type")
    if kind not in ERROR_TYPES:
        lowered = code.lower()
        if "model_tool_turn_failed" in lowered or "invalid_model" in lowered:
            kind = "MODEL_ERROR"
        elif any(word in lowered for word in ("calibration", "mapping", "spatial")):
            kind = "SPATIAL_ERROR"
        elif any(word in lowered for word in ("policy", "permission", "forbidden")):
            kind = "POLICY_REJECTED"
        elif "verification" in lowered:
            kind = "VERIFICATION_ERROR"
        elif any(word in lowered for word in ("fetch", "tool", "evidence_unavailable")):
            kind = "TOOL_ERROR"
        elif "scheduler" in lowered:
            kind = "SCHEDULER_ERROR"
        elif "adapter" in lowered:
            kind = "EXTERNAL_ADAPTER_ERROR"
        elif "route" in lowered:
            kind = "ROUTE_ERROR"
        else:
            kind = "MODEL_ERROR"
    # No arbitrary provider text, user input or traceback reaches Advanced.
    messages = {"MODEL_ERROR": "模型请求或结构化输出失败；不会自动切换Replay。", "TOOL_ERROR": "工具调用未完成，自动执行已停止。",
                "POLICY_REJECTED": "代码级策略拒绝该操作。", "SPATIAL_ERROR": "无法产生合法空间位置；不派发机器人。",
                "SCHEDULER_ERROR": "调度执行失败。", "ROUTE_ERROR": "无法生成合法拓扑路线。", "VERIFICATION_ERROR": "验收请求或证据不可用。",
                "EXTERNAL_ADAPTER_ERROR": "外部适配器未授权或请求失败。"}
    # Error codes can contain provider/user text. Expose the taxonomy code only;
    # arbitrary raw diagnostic strings are not an API-safe identifier.
    return {"type": kind, "code": kind, "message": messages[kind]}
