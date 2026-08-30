"""Bounded, model-directed multi-view evidence acquisition for P1-C.

This module deliberately owns no camera, SLAM, scheduling, robot or HTTP
transport.  It gives a configured Cloud VLM only three read-only tools and
enforces the documented evidence budget around the model's choices.
"""

from __future__ import annotations

import base64
from copy import deepcopy
import json
from datetime import datetime, timezone
from time import perf_counter
from pathlib import Path
from typing import Any, Callable, Iterable

from perception import qwen
from perception.multiview.tools import _contains
from spatial.spatial_data import CAMERAS
from observability.context import CURRENT_TRACE


MAX_ADDITIONAL_CAMERAS = 2
MAX_ACQUISITION_ROUNDS = 2
MAX_MODEL_TURNS = 6
RECOVERABLE_AMBIGUITIES = {
    "reflection",
    "occlusion",
    "perspective",
    "lens_contamination",
    "insufficient_view",
}

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_supporting_cameras",
            "description": "Find legal fixed cameras whose Phase 2 coverage polygon contains the current SLAM location.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_camera_evidence",
            "description": "Fetch one evidence asset from a camera previously returned by find_supporting_cameras.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": ["camera_id"],
                "properties": {"camera_id": {"type": "string", "minLength": 1}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish_visual_judgment",
            "description": "Finish only after the available evidence is sufficient. Return the structured visual judgment; never select a robot or person.",
            "parameters": qwen.VISUAL_JUDGMENT_SCHEMA,
        },
    },
]

_SYSTEM_PROMPT = """You are the Multi-view Perception Agent for a cleaning event.
You may only call the three supplied read-only evidence tools. Decide whether extra
fixed-camera evidence is needed. Do not choose a robot, human operator, route, or
confidence policy. Supporting evidence is controlled PoC evidence, not synchronized
RTSP. Call finish_visual_judgment only with strict JSON after evaluating the evidence.
Do not reveal chain-of-thought; provide only the structured final judgment.
""" + qwen.SEMANTIC_RULES


def _safe_text(value: Any, limit: int = 300) -> str:
    return str(value).replace("\n", " ")[:limit]


def acquisition_contract() -> dict[str, Any]:
    """Hash-only replay compatibility contract; never an API/UI projection."""
    return deepcopy({"system_prompt": _SYSTEM_PROMPT, "tools": _TOOLS,
                     "max_cameras": MAX_ADDITIONAL_CAMERAS, "max_rounds": MAX_ACQUISITION_ROUNDS,
                     "max_model_turns": MAX_MODEL_TURNS, "max_tool_calls_per_turn": 2})


def _normalise_ambiguity(value: Any) -> str:
    return _safe_text(value, 80).strip().lower().replace("-", "_").replace(" ", "_")


def _need_action(review: dict[str, Any]) -> bool:
    value = review.get("need_action", review.get("need_clean", False))
    return value if type(value) is bool else False


def _evidence_sufficient(review: dict[str, Any]) -> bool:
    return review.get("evidence_sufficient") is True


def _audit_entry(
    audit: list[dict[str, Any]],
    entry: dict[str, Any],
    callback: Callable[[dict[str, Any]], None] | None,
) -> None:
    # The audit is deliberately restricted to tool facts: no prompt, model
    # content, local paths, data URLs, secrets or model reasoning are retained.
    safe = {key: value for key, value in entry.items() if key not in {"content", "messages", "image", "path", "raw", "_tool_started"}}
    if "_tool_started" in entry:
        safe["tool_duration_ms"] = round((perf_counter() - entry["_tool_started"]) * 1000)
    safe["timestamp"] = datetime.now(timezone.utc).isoformat()
    audit.append(safe)
    if callback:
        try:
            callback(dict(safe))
        except Exception:
            # Audit persistence must not turn an evidence acquisition failure
            # into an uncaught provider/runtime exception.
            pass


def _image_data_url(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "jpeg"
    mime = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix}"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _allowed_assets(supporting_assets: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Expose only manifest-declared supplemental evidence to the Agent."""
    allowed: dict[str, dict[str, Any]] = {}
    for asset in supporting_assets:
        camera_id = asset.get("camera_id") if isinstance(asset, dict) else None
        if isinstance(camera_id, str) and asset.get("role") == "evidence":
            allowed[camera_id] = asset
    return allowed


