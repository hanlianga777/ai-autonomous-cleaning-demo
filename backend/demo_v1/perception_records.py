"""Persist safe LIVE model messages and replay them through the P1-C policy."""

from __future__ import annotations

from copy import deepcopy
import json
from math import isfinite
from typing import Any

from database.connection import get_event, list_model_records, save_model_record
from perception.qwen import VISUAL_JUDGMENT_SCHEMA, parse_visual_judgment
from perception.yolo import RealInferenceError
from spatial.spatial_data import CAMERAS


PIPELINE_SCHEMA = "p1c.visual-pipeline.v1"
_BUNDLE_KEYS = {"schema", "evidence_key", "event_id", "source_event_id", "responses", "model_turns"}
_TOOL_NAMES = {"find_supporting_cameras", "fetch_camera_evidence", "finish_visual_judgment"}
_CAMERA_IDS = {camera["camera_id"] for camera in CAMERAS}


def _error(message: str) -> RealInferenceError:
    return RealInferenceError(f"Invalid perception replay record: {message}")


def _is_finite_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and isfinite(value) and value >= 0


def _canonical_visual_json(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error("final judgment is not an object")
    schema = VISUAL_JUDGMENT_SCHEMA
    if set(value) != set(schema["properties"]) or not set(schema["required"]).issubset(value):
        raise _error("final judgment is not canonical")
    try:
        parse_visual_judgment(value, "replay-validation", 1, 0)
    except Exception as exc:
        raise _error("final judgment does not meet the visual schema") from exc
    return value


def validate_judgment(review: dict[str, Any]) -> None:
    """Stored runtime projections may include old aliases; provider output cannot."""
    try:
        parse_visual_judgment(review, str(review.get("model", "")), review.get("image_count", 1), review.get("elapsed_ms") or 0, projection=True)
    except Exception as exc:
        raise _error("stored judgment is malformed") from exc


def _decode_arguments(value: Any) -> dict[str, Any]:
    if not isinstance(value, str) or len(value) > 4000:
        raise _error("tool arguments must be bounded JSON text")
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError) as exc:
        raise _error("tool arguments are not JSON") from exc
    if not isinstance(decoded, dict):
        raise _error("tool arguments are not an object")
    return decoded


def _validate_tool_call(call: Any) -> None:
    if not isinstance(call, dict) or set(call) != {"id", "type", "function"}:
        raise _error("tool call shape is invalid")
    if not isinstance(call["id"], str) or not call["id"] or len(call["id"]) > 200 or call["type"] != "function":
        raise _error("tool call id or type is invalid")
    function = call["function"]
    if not isinstance(function, dict) or set(function) != {"name", "arguments"}:
        raise _error("tool function shape is invalid")
    name = function["name"]
    if name not in _TOOL_NAMES:
        raise _error("tool is not permitted")
    arguments = _decode_arguments(function["arguments"])
    if name == "find_supporting_cameras":
        if arguments:
            raise _error("coverage tool arguments are not empty")
    elif name == "fetch_camera_evidence":
        if set(arguments) != {"camera_id"} or arguments.get("camera_id") not in _CAMERA_IDS:
            raise _error("fetch camera is not legal")
    else:
        _canonical_visual_json(arguments)


def _validate_model_turns(turns: Any) -> None:
    if not isinstance(turns, list) or len(turns) > 6:
        raise _error("model turn count is invalid")
    for expected_turn, turn in enumerate(turns, start=1):
        if not isinstance(turn, dict):
            raise _error("model turn is not an object")
        allowed = {"turn", "source", "elapsed_ms", "historical_elapsed_ms", "role", "tool_calls", "content"}
        if not set(turn).issubset(allowed):
            raise _error("model turn contains unsafe fields")
        if turn.get("turn") != expected_turn or turn.get("source") != "LIVE_MODEL" or turn.get("role") != "assistant":
            raise _error("model turn provenance is invalid")
        if not _is_finite_number(turn.get("elapsed_ms")) or turn.get("historical_elapsed_ms") is not None:
            raise _error("LIVE model turn timing is invalid")
        has_tools, has_content = "tool_calls" in turn, "content" in turn
        if has_tools == has_content:
            raise _error("model turn must have exactly one safe response form")
        if has_tools:
            calls = turn["tool_calls"]
            if not isinstance(calls, list) or not 1 <= len(calls) <= 2:
                raise _error("tool call list is invalid")
            for call in calls:
                _validate_tool_call(call)
        else:
            content = turn["content"]
            if not isinstance(content, str) or len(content) > 8000:
                raise _error("model content is invalid")
            try:
                _canonical_visual_json(json.loads(content))
            except (TypeError, ValueError) as exc:
                raise _error("model content is not canonical JSON") from exc


