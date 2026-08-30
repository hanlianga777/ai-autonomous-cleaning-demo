"""Phase 4 AI Lab orchestration. It deliberately does not dispatch workflows."""

from __future__ import annotations

import os
from urllib.error import HTTPError, URLError
from pathlib import Path
from uuid import uuid4

from perception.config import get_runtime
from perception.qwen import request_qwen_tool_turn, run_qwen_vl
from perception.business_detection import business_detection
from perception.keyframes import extract_keyframes
from perception.integration import scheduler_preview
from perception.mock import list_mock_cases, mock_analysis, mock_case_analysis
from perception.models import AI_RESULT_SCHEMA_VERSION, derive_required_capabilities, perception_schema, validate_ai_result_schema
from perception.yolo import RealInferenceError, run_yolo
from spatial.calibration import CalibrationError, map_pixel_to_slam

UPLOAD_ROOT = Path(__file__).resolve().parents[1] / ".runtime" / "ai-lab"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_SUFFIXES = {".mp4"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def ai_lab_status() -> dict:
    runtime = get_runtime()
    return {"requested_mode": runtime.requested_mode, "active_mode": runtime.active_mode, "mode_label": runtime.label, "real_ready": runtime.ready, "reason": runtime.reason, "models": {"yolo": runtime.yolo_model or "not configured", "qwen_vl": runtime.qwen_model}, "accepted_media": {"images": sorted(IMAGE_SUFFIXES), "videos": sorted(VIDEO_SUFFIXES)}, "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024)}


def system_ai_status() -> dict:
    """Configuration truth only; this endpoint never calls a cloud model."""
    runtime = get_runtime()
    yolo_path = Path(runtime.yolo_model).expanduser() if runtime.yolo_model else None
    return {
        "contract": "system-ai-status.v2",
        "overall_mode": runtime.active_mode,
        "reason": runtime.reason,
        "yolo": {"mode": "REAL" if runtime.active_mode == "real" else "MOCK", "model": yolo_path.name if yolo_path else None, "loaded": bool(yolo_path and yolo_path.is_file() and runtime.active_mode == "real"), "weights_path": str(yolo_path) if yolo_path else None},
        "qwen_vl": {"mode": "CONFIGURED" if runtime.qwen_ready else "KEY_MISSING", "model": runtime.qwen_model, "api_key_configured": runtime.qwen_ready, "reachable": "not_checked"},
        "multiview_agent": {"mode": "CONFIGURED" if runtime.agent_ready else "KEY_MISSING", "model": runtime.agent_model, "max_additional_cameras": 2, "max_iterations": 2, "reachable": "not_checked"},
        "camera_to_slam": {"mode": "REAL_CALCULATION", "implementation": "spatial.calibration.map_pixel_to_slam"},
        "scheduler": {"mode": "REAL_ALGORITHM", "implementation": "Phase 3 deterministic capability + score"},
        "robot": {"mode": "SIMULATION"},
        "verification": {"mode": "REAL" if runtime.qwen_ready else "UNAVAILABLE"},
        "readiness": {
            "cloud_vlm_configured": runtime.qwen_ready,
            "cloud_vlm_reachable": "not_checked",
            "multiview_agent_configured": runtime.agent_ready,
            "multiview_agent_reachable": "not_checked",
            "controlled_edge_ready": runtime.controlled_edge_ready,
            "local_yolo_ready": runtime.local_yolo_ready,
            "full_ai_lab_ready": runtime.full_ai_lab_ready,
            "interview_live_ready": runtime.interview_live_ready,
        },
    }


def _probe_outcome(error: Exception) -> str:
    """Stable, secret-free status category for a cloud readiness probe."""
    if isinstance(error, HTTPError):
        if error.code in {401, 403}:
            return "AUTH_FAILED"
        if error.code == 429:
            return "RATE_LIMITED"
        if error.code in {404, 400, 422}:
            return "MODEL_UNAVAILABLE"
        if error.code >= 500:
            return "PROVIDER_5XX"
    if isinstance(error, (URLError, TimeoutError)):
        return "NETWORK_ERROR"
    text = str(error).lower()
    if "401" in text or "403" in text or "auth" in text:
        return "AUTH_FAILED"
    if "429" in text or "rate" in text:
        return "RATE_LIMITED"
    if "not configured" in text:
        return "KEY_MISSING"
    if "404" in text or "model" in text:
        return "MODEL_UNAVAILABLE"
    if "5" in text and "http" in text:
        return "PROVIDER_5XX"
    return "NETWORK_ERROR"


def interview_ai_readiness_probe() -> dict:
    """Probe the two official cloud models without creating any business data."""
    runtime = get_runtime()
    base = system_ai_status()
    if not runtime.qwen_ready:
        base["readiness"].update({"cloud_vlm_reachable": "KEY_MISSING", "multiview_agent_reachable": "KEY_MISSING", "interview_live_ready": False})
        return base
    outcomes: dict[str, str] = {}
    for role, model in (("cloud_vlm", runtime.qwen_model), ("multiview_agent", runtime.agent_model)):
        try:
            answer, _ = request_qwen_tool_turn([{"role": "user", "content": "Reply exactly READY."}], [], model)
            outcomes[role] = "READY" if isinstance(answer.get("content"), str) else "MODEL_UNAVAILABLE"
        except Exception as error:  # transport errors are intentionally projected, not logged here
            outcomes[role] = _probe_outcome(error)
    ready = runtime.controlled_edge_ready and outcomes["cloud_vlm"] == "READY" and outcomes["multiview_agent"] == "READY"
    base["readiness"].update({
        "cloud_vlm_reachable": outcomes["cloud_vlm"],
        "multiview_agent_reachable": outcomes["multiview_agent"],
        "interview_live_ready": ready,
    })
    return base


def ai_lab_schema() -> dict:
    return perception_schema()


def available_mock_cases() -> list[dict[str, str]]:
    return list_mock_cases()


def media_kind(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    raise ValueError("Only JPG, JPEG, PNG, WEBP and MP4 uploads are accepted.")


def save_upload(filename: str, content: bytes) -> Path:
    if not content:
        raise ValueError("The uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f"The upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
    safe_name = Path(filename).name.replace(" ", "-")
    run_dir = UPLOAD_ROOT / uuid4().hex
    run_dir.mkdir(parents=True, exist_ok=False)
    path = run_dir / safe_name
    path.write_bytes(content)
    return path


def _location(camera_id: str, detection: dict) -> dict | None:
    bbox = detection["bbox"]
    u = (bbox["x1"] + bbox["x2"]) / 2
    v = (bbox["y1"] + bbox["y2"]) / 2
    try:
        return map_pixel_to_slam(camera_id, u, v)
    except CalibrationError:
        return None


def _with_compatibility_preview(result: dict) -> dict:
    workflow_input, preview = scheduler_preview(result)
    result["workflow_input"] = workflow_input
    result["scheduler_preview"] = preview
    return validate_ai_result_schema(result)


def analyze_upload(file_path: Path, original_filename: str, camera_id: str) -> dict:
    media_type = media_kind(original_filename)
    runtime = get_runtime()
    if runtime.active_mode == "mock":
        return _with_compatibility_preview(mock_analysis(original_filename, media_type, camera_id))
    try:
        frames = [file_path] if media_type == "image" else extract_keyframes(file_path, file_path.parent / "keyframes")
        detections = []
        for frame_index, frame in enumerate(frames):
            for detection in run_yolo(frame, runtime.yolo_model or ""):
                detection["frame_index"] = frame_index
                detections.append(detection)
        primary = max(detections, key=lambda item: item["confidence"], default=None)
        vlm_frame = frames[primary["frame_index"]] if primary else frames[0]
        vlm = run_qwen_vl(vlm_frame, runtime.qwen_model)
        location = _location(camera_id, primary) if primary else None
        task_profile = derive_required_capabilities(vlm["task_profile"], location["location"]["building"]) if location else vlm["task_profile"]
        result = {
            "schema_version": AI_RESULT_SCHEMA_VERSION,
            "mode": "real", "mode_label": "REAL AI MODE", "source": {"filename": original_filename, "media_type": media_type, "camera_id": camera_id},
            "pipeline": {"yolo": Path(runtime.yolo_model or "").name, "vlm": runtime.qwen_model, "keyframes": len(frames)},
            "detections": detections, "location": location,
            "perception": {key: value for key, value in vlm.items() if key not in {"task_profile", "business_class", "business_confidence"}}, "business_detections": business_detection(vlm, detections), "task_profile": task_profile,
            "workflow_input": None, "scheduler_preview": None,
            "notes": ["REAL mode executed local YOLO and DashScope Qwen-VL.", "AI Lab output is intentionally separate from the Scenario workflow."],
        }
        return _with_compatibility_preview(result)
    except RealInferenceError:
        raise
    except Exception as error:
        raise RealInferenceError(f"AI Lab real pipeline failed: {error}") from error


def analyze_mock_case(case_name: str) -> dict:
    """Run an AI Lab-only business fixture through the same compatibility preview."""
    return _with_compatibility_preview(mock_case_analysis(case_name))
