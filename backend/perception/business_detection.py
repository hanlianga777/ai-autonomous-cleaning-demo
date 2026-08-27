"""Translate model evidence into the five customer-facing business classes.

This is a transparent presentation adapter: raw YOLO labels are preserved and
liquid / leaf / large-object classes are never claimed from stock YOLO alone.
"""

from __future__ import annotations

from typing import Any


BUSINESS_CLASSES = {"liquid", "can", "leaf", "large_object", "small_litter"}
YOLO_TO_BUSINESS = {
    "can": "can",
    "bottle": "small_litter",
    "cup": "small_litter",
    "banana": "small_litter",
}


def business_detection(vlm: dict[str, Any], detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one auditable business result without inventing a detector box."""
    raw_class = str(vlm.get("business_class", "")).strip().lower()
    raw_confidence = vlm.get("business_confidence", vlm.get("confidence", 0.0))
    vlm_class = raw_class if raw_class in BUSINESS_CLASSES else None
    vlm_confidence = round(float(raw_confidence), 4) if isinstance(raw_confidence, (int, float)) else 0.0
    matching = next((item for item in detections if YOLO_TO_BUSINESS.get(str(item.get("class_name", "")).lower()) == vlm_class), None)
    if vlm_class:
        return [{
            "bbox": matching.get("bbox") if matching else None,
            "business_class": vlm_class,
            "display_confidence": vlm_confidence,
            "confidence_source": "FUSION" if matching else "VLM",
            "raw_yolo_class": matching.get("class_name") if matching else None,
            "raw_yolo_confidence": matching.get("confidence") if matching else None,
            "vlm_class": vlm_class,
            "vlm_confidence": vlm_confidence,
        }]
    if detections:
        best = max(detections, key=lambda item: float(item.get("confidence", 0.0)))
        inferred = YOLO_TO_BUSINESS.get(str(best.get("class_name", "")).lower())
        if inferred:
            return [{
                "bbox": best.get("bbox"), "business_class": inferred,
                "display_confidence": best.get("confidence", 0.0), "confidence_source": "YOLO",
                "raw_yolo_class": best.get("class_name"), "raw_yolo_confidence": best.get("confidence"),
                "vlm_class": None, "vlm_confidence": None,
            }]
    return []
