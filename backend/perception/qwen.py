"""Minimal DashScope OpenAI-compatible Qwen-VL client with strict JSON parsing."""

from __future__ import annotations

import base64
import json
import os
from time import perf_counter
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from perception.models import normalize_task_profile
from perception.yolo import RealInferenceError

PROMPT = """You are a cleaning perception verifier. Return JSON only, with this schema:
{"need_clean": boolean, "confidence": number, "summary": string,
 "business_class": "liquid|can|leaf|large_object|small_litter|unknown", "business_confidence": number,
 "task_profile": {"object_type": string, "pollution_form": string, "severity": string,
 "estimated_area": number, "surface": string, "required_capabilities": [string],
 "priority": string, "crowd_level": string}}
Use conservative values. Do not include markdown."""


def _image_data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower().lstrip(".") or "jpeg"
    mime = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix}"
    return f"data:{mime};base64,{base64.b64encode(image_path.read_bytes()).decode('ascii')}"


def _request_qwen(content: list[dict[str, Any]], model: str) -> tuple[dict[str, Any], int]:
    """Shared DashScope transport for every Qwen-VL entry point.

    Callers own their schema prompts; this module owns the only HTTP client so
    the project cannot accidentally grow parallel SDK layers or leak a key.
    """
    key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not key:
        raise RealInferenceError("DASHSCOPE_API_KEY is not configured.")
    endpoint = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
    payload = {"model": model, "messages": [{"role": "user", "content": content}], "temperature": 0.1}
    request = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    started = perf_counter()
    try:
        with urlopen(request, timeout=45) as response:  # nosec B310: endpoint is explicit local configuration
            body = json.loads(response.read().decode("utf-8"))
        content_text = body["choices"][0]["message"]["content"]
    except (HTTPError, URLError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise RealInferenceError(f"Qwen-VL request failed: {error}") from error
    return _parse_json(content_text), round((perf_counter() - started) * 1000)


def _parse_json(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise RealInferenceError("Qwen-VL did not return valid JSON.") from error
    if not isinstance(value, dict):
        raise RealInferenceError("Qwen-VL JSON response is not an object.")
    return value


def run_qwen_vl(image_path: Path, model: str) -> dict:
    parsed, _ = _request_qwen([{"type": "text", "text": PROMPT}, {"type": "image_url", "image_url": {"url": _image_data_url(image_path)}}], model)
    confidence = parsed.get("confidence", 0)
    need_clean = parsed.get("need_clean", parsed.get("needs_cleaning", False))
    return {"need_clean": bool(need_clean), "confidence": round(float(confidence), 4) if isinstance(confidence, (int, float)) else 0.0, "summary": str(parsed.get("summary", ""))[:500], "business_class": str(parsed.get("business_class", "unknown")).strip().lower(), "business_confidence": parsed.get("business_confidence", confidence), "raw": parsed, "task_profile": normalize_task_profile(parsed.get("task_profile"))}


EVENT_PROMPT = """You are a cautious cleaning-event semantic reviewer. Review the supplied camera image(s), controlled edge detection evidence, and camera context. Return JSON only:
{"need_clean": boolean, "event_type": "small_litter|liquid|can|large_object|unknown", "decision_confidence": number, "severity": "low|medium|high", "surface_type": string, "interference_factors": [string], "evidence_summary": string, "recommended_capabilities": [string], "next_action": "dispatch_robot|human_review|ignore"}
Do not choose a robot. Do not invent evidence. Keep evidence_summary in concise Chinese (40-80 Chinese characters)."""

TARGETED_REVIEW_PROMPT = """You are an independent second cleaning-event reviewer. This is a fresh review: do not assume, repeat, or receive any first-review conclusion. Review the supplied camera images and the limited factual context only. For the liquid-spill case, the three images are from the same place and time but different fixed cameras; each single image can be ambiguous. Compare spatial alignment, shape continuity, surface reflection and camera consistency before deciding. Return JSON only:
{"need_clean": boolean, "event_type": "small_litter|liquid|can|large_object|unknown", "decision_confidence": number, "severity": "low|medium|high", "surface_type": string, "interference_factors": [string], "evidence_summary": string, "recommended_capabilities": [string], "next_action": "dispatch_robot|human_review|ignore"}
Do not choose a robot. Do not invent evidence. Keep evidence_summary in concise Chinese (40-80 Chinese characters)."""

VERIFICATION_PROMPT = """You are a cautious cleaning verification reviewer. The first image is before cleaning and the second is after cleaning. Return JSON only:
{"issue_remaining": boolean, "verification_pass": boolean, "confidence": number, "evidence_summary": string, "next_action": "close|retry|human_review"}
Use concise Chinese evidence_summary. Do not invent a pass when the result is unclear."""


def run_event_qwen_vl(images: list[Path], yolo_evidence: list[dict[str, Any]], cameras: list[dict[str, Any]], model: str) -> dict[str, Any]:
    """One real multi-image semantic call; the answer is never averaged client-side."""
    context = {"yolo_evidence": yolo_evidence, "cameras": cameras}
    content: list[dict[str, Any]] = [{"type": "text", "text": f"{EVENT_PROMPT}\nContext JSON: {json.dumps(context, ensure_ascii=False)}"}]
    content.extend({"type": "image_url", "image_url": {"url": _image_data_url(path)}} for path in images)
    parsed, elapsed_ms = _request_qwen(content, model)
    confidence = parsed.get("decision_confidence", parsed.get("confidence", 0))
    return {
        "provider": "DashScope Qwen-VL", "model": model, "image_count": len(images), "elapsed_ms": elapsed_ms,
        "need_clean": bool(parsed.get("need_clean", False)), "event_type": str(parsed.get("event_type", "unknown")).lower(),
        "decision_confidence": round(float(confidence), 4) if isinstance(confidence, (int, float)) else 0.0,
        "severity": str(parsed.get("severity", "medium")).lower(), "surface_type": str(parsed.get("surface_type", ""))[:80],
        "interference_factors": [str(item)[:100] for item in parsed.get("interference_factors", []) if isinstance(item, str)][:6],
        "evidence_summary": str(parsed.get("evidence_summary", ""))[:500],
        "recommended_capabilities": [str(item)[:80] for item in parsed.get("recommended_capabilities", []) if isinstance(item, str)][:8],
        "next_action": str(parsed.get("next_action", "human_review")).lower(), "raw": parsed,
    }


def run_targeted_event_qwen_vl(images: list[Path], yolo_evidence: list[dict[str, Any]], cameras: list[dict[str, Any]], model: str) -> dict[str, Any]:
    """Run an independent grey-zone review through the same transport and schema.

    It deliberately receives no first-review response, preventing a prompt-chain
    from laundering the initial conclusion into a supposed second opinion.
    """
    context = {"yolo_evidence": yolo_evidence, "cameras": cameras}
    content: list[dict[str, Any]] = [{"type": "text", "text": f"{TARGETED_REVIEW_PROMPT}\nContext JSON: {json.dumps(context, ensure_ascii=False)}"}]
    content.extend({"type": "image_url", "image_url": {"url": _image_data_url(path)}} for path in images)
    parsed, elapsed_ms = _request_qwen(content, model)
    confidence = parsed.get("decision_confidence", parsed.get("confidence", 0))
    return {
        "provider": "DashScope Qwen-VL", "model": model, "image_count": len(images), "elapsed_ms": elapsed_ms,
        "need_clean": bool(parsed.get("need_clean", False)), "event_type": str(parsed.get("event_type", "unknown")).lower(),
        "decision_confidence": round(float(confidence), 4) if isinstance(confidence, (int, float)) else 0.0,
        "severity": str(parsed.get("severity", "medium")).lower(), "surface_type": str(parsed.get("surface_type", ""))[:80],
        "interference_factors": [str(item)[:100] for item in parsed.get("interference_factors", []) if isinstance(item, str)][:6],
        "evidence_summary": str(parsed.get("evidence_summary", ""))[:500],
        "recommended_capabilities": [str(item)[:80] for item in parsed.get("recommended_capabilities", []) if isinstance(item, str)][:8],
        "next_action": str(parsed.get("next_action", "human_review")).lower(), "raw": parsed,
    }


def run_verification_qwen_vl(before: Path, after: Path, context: dict[str, Any], model: str) -> dict[str, Any]:
    content = [{"type": "text", "text": f"{VERIFICATION_PROMPT}\nContext JSON: {json.dumps(context, ensure_ascii=False)}"}, {"type": "image_url", "image_url": {"url": _image_data_url(before)}}, {"type": "image_url", "image_url": {"url": _image_data_url(after)}}]
    parsed, elapsed_ms = _request_qwen(content, model)
    confidence = parsed.get("confidence", 0)
    return {"provider": "DashScope Qwen-VL", "model": model, "elapsed_ms": elapsed_ms, "issue_remaining": bool(parsed.get("issue_remaining", False)), "verification_pass": bool(parsed.get("verification_pass", False)), "confidence": round(float(confidence), 4) if isinstance(confidence, (int, float)) else 0.0, "evidence_summary": str(parsed.get("evidence_summary", ""))[:500], "next_action": str(parsed.get("next_action", "human_review")).lower(), "raw": parsed}
