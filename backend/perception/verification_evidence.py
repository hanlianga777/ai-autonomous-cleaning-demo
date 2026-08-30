"""Target-region evidence for conservative post-cleaning verification.

The detection evidence used to dispatch a task is also the only allowed source
for its verification region.  This avoids a second, scenario-specific image
coordinate system and makes a post-cleaning decision about the originally
detected object rather than unrelated changes elsewhere in a camera frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from math import ceil, isfinite
from pathlib import Path
from typing import Any

from PIL import Image

from perception.yolo import RealInferenceError


ROI_CONTRACT = "target_roi.v1"
ROI_SOURCE = "controlled_yolo_normalized_union"
# A minimum window keeps a small object legible to the VLM; relative padding
# keeps larger spills and cartons in context.  Both are normalized so the same
# region can be applied to before and after images of different resolutions.
ROI_MARGIN_RATIO = 0.60
ROI_MIN_WIDTH = 0.12
ROI_MIN_HEIGHT = 0.12


@dataclass(frozen=True)
class VerificationEvidence:
    """In-memory paired target crops and their replay-bindable factual context."""

    before_roi: bytes
    after_roi: bytes
    context: dict[str, Any]


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise RealInferenceError(f"Verification target bbox {field} must be a finite number.")
    return float(value)


def _bbox_union(controlled_yolo: list[dict[str, Any]], camera_id: str) -> tuple[dict[str, float], list[str]]:
    """Return the union of primary-camera normalized detection boxes.

    Supporting-camera boxes deliberately cannot be unioned with a primary
    camera's image plane.  They are excluded rather than silently transformed.
    A malformed primary-camera box fails closed because using a guessed target
    would weaken the audit contract.
    """
    candidates = [item for item in controlled_yolo if item.get("camera_id") == camera_id]
    if not candidates:
        raise RealInferenceError("No controlled edge target exists for verification camera.")
    boxes: list[tuple[float, float, float, float]] = []
    labels: list[str] = []
    for item in candidates:
        bbox = item.get("bbox")
        if not isinstance(bbox, dict):
            raise RealInferenceError("Verification target bbox is missing.")
        x1, y1, x2, y2 = (_number(bbox.get(key), key) for key in ("x1", "y1", "x2", "y2"))
        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
            raise RealInferenceError("Verification target bbox must be ordered and normalized.")
        boxes.append((x1, y1, x2, y2))
        label = item.get("class_name")
        if isinstance(label, str) and label.strip():
            labels.append(label.strip())
    if not boxes:
        raise RealInferenceError("No controlled edge target bounding boxes are available.")
    return {
        "x1": min(box[0] for box in boxes),
        "y1": min(box[1] for box in boxes),
        "x2": max(box[2] for box in boxes),
        "y2": max(box[3] for box in boxes),
    }, sorted(set(labels))


def _expanded_roi(union: dict[str, float]) -> dict[str, float]:
    width = union["x2"] - union["x1"]
    height = union["y2"] - union["y1"]
    target_width = max(width * (1 + 2 * ROI_MARGIN_RATIO), ROI_MIN_WIDTH)
    target_height = max(height * (1 + 2 * ROI_MARGIN_RATIO), ROI_MIN_HEIGHT)
    center_x = (union["x1"] + union["x2"]) / 2
    center_y = (union["y1"] + union["y2"]) / 2
    x1 = max(0.0, center_x - target_width / 2)
    x2 = min(1.0, center_x + target_width / 2)
    y1 = max(0.0, center_y - target_height / 2)
    y2 = min(1.0, center_y + target_height / 2)
    if not (x1 < x2 and y1 < y2):
        raise RealInferenceError("Verification target ROI is empty after clipping.")
    return {"x1": round(x1, 6), "y1": round(y1, 6), "x2": round(x2, 6), "y2": round(y2, 6)}


def _crop_png(path: Path, roi: dict[str, float]) -> bytes:
    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
            width, height = image.size
            if width < 1 or height < 1:
                raise ValueError("empty source image")
            # Floor/ceil preserve the requested normalized region even for a
            # tiny original detection.  Clamp once more for defensive safety.
            left = max(0, min(width - 1, int(roi["x1"] * width)))
            top = max(0, min(height - 1, int(roi["y1"] * height)))
            right = max(left + 1, min(width, ceil(roi["x2"] * width)))
            bottom = max(top + 1, min(height, ceil(roi["y2"] * height)))
            crop = image.crop((left, top, right, bottom))
            output = BytesIO()
            crop.save(output, format="PNG", optimize=True)
            return output.getvalue()
    except (FileNotFoundError, OSError, ValueError) as error:
        raise RealInferenceError("Verification target evidence image is unavailable or invalid.") from error


def build_verification_evidence(
    *,
    before: Path,
    after: Path,
    controlled_yolo: list[dict[str, Any]],
    camera_id: str,
    object_type: str | None,
) -> VerificationEvidence:
    """Build same-normalized-region before/after crops without writing assets.

    The returned context is intentionally factual and is included in the
    existing replay key by the caller.  It contains crop hashes rather than
    image data, while the raw crops are sent only to the single verifier call.
    """
    union, labels = _bbox_union(controlled_yolo, camera_id)
    roi = _expanded_roi(union)
    before_roi = _crop_png(before, roi)
    after_roi = _crop_png(after, roi)
    target_type = object_type.strip() if isinstance(object_type, str) and object_type.strip() else "unknown"
    context = {
        "verification_contract": ROI_CONTRACT,
        "roi_source": ROI_SOURCE,
        "target": {
            "camera_id": camera_id,
            "object_type": target_type,
            "edge_labels": labels,
            "bbox_union": union,
            "roi": roi,
            "crop_sha256": {
                "before": sha256(before_roi).hexdigest(),
                "after": sha256(after_roi).hexdigest(),
            },
        },
    }
    return VerificationEvidence(before_roi=before_roi, after_roi=after_roi, context=context)
