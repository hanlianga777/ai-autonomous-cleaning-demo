"""Machine-readable identity for the locally launched interview runtime.

This is intentionally separate from the Git revision. A running process must
prove its API surface, while GitHub remains the source of truth for code state.
"""

from __future__ import annotations

import re

from perception.config import get_agent_model
from perception.service import system_ai_status

RELEASE_CONTRACT = "cleanops.interview.v1"
REQUIRED_CAPABILITIES = (
    "stage_runtime",
    "event_archive",
    "analytics",
    "robot_operations",
    "advanced_observability",
    "spatial_v2",
)
SAFE_MODEL_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _safe_model_identifier(value: object) -> str:
    """Model configuration is displayable only as an opaque identifier."""
    return value if isinstance(value, str) and SAFE_MODEL_IDENTIFIER.fullmatch(value) else "[REDACTED]"


def runtime_fingerprint() -> dict:
    """Return a stable, secret-free contract used by the local launcher."""
    return {
        "app_name": "CleanOps Interview Demo",
        "backend_version": "0.6.0",
        "release_contract": RELEASE_CONTRACT,
        "capabilities": list(REQUIRED_CAPABILITIES),
    }


def runtime_info() -> dict:
    """Return the small allowlisted projection displayed in Advanced."""
    ai_status = system_ai_status()
    qwen = ai_status.get("qwen_vl", {})
    yolo = ai_status.get("yolo", {})
    return {
        **runtime_fingerprint(),
        "cloud_status": qwen.get("mode", "UNKNOWN"),
        "vlm_model": _safe_model_identifier(qwen.get("model")),
        "agent_model": _safe_model_identifier(get_agent_model()),
        "evidence_mode": "REAL_YOLO" if yolo.get("loaded") else "CONTROLLED_EVIDENCE",
    }
