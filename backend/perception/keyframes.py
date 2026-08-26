"""Video keyframe extraction kept optional so Mock mode has no CV dependency."""

from __future__ import annotations

from pathlib import Path

from perception.yolo import RealInferenceError


def extract_keyframes(video_path: Path, output_dir: Path) -> list[Path]:
    try:
        import cv2
    except ImportError as error:
        raise RealInferenceError("OpenCV is not installed. Install backend/requirements-real-ai.txt for MP4 REAL mode.") from error
    capture = cv2.VideoCapture(str(video_path))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        capture.release()
        raise RealInferenceError("Unable to read a usable video frame from this MP4.")
    output_dir.mkdir(parents=True, exist_ok=True)
    indices = sorted({0, max(0, total // 2), max(0, total - 1)})
    frames: list[Path] = []
    for index in indices:
        capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = capture.read()
        if ok:
            path = output_dir / f"keyframe-{index}.jpg"
            if cv2.imwrite(str(path), frame):
                frames.append(path)
    capture.release()
    if not frames:
        raise RealInferenceError("Unable to extract keyframes from this MP4.")
    return frames