def _validate_bundle(bundle: Any, *, source_event_id: str | None = None) -> None:
    if not isinstance(bundle, dict) or set(bundle) != _BUNDLE_KEYS:
        raise _error("bundle shape is invalid")
    if bundle.get("schema") != PIPELINE_SCHEMA:
        raise _error("bundle schema is invalid")
    for name in ("evidence_key", "event_id", "source_event_id"):
        if not isinstance(bundle.get(name), str) or not bundle[name]:
            raise _error(f"bundle {name} is invalid")
    if source_event_id is not None and bundle["source_event_id"] != source_event_id:
        raise _error("bundle source event id does not match record")
    responses = bundle.get("responses")
    if not isinstance(responses, dict) or set(responses) != {"first", "final", "second"}:
        raise _error("bundle has missing judgment phases")
    for name in ("first", "final"):
        if not isinstance(responses[name], dict):
            raise _error("bundle has no valid judgment")
        validate_judgment(responses[name])
    final = responses["final"]
    requires_second = final["evidence_sufficient"] and 0.50 <= final["decision_confidence"] < 0.85
    if requires_second != (responses["second"] is not None):
        raise _error("second-review record does not match the evidence gate")
    if responses["second"] is not None:
        if not isinstance(responses["second"], dict):
            raise _error("second-review response is invalid")
        validate_judgment(responses["second"])
    _validate_model_turns(bundle["model_turns"])


def _live_event_context(stored: dict[str, Any]) -> tuple[str, str]:
    runtime = stored.get("demo_v1") if isinstance(stored, dict) else None
    event_id = stored.get("event_id") if isinstance(stored, dict) else None
    source_event_id = runtime.get("source_event_id") if isinstance(runtime, dict) else None
    if (not isinstance(runtime, dict) or runtime.get("mode") != "LIVE" or not isinstance(event_id, str)
            or not event_id or not isinstance(source_event_id, str) or not source_event_id):
        raise _error("only a concrete LIVE event may create a replay record")
    return event_id, source_event_id


def save_perception_record(
    stored: dict[str, Any], key: str, first: dict[str, Any], final: dict[str, Any], second: dict[str, Any] | None,
    model_turns: list[dict[str, Any]],
) -> None:
    event_id, source_event_id = _live_event_context(stored)
    if not isinstance(key, str) or not key:
        raise _error("evidence key is invalid")
    bundle = {
        "schema": PIPELINE_SCHEMA, "evidence_key": key, "event_id": event_id, "source_event_id": source_event_id,
        "responses": {"first": first, "final": final, "second": second}, "model_turns": model_turns,
    }
    _validate_bundle(bundle, source_event_id=source_event_id)
    save_model_record(source_event_id, "event_review", "LIVE", bundle)


def load_perception_record(stored: dict[str, Any], key: str) -> dict[str, Any]:
    runtime = stored.get("demo_v1") if isinstance(stored, dict) else None
    source_event_id = runtime.get("source_event_id") if isinstance(runtime, dict) else None
    if not isinstance(key, str) or not key or not isinstance(source_event_id, str) or not source_event_id:
        raise RealInferenceError("No compatible LIVE perception record exists for the current evidence and model contract.")
    for row in list_model_records(source_event_id, "event_review"):
        bundle = row["payload"]
        if not isinstance(bundle, dict) or bundle.get("schema") != PIPELINE_SCHEMA or bundle.get("evidence_key") != key:
            continue
        try:
            _validate_bundle(bundle, source_event_id=source_event_id)
            original = get_event(bundle["event_id"])
            original_runtime = original.get("demo_v1") if isinstance(original, dict) else None
            if (not isinstance(original_runtime, dict) or original_runtime.get("mode") != "LIVE"
                    or original_runtime.get("source_event_id") != source_event_id):
                raise _error("record does not belong to a matching LIVE event")
        except (RealInferenceError, TypeError, ValueError):
            continue
        replay = deepcopy(bundle)
        for review in replay["responses"].values():
            if review is not None:
                review.update({
                    "original_provider": review.get("provider"), "provider": "Stable Replay", "source": "REPLAY",
                    "source_badge": "REPLAY", "historical_elapsed_ms": review.get("elapsed_ms"), "elapsed_ms": None,
                    "replay_record_id": row["id"], "replay_event_id": bundle["event_id"],
                })
        return replay
    raise RealInferenceError("No compatible LIVE perception record exists for the current evidence and model contract.")


class RecordedToolTurns:
    """Finite, validated assistant-message feed; tools are executed again by P1-C."""

    def __init__(self, turns: list[dict[str, Any]]):
        _validate_model_turns(turns)
        self.turns = deepcopy(turns)
        self.index = 0

    def __call__(self, messages: list[dict], tools: list[dict], model: str) -> tuple[dict, int]:
        if self.index >= len(self.turns):
            raise RealInferenceError("Replay has no further model tool-turn response.")
        turn = self.turns[self.index]
        self.index += 1
        message: dict[str, Any] = {"role": "assistant"}
        if "tool_calls" in turn:
            message["tool_calls"] = deepcopy(turn["tool_calls"])
        else:
            message["content"] = turn["content"]
        return message, int(turn["elapsed_ms"])

    def assert_consumed(self) -> None:
        if self.index != len(self.turns):
            raise RealInferenceError("Replay tool-turn sequence no longer matches the current workflow.")
