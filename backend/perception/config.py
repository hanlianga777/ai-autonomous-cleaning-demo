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
            # A non-empty process value is intentional and wins.  An empty
            # exported value, however, must not shadow a valid local secret:
            # macOS launchers commonly inherit empty placeholders.
            if key and value and not os.getenv(key, "").strip():
                os.environ[key] = value


@dataclass(frozen=True)
class AiRuntime:
    requested_mode: str
    active_mode: str
    label: str
    ready: bool
    reason: str
    yolo_model: str | None
    qwen_model: str
    qwen_ready: bool
    agent_model: str
    agent_ready: bool
    controlled_edge_ready: bool
    local_yolo_ready: bool
    full_ai_lab_ready: bool
    interview_live_ready: bool


def get_agent_model() -> str:
    """Explicit configurable image/tool model, separate from semantic VLM."""
    _load_project_env()
    return os.getenv("DASHSCOPE_AGENT_MODEL", "qwen3-vl-plus").strip() or "qwen3-vl-plus"


def get_runtime() -> AiRuntime:
    """Return distinct AI-Lab and official-Demo readiness facts.

    Official Demo01–04 consume controlled edge evidence plus two cloud models;
    they do not need a locally installed YOLO model.  ``active_mode`` remains
    the *AI Lab* pipeline mode so a mock local lab is never presented as a
    real YOLO run.
    """
    _load_project_env()
    requested = os.getenv("AI_LAB_MODE", os.getenv("AI_MODE", "auto")).strip().lower()
    if requested not in {"auto", "mock", "real"}:
        requested = "auto"
    model = os.getenv("AI_LAB_YOLO_MODEL", "").strip() or None
    key_present = bool(os.getenv("DASHSCOPE_API_KEY", "").strip())
    model_present = bool(model and Path(model).expanduser().is_file())
    qwen_model = os.getenv("DASHSCOPE_VL_MODEL", "qwen-vl-max").strip() or "qwen-vl-max"
    agent_model = get_agent_model()
    controlled_edge_ready = True
    full_ai_lab_ready = model_present and key_present
    interview_live_ready = controlled_edge_ready and key_present and bool(agent_model)
    if requested != "mock" and full_ai_lab_ready:
        return AiRuntime(requested, "real", "REAL AI MODE", True, "Local YOLO model and DashScope credentials are configured.", model, qwen_model, key_present, agent_model, key_present, controlled_edge_ready, model_present, full_ai_lab_ready, interview_live_ready)
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
    return AiRuntime(requested, "mock", "DEMO MOCK MODE", False, reason, model, qwen_model, key_present, agent_model, key_present, controlled_edge_ready, model_present, full_ai_lab_ready, interview_live_ready)
