"""The only three tools available to the Multi-view Perception Agent."""

from __future__ import annotations

from typing import Any

from spatial.spatial_data import CAMERAS


SCENARIO_02_EVIDENCE = {
    "CAM-A1-02": {"frame_id": "mv-a1-02-001", "captured_at": "2026-08-26T10:00:01+08:00", "sync_offset_ms": 180, "evidence": "wet reflective patch adjacent to beverage cup", "confidence": 0.90},
    "CAM-A1-03": {"frame_id": "mv-a1-03-001", "captured_at": "2026-08-26T10:00:01+08:00", "sync_offset_ms": 240, "evidence": "spreading liquid boundary on tiled lobby floor", "confidence": 0.92},
}


def _contains(point: dict[str, float], polygon: list[dict[str, float]]) -> bool:
    """Small ray-cast helper over the Phase 2 coverage polygons; no new map model."""
    x, y = point["x"], point["y"]
    inside = False
    previous = polygon[-1]
    for current in polygon:
        intersects = (current["y"] > y) != (previous["y"] > y) and x < (previous["x"] - current["x"]) * (y - current["y"]) / (previous["y"] - current["y"]) + current["x"]
        if intersects:
            inside = not inside
        previous = current
    return inside


def camera_coverage_tool(location: dict[str, Any], primary_camera_id: str, limit: int) -> dict[str, Any]:
    """Use existing Phase 2 Camera Coverage metadata to select valid extra views."""
    candidates = []
    for camera in CAMERAS:
        if camera["camera_id"] == primary_camera_id or camera["map_id"] != location["map_id"]:
            continue
        if _contains(location, camera["coverage_polygon"]):
            candidates.append({"camera_id": camera["camera_id"], "name": camera["name"], "map_id": camera["map_id"], "zone": camera["zone"], "selection_basis": "same-map coverage polygon contains initial SLAM target"})
    return {"tool": "Camera Coverage Tool", "primary_camera_id": primary_camera_id, "selected_cameras": candidates[:limit], "candidate_count": len(candidates)}


def frame_fetch_tool(camera_id: str, scenario: str) -> dict[str, Any]:
    """Fetch a near-synchronous frame reference. Mock frame facts are explicit for demo stability."""
    fixture = SCENARIO_02_EVIDENCE.get(camera_id, {}) if scenario == "scenario02" else {}
    return {"tool": "Frame Fetch Tool", "camera_id": camera_id, "frame_id": fixture.get("frame_id", f"mock-{camera_id.lower()}"), "captured_at": fixture.get("captured_at", "2026-08-26T10:00:01+08:00"), "sync_offset_ms": fixture.get("sync_offset_ms", 0), "evidence": fixture.get("evidence", "No reliable visual evidence."), "confidence": fixture.get("confidence", 0.0), "mode": "mock"}


def vlm_tool(frames: list[dict[str, Any]], scenario: str) -> dict[str, Any]:
    """Produce bounded visual evidence, not hidden reasoning or device commands."""
    if scenario == "scenario02" and len(frames) >= 2:
        return {"tool": "VLM Tool", "need_clean": True, "confidence": 0.92, "summary": "Two synchronized views corroborate a large beverage liquid spill on tile.", "evidence": [{"camera_id": frame["camera_id"], "frame_id": frame["frame_id"], "observation": frame["evidence"], "confidence": frame["confidence"]} for frame in frames]}
    return {"tool": "VLM Tool", "need_clean": False, "confidence": 0.48, "summary": "Available additional views do not provide enough reliable visual evidence.", "evidence": [{"camera_id": frame["camera_id"], "frame_id": frame["frame_id"], "observation": frame["evidence"], "confidence": frame["confidence"]} for frame in frames]}
