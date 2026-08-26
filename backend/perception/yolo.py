"""Optional Ultralytics YOLO adapter. Imported only for REAL AI MODE."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class RealInferenceError(RuntimeError):
    pass


def run_yolo(image_path: Path, model_path: str) -> list[dict[str, Any]]:
    try:
        from ultralytics import YOLO
    except ImportError as error:
        raise RealInferenceError("Ultralytics is not installed. Install backend/requirements-real-ai.txt for REAL mode.") from error
    try:
        model = YOLO(model_path)
        result = model.predict(source=str(image_path), conf=0.25, verbose=False)[0]
        names = result.names
        detections = []
        for box in result.boxes:
            coords = [round(float(item), 2) for item in box.xyxy[0].tolist()]
            class_id = int(box.cls[0].item())
            detections.append({
                "class_name": str(names[class_id]),
                "confidence": round(float(box.conf[0].item()), 4),
                "bbox": {"x1": coords[0], "y1": coords[1], "x2": coords[2], "y2": coords[3]},
                "frame_index": 0,
            })
        return detections
    except Exception as error:  # Surface the error; never fabricate a REAL result.
        raise RealInferenceError(f"YOLO inference failed: {error}") from error
