"""A LangGraph agent with an intentionally small, audited tool surface."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from perception.multiview.config import GRAY_ZONE_MAX, GRAY_ZONE_MIN, MAX_ADDITIONAL_CAMERAS, MAX_AGENT_ITERATIONS, MULTIVIEW_CONFIRM_THRESHOLD, MULTIVIEW_REVIEW_THRESHOLD
from perception.multiview.tools import camera_coverage_tool, frame_fetch_tool, vlm_tool


class MultiViewState(TypedDict, total=False):
    initial_confidence: float
    primary_camera_id: str
    location: dict[str, Any]
    scenario: str
    selected_cameras: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    final_confidence: float
    decision: str
    iteration_count: int


def _coverage_node(state: MultiViewState) -> dict:
    coverage = camera_coverage_tool(state["location"], state["primary_camera_id"], MAX_ADDITIONAL_CAMERAS)
    return {"selected_cameras": coverage["selected_cameras"], "tool_calls": [coverage], "iteration_count": 1}


def _frame_fetch_node(state: MultiViewState) -> dict:
    frames = [frame_fetch_tool(camera["camera_id"], state["scenario"]) for camera in state.get("selected_cameras", [])]
    return {"evidence": frames, "tool_calls": state.get("tool_calls", []) + frames}


def _vlm_node(state: MultiViewState) -> dict:
    vlm = vlm_tool(state.get("evidence", []), state["scenario"])
    return {"final_confidence": vlm["confidence"], "evidence": vlm["evidence"], "tool_calls": state.get("tool_calls", []) + [vlm]}


def _decision_node(state: MultiViewState) -> dict:
    confidence = state["final_confidence"]
    decision = "CONFIRM" if confidence >= MULTIVIEW_CONFIRM_THRESHOLD else "HUMAN_REVIEW" if confidence >= MULTIVIEW_REVIEW_THRESHOLD else "REJECT"
    return {"decision": decision}


def _build_graph():
    builder = StateGraph(MultiViewState)
    builder.add_node("camera_coverage", _coverage_node)
    builder.add_node("frame_fetch", _frame_fetch_node)
    builder.add_node("vlm", _vlm_node)
    builder.add_node("decision", _decision_node)
    builder.add_edge(START, "camera_coverage")
    builder.add_edge("camera_coverage", "frame_fetch")
    builder.add_edge("frame_fetch", "vlm")
    builder.add_edge("vlm", "decision")
    builder.add_edge("decision", END)
    return builder.compile()


GRAPH = _build_graph()


def in_gray_zone(confidence: float) -> bool:
    return GRAY_ZONE_MIN <= confidence < GRAY_ZONE_MAX


def run_multi_view_agent(initial_confidence: float, primary_camera_id: str, location: dict[str, Any], scenario: str = "scenario02") -> dict[str, Any]:
    """Run only for the configured gray zone and expose an audit, never CoT."""
    if not in_gray_zone(initial_confidence):
        return {"triggered": False, "initial_confidence": initial_confidence, "selected_cameras": [], "tool_calls": [], "evidence": [], "final_confidence": initial_confidence, "decision": None, "iteration_count": 0, "limits": {"max_additional_cameras": MAX_ADDITIONAL_CAMERAS, "max_agent_iterations": MAX_AGENT_ITERATIONS}}
    result = GRAPH.invoke({"initial_confidence": initial_confidence, "primary_camera_id": primary_camera_id, "location": location, "scenario": scenario, "tool_calls": [], "evidence": [], "iteration_count": 0})
    return {"triggered": True, "initial_confidence": initial_confidence, "selected_cameras": result.get("selected_cameras", []), "tool_calls": result.get("tool_calls", []), "evidence": result.get("evidence", []), "final_confidence": result["final_confidence"], "decision": result["decision"], "iteration_count": min(result.get("iteration_count", 1), MAX_AGENT_ITERATIONS), "limits": {"max_additional_cameras": MAX_ADDITIONAL_CAMERAS, "max_agent_iterations": MAX_AGENT_ITERATIONS}}