def find_supporting_cameras(
    *, location: dict[str, Any], primary_camera_id: str, allowed_assets: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Read the existing Phase 2 Camera Coverage geometry; do not rank fixtures."""
    try:
        target = {"x": float(location["x"]), "y": float(location["y"])}
        map_id = str(location["map_id"])
    except (KeyError, TypeError, ValueError):
        return []
    candidates: list[dict[str, Any]] = []
    for camera in CAMERAS:
        camera_id = camera["camera_id"]
        if camera_id == primary_camera_id or camera_id not in allowed_assets or camera["map_id"] != map_id:
            continue
        if _contains(target, camera["coverage_polygon"]):
            candidates.append({
                "camera_id": camera_id,
                "name": camera["name"],
                "map_id": camera["map_id"],
                "zone": camera["zone"],
                "selection_basis": "phase2_coverage_polygon_contains_slam_target",
                "evidence_source": "CONTROLLED_EVIDENCE",
            })
    return candidates


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls = message.get("tool_calls") if isinstance(message, dict) else None
    return calls if isinstance(calls, list) else []


def _call_function(call: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    if not isinstance(call, dict):
        return "", "", None
    function = call.get("function") if isinstance(call.get("function"), dict) else {}
    name = function.get("name")
    arguments = function.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = None
    return str(name or ""), str(call.get("id") or ""), arguments if isinstance(arguments, dict) else None


def _assistant_json(message: dict[str, Any]) -> dict[str, Any] | None:
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, list):
        content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
    if not isinstance(content, str) or not content.strip():
        return None
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _final_decision(review: dict[str, Any]) -> str:
    # A gray result is provisional: the composition layer must run independent
    # review before it can expose a final CONFIRM/REJECT to consumers.
    if not _evidence_sufficient(review) or review.get("confidence", review.get("decision_confidence", 0)) < 0.85:
        return "HUMAN_REVIEW"
    return "CONFIRM" if _need_action(review) else "REJECT"


def _acquired_evidence_verdict(review: dict[str, Any], evidence: list[dict[str, Any]]) -> tuple[str, str | None]:
    """An initial insufficiency cannot become autonomous without new legal evidence."""
    if not _evidence_sufficient(review):
        return "HUMAN_REVIEW", "final_evidence_insufficient"
    if not evidence:
        return "HUMAN_REVIEW", "no_evidence_acquired"
    return _final_decision(review), None


def _valid_finish_arguments(arguments: dict[str, Any]) -> bool:
    schema = qwen.VISUAL_JUDGMENT_SCHEMA
    return set(arguments).issubset(schema["properties"]) and set(schema["required"]).issubset(arguments)


def _result(
    *, review: dict[str, Any], selected: list[str], evidence: list[dict[str, Any]], audit: list[dict[str, Any]],
    decision: str, error: str | None, iterations: int, model_turns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "review": review,
        "selected_cameras": selected,
        "evidence_assets": evidence,
        "audit": audit,
        "decision": decision,
        "error": error,
        "iteration_count": iterations,
        "model_turns": model_turns or [],
    }


def _safe_model_message(message: dict[str, Any]) -> dict[str, Any]:
    """Persist a replayable provider response without prompts, images or CoT."""
    safe: dict[str, Any] = {"role": str(message.get("role", "assistant"))}
    calls = []
    for call in _tool_calls(message):
        name, call_id, arguments = _call_function(call)
        safe_arguments: dict[str, Any] | None
        if name == "fetch_camera_evidence" and isinstance(arguments, dict) and set(arguments) == {"camera_id"}:
            safe_arguments = {"camera_id": _safe_text(arguments.get("camera_id"), 100)}
        elif name == "finish_visual_judgment" and isinstance(arguments, dict) and _valid_finish_arguments(arguments):
            # Keep only the public visual schema; no arbitrary provider fields
            # (including accidental secrets) enter a replay record.
            safe_arguments = {key: arguments[key] for key in qwen.VISUAL_JUDGMENT_SCHEMA["properties"] if key in arguments}
        elif name == "find_supporting_cameras" and arguments == {}:
            safe_arguments = {}
        else:
            safe_arguments = None
        # Preserve the OpenAI-compatible assistant shape so a replay feeder can
        # return this record verbatim to ``request_turn`` without rebuilding a
        # hidden answer or changing the Agent's tool-policy path.
        calls.append({
            "id": call_id or "missing",
            "type": "function",
            "function": {"name": name or "unknown", "arguments": json.dumps(safe_arguments, ensure_ascii=False)},
        })
    if calls:
        safe["tool_calls"] = calls
    else:
        parsed = _assistant_json(message)
        # Final JSON is structured output, not model reasoning. A non-JSON
        # content reply is intentionally not persisted or replayable.
        safe["content"] = (json.dumps({key: parsed[key] for key in qwen.VISUAL_JUDGMENT_SCHEMA["properties"] if key in parsed}, ensure_ascii=False) if parsed is not None else None)
    return safe


def run_autonomous_acquisition(
    *,
    initial_review: dict[str, Any],
    primary_asset: dict[str, Any],
    primary_path: Path,
    location: dict[str, Any],
    supporting_assets: Iterable[dict[str, Any]],
    model: str,
    resolve_asset: Callable[[dict[str, Any]], Path],
    on_audit: Callable[[dict[str, Any]], None] | None = None,
    request_turn: Callable[[list[dict[str, Any]], list[dict[str, Any]], str], tuple[dict[str, Any], int]] | None = None,
    response_source: str = "LIVE_MODEL",
    primary_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Acquire only model-selected legal evidence, then return a bounded verdict.

    `request_qwen_tool_turn` is provided by ``perception.qwen`` and owns the
    actual provider transport. It is intentionally invoked with the supplied
    tool definitions only; this function has no HTTP fallback.
    """
    review = dict(initial_review) if isinstance(initial_review, dict) else {}
    audit: list[dict[str, Any]] = []
    model_turns: list[dict[str, Any]] = []
    if response_source not in {"LIVE_MODEL", "REPLAY"}:
        return _result(review=review, selected=[], evidence=[], audit=audit, decision="HUMAN_REVIEW", error="invalid_response_source", iterations=0, model_turns=model_turns)
    primary_camera_id = primary_asset.get("camera_id") if isinstance(primary_asset, dict) else None
    if not isinstance(primary_camera_id, str) or not primary_camera_id:
        return _result(review=review, selected=[], evidence=[], audit=audit, decision="HUMAN_REVIEW", error="invalid_primary_asset", iterations=0, model_turns=model_turns)

    ambiguity = _normalise_ambiguity(review.get("ambiguity_type"))
    if _evidence_sufficient(review):
        _audit_entry(audit, {"source": "AGENT_RUNTIME", "name": "evidence_gate", "status": "NOT_TRIGGERED", "reason": "EVIDENCE_ALREADY_SUFFICIENT"}, on_audit)
        return _result(review=review, selected=[], evidence=[], audit=audit, decision=_final_decision(review), error=None, iterations=0, model_turns=model_turns)
    if ambiguity not in RECOVERABLE_AMBIGUITIES:
        _audit_entry(audit, {"source": "AGENT_RUNTIME", "name": "evidence_gate", "status": "HUMAN_REVIEW", "reason": "unrecoverable_ambiguity"}, on_audit)
        return _result(review=review, selected=[], evidence=[], audit=audit, decision="HUMAN_REVIEW", error="unrecoverable_ambiguity", iterations=0, model_turns=model_turns)

    allowed_assets = _allowed_assets(supporting_assets)
    available = find_supporting_cameras(location=location, primary_camera_id=primary_camera_id, allowed_assets=allowed_assets)
    if not available:
        _audit_entry(audit, {"source": "AGENT_RUNTIME", "name": "evidence_gate", "status": "HUMAN_REVIEW", "reason": "no_legal_supporting_camera"}, on_audit)
        return _result(review=review, selected=[], evidence=[], audit=audit, decision="HUMAN_REVIEW", error="no_legal_supporting_camera", iterations=0, model_turns=model_turns)

    try:
        primary_image = _image_data_url(Path(primary_path))
    except (OSError, ValueError):
        return _result(review=review, selected=[], evidence=[], audit=audit, decision="HUMAN_REVIEW", error="primary_asset_unavailable", iterations=0, model_turns=model_turns)

    # The candidate list is not inserted into the model context: the model must
    # call the coverage tool itself to receive it, rather than being handed a
    # preselected multi-camera bundle.
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "text", "text": json.dumps({
                "primary_camera_id": primary_camera_id,
                "camera_context": primary_context or {},
                "slam_location": {key: location.get(key) for key in ("map_id", "building", "floor", "zone", "x", "y")},
                "initial_evidence_sufficient": False,
                "ambiguity_type": ambiguity,
                "instruction": "The primary image is supplied below. Use tools only if additional evidence is necessary.",
            }, ensure_ascii=False)},
            {"type": "image_url", "image_url": {"url": primary_image}},
        ]},
    ]
    selected: list[str] = []
    evidence: list[dict[str, Any]] = []
    permitted_candidates: set[str] = set()
    rounds = 0
    turns = 0

    request_turn = request_turn or getattr(qwen, "request_qwen_tool_turn", None)
    parse_judgment = getattr(qwen, "parse_visual_judgment", None)
    if not callable(request_turn) or not callable(parse_judgment):
        return _result(review=review, selected=[], evidence=[], audit=audit, decision="HUMAN_REVIEW", error="qwen_tool_calling_unavailable", iterations=0, model_turns=model_turns)

    _audit_entry(audit, {"source": "AGENT_RUNTIME", "name": "agent_start", "status": "STARTED", "model": model, "model_source": response_source}, on_audit)

    while turns < MAX_MODEL_TURNS:
        turns += 1
        try:
            assistant_message, elapsed_ms = request_turn(messages=messages, tools=_TOOLS, model=model)
        except Exception as error:  # provider errors must not become a mock response
            return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error=f"model_tool_turn_failed:{type(error).__name__}", iterations=rounds, model_turns=model_turns)
        if not isinstance(assistant_message, dict):
            return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error="invalid_model_tool_message", iterations=rounds, model_turns=model_turns)
        supplied_calls = assistant_message.get("tool_calls")
        if supplied_calls is not None and (
            not isinstance(supplied_calls, list) or not 1 <= len(supplied_calls) <= 2
            or any(not isinstance(call, dict) or call.get("type") != "function"
                   or not isinstance(call.get("id"), str) or not call["id"]
                   or not isinstance(call.get("function"), dict) for call in supplied_calls)
            or len({call["id"] for call in supplied_calls}) != len(supplied_calls)
        ):
            return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error="invalid_model_tool_calls", iterations=rounds, model_turns=model_turns)
        safe_turn = _safe_model_message(assistant_message)
        safe_turn["turn"] = turns
        safe_turn["elapsed_ms"] = elapsed_ms if response_source == "LIVE_MODEL" else None
        safe_turn["historical_elapsed_ms"] = elapsed_ms if response_source == "REPLAY" else None
        safe_turn["source"] = response_source
        model_turns.append(safe_turn)

        calls = _tool_calls(assistant_message)
        if not calls:
            parsed = _assistant_json(assistant_message)
            if parsed is None:
                return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error="model_did_not_finish_with_json", iterations=rounds, model_turns=model_turns)
            try:
                review = parse_judgment(parsed=parsed, model=model, image_count=1 + len(evidence), elapsed_ms=elapsed_ms)
            except Exception as error:
                return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error=f"final_judgment_invalid:{type(error).__name__}", iterations=rounds, model_turns=model_turns)
            decision, error = _acquired_evidence_verdict(review, evidence)
            return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision=decision, error=error, iterations=rounds, model_turns=model_turns)

        messages.append(assistant_message)
        round_fetches = 0
        tool_messages: list[dict[str, Any]] = []
        new_images: list[dict[str, Any]] = []
        for call in calls:
            name, call_id, arguments = _call_function(call)
            safe_args = {"camera_id": arguments.get("camera_id")} if isinstance(arguments, dict) and "camera_id" in arguments else {}
            base_audit = {
                "_tool_started": perf_counter(), "started_at": datetime.now(timezone.utc).isoformat(),
                "trace_id": CURRENT_TRACE.get(),
                "source": "MODEL_TOOL_CALL", "model_source": response_source,
                "tool_call_id": call_id or "missing", "name": name or "unknown", "arguments": safe_args,
                "elapsed_ms": elapsed_ms if response_source == "LIVE_MODEL" else None,
                "historical_elapsed_ms": elapsed_ms if response_source == "REPLAY" else None,
            }
            if name == "find_supporting_cameras":
                if arguments != {}:
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "invalid_schema"}, on_audit)
                    tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": "invalid_schema"})})
                    continue
                candidates = find_supporting_cameras(location=location, primary_camera_id=primary_camera_id, allowed_assets=allowed_assets)
                permitted_candidates = {item["camera_id"] for item in candidates}
                _audit_entry(audit, {**base_audit, "status": "OK", "candidate_count": len(candidates), "candidates": candidates}, on_audit)
                tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"candidates": candidates}, ensure_ascii=False)})
                continue
            if name == "fetch_camera_evidence":
                camera_id = arguments.get("camera_id") if isinstance(arguments, dict) else None
                if rounds >= MAX_ACQUISITION_ROUNDS:
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "acquisition_round_limit"}, on_audit)
                    tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": "acquisition_round_limit"})})
                    continue
                if not isinstance(camera_id, str) or set(arguments) != {"camera_id"}:
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "invalid_schema"}, on_audit)
                    tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": "invalid_schema"})})
                    continue
                if camera_id not in permitted_candidates or camera_id not in allowed_assets:
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "unauthorised_camera"}, on_audit)
                    tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": "unauthorised_camera"})})
                    continue
                if camera_id in selected:
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "duplicate_camera"}, on_audit)
                    tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": "duplicate_camera"})})
                    continue
                if len(selected) >= MAX_ADDITIONAL_CAMERAS:
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "camera_limit"}, on_audit)
                    tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": "camera_limit"})})
                    continue
                try:
                    path = Path(resolve_asset(allowed_assets[camera_id]))
                    image = _image_data_url(path)
                except (OSError, TypeError, ValueError):
                    _audit_entry(audit, {**base_audit, "status": "FAILED", "reason": "evidence_fetch_failed"}, on_audit)
                    return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error="evidence_fetch_failed", iterations=rounds, model_turns=model_turns)
                selected.append(camera_id)
                round_fetches += 1
                asset = allowed_assets[camera_id]
                safe_asset = {key: asset[key] for key in ("camera_id", "event_id", "filename", "role", "source") if key in asset}
                evidence.append(safe_asset)
                _audit_entry(audit, {**base_audit, "status": "OK", "evidence_source": "CONTROLLED_EVIDENCE"}, on_audit)
                tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"camera_id": camera_id, "available": True, "evidence_source": "CONTROLLED_EVIDENCE"})})
                new_images.extend([
                    {"type": "text", "text": f"Evidence camera: {camera_id} (controlled evidence asset)."},
                    {"type": "image_url", "image_url": {"url": image}},
                ])
                continue
            if name == "finish_visual_judgment":
                if calls != [call] or round_fetches:
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "finish_must_follow_evidence_turn"}, on_audit)
                    tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": "finish_must_follow_evidence_turn"})})
                    continue
                if not isinstance(arguments, dict) or not _valid_finish_arguments(arguments):
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "invalid_schema"}, on_audit)
                    return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error="final_schema_invalid", iterations=rounds, model_turns=model_turns)
                try:
                    review = parse_judgment(parsed=arguments, model=model, image_count=1 + len(evidence), elapsed_ms=elapsed_ms)
                except Exception as error:
                    _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "invalid_final_judgment"}, on_audit)
                    return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error=f"final_judgment_invalid:{type(error).__name__}", iterations=rounds, model_turns=model_turns)
                _audit_entry(audit, {**base_audit, "status": "OK"}, on_audit)
                decision, error = _acquired_evidence_verdict(review, evidence)
                return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision=decision, error=error, iterations=rounds, model_turns=model_turns)
            _audit_entry(audit, {**base_audit, "status": "REJECTED", "reason": "unauthorised_tool"}, on_audit)
            tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": "unauthorised_tool"})})

        if round_fetches:
            rounds += 1
        messages.extend(tool_messages)
        if new_images:
            messages.append({"role": "user", "content": [
                {"type": "text", "text": "The following image(s) are the only newly fetched controlled evidence. Continue from the tool results and finish when sufficient."},
                *new_images,
            ]})

    return _result(review=review, selected=selected, evidence=evidence, audit=audit, decision="HUMAN_REVIEW", error="model_turn_limit", iterations=rounds, model_turns=model_turns)
