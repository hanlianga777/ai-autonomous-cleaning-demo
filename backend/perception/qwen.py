"""Minimal DashScope OpenAI-compatible Qwen-VL client with strict JSON parsing."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
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
    key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not key:
        raise RealInferenceError("DASHSCOPE_API_KEY is not configured.")
    endpoint = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
    payload = {"model": model, "messages": [{"role": "user", "content": [{"type": "text", "text": PROMPT}, {"type": "image_url", "image_url": {"url": _image_data_url(image_path)}}]}], "temperature": 0.1}
    request = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=45) as response:  # nosec B310: endpoint is explicit local configuration
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
    except (HTTPError, URLError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise RealInferenceError(f"Qwen-VL request failed: {error}") from error
    parsed = _parse_json(content)
    confidence = parsed.get("confidence", 0)
    need_clean = parsed.get("need_clean", parsed.get("needs_cleaning", False))
    return {"need_clean": bool(need_clean), "confidence": round(float(confidence), 4) if isinstance(confidence, (int, float)) else 0.0, "summary": str(parsed.get("summary", ""))[:500], "business_class": str(parsed.get("business_class", "unknown")).strip().lower(), "business_confidence": parsed.get("business_confidence", confidence), "raw": parsed, "task_profile": normalize_task_profile(parsed.get("task_profile"))}
