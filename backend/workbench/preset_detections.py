"""Reviewed visual overlays for the supplied, controlled customer-demo images.

These overlays make the offline replay inspectable without requiring a large
local model on the demo laptop.  They are deliberately scoped to image hashes
already accepted by :mod:`workbench.service`; unknown uploads never receive an
overlay or a business classification from this module.
"""

from __future__ import annotations

from typing import Any


# Coordinates were reviewed against the authorised 1448 x 1086 source images
# and are stored as pixels so Camera -> SLAM can continue to use the same
# image-space convention.  ``source`` is retained in the API payload rather
# than being presented as a live model response.
_OVERLAYS: dict[tuple[str, str, str], list[dict[str, Any]]] = {
    ("event-beverage-spill-002", "CAM-A1-01", "primary-ambiguous-v2.png"): [
        {"label": "液体污渍", "bbox": [643, 544, 827, 641], "confidence": 0.67},
    ],
    ("event-outdoor-tissue-001", "CAM-OUT-01", "primary.png"): [
        {"label": "地面纸巾", "bbox": [716, 675, 775, 716], "confidence": 0.94},
    ],
    ("event-beverage-spill-002", "CAM-A1-01", "primary.png"): [
        {"label": "液体污渍", "bbox": [643, 544, 827, 641], "confidence": 0.67},
    ],
    ("event-beverage-spill-002", "CAM-A1-02", "secondary.png"): [
        {"label": "液体污渍", "bbox": [684, 529, 802, 617], "confidence": 0.88},
    ],
    ("event-beverage-spill-002", "CAM-A1-04", "secondary.png"): [
        {"label": "液体污渍", "bbox": [630, 539, 817, 614], "confidence": 0.91},
    ],
    ("event-indoor-can-003", "CAM-A2-08", "primary.png"): [
        {"label": "易拉罐", "bbox": [681, 682, 753, 734], "confidence": 0.92},
    ],
    ("event-oversized-box-004", "CAM-A2-11", "primary.png"): [
        {"label": "大型纸箱", "bbox": [505, 570, 627, 706], "confidence": 0.94},
        {"label": "大型纸箱", "bbox": [604, 610, 723, 729], "confidence": 0.79},
    ],
}


def overlays_for_asset(event_id: str, camera_id: str, filename: str) -> list[dict[str, Any]]:
    """Return normalised review overlays for one exact controlled asset."""
    items = _OVERLAYS.get((event_id, camera_id, filename), [])
    return [
        {
            "label": item["label"],
            "confidence": item["confidence"],
            "bbox": {
                "x1": round(item["bbox"][0] / 1448, 6),
                "y1": round(item["bbox"][1] / 1086, 6),
                "x2": round(item["bbox"][2] / 1448, 6),
                "y2": round(item["bbox"][3] / 1086, 6),
            },
            "source": "CONTROLLED_REPLAY",
        }
        for item in items
    ]
