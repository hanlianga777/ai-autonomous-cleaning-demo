"""Versioned external-response replay; never stores a precomputed workflow.

Records are bound to actual image bytes, model and factual request context.
Legacy unversioned rows are deliberately ineligible. Algorithms and state
transitions are not part of the response bundle and must execute afresh.
"""
from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

from database.connection import get_event, list_model_records, save_model_record
from perception.yolo import RealInferenceError
from perception.qwen import EVENT_PROMPT, TARGETED_REVIEW_PROMPT, VERIFICATION_PROMPT, validate_verification_response

SCHEMA = "p1a.ai-response.v1"


def evidence_key(images: list[Path], context: dict, model: str) -> str:
    try:
        content = {"schema": SCHEMA, "model": model, "prompt_contract": [EVENT_PROMPT, TARGETED_REVIEW_PROMPT, VERIFICATION_PROMPT], "images": [sha256(path.read_bytes()).hexdigest() for path in images], "context": context}
        return sha256(json.dumps(content, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()
    except (OSError, ValueError, TypeError) as error:
        raise RealInferenceError("AI evidence is unavailable or invalid.") from error


def validate_response(response: dict, phase: str) -> None:
    if phase == "verification":
        validate_verification_response(response)
        return
    if not isinstance(response, dict):
        raise RealInferenceError("Structured AI response is not an object.")
    key = "decision_confidence" if phase == "event_review" else "confidence"
    value = response.get(key)
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) or not 0 <= value <= 1:
        raise RealInferenceError("Structured AI confidence is invalid.")
    flag = "need_clean" if phase == "event_review" else "verification_pass"
    if type(response.get(flag)) is not bool:
        raise RealInferenceError(f"Structured AI {flag} is invalid.")
    if phase == "event_review":
        if not isinstance(response.get("event_type"), str) or response["event_type"] not in {"small_litter", "liquid", "can", "large_object", "unknown"}:
            raise RealInferenceError("Structured AI event type is invalid.")
        if not isinstance(response.get("severity"), str) or response["severity"] not in {"low", "medium", "high"} or not isinstance(response.get("surface_type"), str):
            raise RealInferenceError("Structured AI TaskProfile fields are invalid.")
        actions = {"dispatch_robot", "human_review", "ignore"}
    else:
        actions = {"close", "retry", "human_review"}
    if not isinstance(response.get("next_action"), str) or response["next_action"] not in actions:
        raise RealInferenceError("Structured AI next action is invalid.")


def save_live_bundle(stored: dict, phase: str, key: str, responses: dict) -> None:
    for response in responses.values():
        if response is not None:
            validate_response(response, phase)
    save_model_record(stored["demo_v1"]["source_event_id"], phase, "LIVE", {
        "schema": SCHEMA, "evidence_key": key, "event_id": stored["event_id"], "responses": responses,
    })


def load_replay_bundle(stored: dict, phase: str, key: str) -> dict:
    for row in list_model_records(stored["demo_v1"]["source_event_id"], phase):
        record = row["payload"]
        if record.get("schema") != SCHEMA or record.get("evidence_key") != key:
            continue
        if not isinstance(record.get("event_id"), str):
            continue
        original = get_event(record["event_id"])
        if (not original or original.get("demo_v1", {}).get("mode") != "LIVE"
                or original["demo_v1"].get("source_event_id") != stored["demo_v1"]["source_event_id"]):
            continue
        responses = record.get("responses")
        required = {"first", "second"} if phase == "event_review" else {"verification"}
        if not isinstance(responses, dict) or set(responses) != required:
            continue
        if not responses.get("first" if phase == "event_review" else "verification"):
            continue
        try:
            for response in responses.values():
                if response is not None:
                    validate_response(response, phase)
        except RealInferenceError:
            continue
        if phase == "event_review" and (0.5 <= responses["first"]["decision_confidence"] < 0.85) != (responses["second"] is not None):
            continue
        result = deepcopy(responses)
        for response in result.values():
            if response is not None:
                response.update({"original_provider": response.get("provider"), "historical_elapsed_ms": response.get("elapsed_ms"), "provider": "Stable Replay", "source": "REPLAY", "source_badge": "REPLAY", "elapsed_ms": None, "replay_record_id": row["id"], "replay_event_id": record["event_id"], "replayed_recorded_at": row["recorded_at"]})
        return result
    raise RealInferenceError("No compatible LIVE structured AI record exists for these images, model and context.")
