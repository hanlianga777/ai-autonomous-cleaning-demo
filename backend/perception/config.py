"""Runtime configuration for the independently deployable AI Lab."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_project_env() -> None:
    """Load local .env files without replacing explicit shell environment.

    This intentionally tiny loader avoids a runtime dependency and keeps keys
    on the local machine. Values are never returned, logged or committed.
    """
    root = Path(__file__).resolve().parents[2]
    for path in (root / ".env", root / "backend" / ".env"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


@dataclass(frozen=True)
class AiRuntime:
    requested_mode: str
    active_mode: str
    label: str
    ready: bool
    reason: str
    yolo_model: str | None
    qwen_model: str


def get_runtime() -> AiRuntime:
    """Resolve a truthful AI runtime without attempting any cloud call.

    REAL is available only when both a local YOLO model and DashScope key are
    supplied.  This prevents a configured-looking screen from pretending that
    an inference actually happened.
    """
    _load_project_env()
    requested = os.getenv("AI_LAB_MODE", os.getenv("AI_MODE", "auto")).strip().lower()
    if requested not in {"auto", "mock", "real"}:
        requested = "auto"
    model = os.getenv("AI_LAB_YOLO_MODEL", "").strip() or None
    key_present = bool(os.getenv("DASHSCOPE_API_KEY", "").strip())
    model_present = bool(model and Path(model).expanduser().is_file())
    if requested != "mock" and model_present and key_present:
        return AiRuntime(requested, "real", "REAL AI MODE", True, "Local YOLO model and DashScope credentials are configured.", model, os.getenv("DASHSCOPE_VL_MODEL", "qwen-vl-max"))
    if requested == "real":
        missing = []
        if not model_present:
            missing.append("AI_LAB_YOLO_MODEL")
        if not key_present:
            missing.append("DASHSCOPE_API_KEY")
        reason = f"REAL mode requested but missing: {', '.join(missing)}."
    elif requested == "mock":
        reason = "MOCK mode was selected explicitly."
    else:
        reason = "REAL prerequisites are not configured; stable local Mock is active."
    return AiRuntime(requested, "mock", "DEMO MOCK MODE", False, reason, model, os.getenv("DASHSCOPE_VL_MODEL", "qwen-vl-max"))
