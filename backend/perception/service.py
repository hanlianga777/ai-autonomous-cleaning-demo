"""Phase 4 AI Lab orchestration. It deliberately does not dispatch workflows."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from perception.config import get_runtime
from perception.keyframes import extract_keyframes
from perception.mock import mock_analysis
from perception.qwen import run_qwen_vl
from perception.yolo import RealInferenceError, run_yolo
from spatial.calibration import CalibrationError, map_pixel_to_slam

UPLOAD_ROOT = Path(__file__).resolve().parents[1] / ".runtime" / "ai-lab"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_SUFFIXES = {".mp4"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def ai_lab_status() -> dict:
    runtime = get_runtime()
    return {"requested_mode": runtime.requested_mode, "active_mode": runtime.active_mode, "mode_label": runtime.label, "real_ready": runtime.ready, "reason": runtime.reason, "models": {"yolo": runtime.yolo_model or "not configured", "qwen_vl": runtime.qwen_model}, "accepted_media": {"images": sorted(IMAGE_SUFFIXES), "videos": sorted(VIDEO_SUFFIXES)}, "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024)}


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


def analyze_upload(file_path: Path, original_filename: str, camera_id: str) -> dict:
    media_type = media_kind(original_filename)
    runtime = get_runtime()
    if runtime.active_mode == "mock":
        return mock_analysis(original_filename, media_type, camera_id) | {"runtime_reason": runtime.reason}
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
        return {
            "mode": "real", "mode_label": "REAL AI MODE", "source": {"filename": original_filename, "media_type": media_type, "camera_id": camera_id},
            "pipeline": {"yolo": Path(runtime.yolo_model or "").name, "vlm": runtime.qwen_model, "keyframes": len(frames)},
            "detections": detections, "location": _location(camera_id, primary) if primary else None,
            "vlm": {key: value for key, value in vlm.items() if key != "task_profile"}, "task_profile": vlm["task_profile"],
            "notes": ["REAL mode executed local YOLO and DashScope Qwen-VL.", "AI Lab output is intentionally separate from the Scenario workflow."],
        }
    except RealInferenceError:
        raise
    except Exception as error:
        raise RealInferenceError(f"AI Lab real pipeline failed: {error}") from error
