"""Scenario 02 workbench adapter; it does not reimplement perception or dispatch rules."""

from __future__ import annotations

import json
from pathlib import Path

from perception.service import analyze_mock_case
from workflow.engine import run_scenario_02


ASSET_ROOT = Path(__file__).resolve().parents[2] / "sample_data" / "camera_events"
SCENARIO_02_EVENT_ID = "event-beverage-spill-002"
SCENARIO_02_ASSETS = [
    ("CAM-A1-01", "primary.jpg", "主视角"),
    ("CAM-A1-02", "secondary.jpg", "补充视角"),
    ("CAM-A1-03", "secondary.jpg", "补充视角"),
    ("CAM-A1-01", "after.jpg", "清洁后"),
]


def _asset_item(camera_id: str, filename: str, label: str) -> dict:
    path = ASSET_ROOT / camera_id / SCENARIO_02_EVENT_ID / filename
    return {"camera_id": camera_id, "event_id": SCENARIO_02_EVENT_ID, "filename": filename, "label": label, "available": path.is_file(), "url": f"/demo-assets/{camera_id}/{SCENARIO_02_EVENT_ID}/{filename}" if path.is_file() else None}


def scenario_02_assets() -> dict:
    metadata_path = ASSET_ROOT / "CAM-A1-01" / SCENARIO_02_EVENT_ID / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else None
    assets = [_asset_item(*asset) for asset in SCENARIO_02_ASSETS]
    return {"event_id": SCENARIO_02_EVENT_ID, "metadata": metadata, "assets": assets, "missing_assets": [asset["filename"] for asset in assets if not asset["available"]]}


def run_scenario_02_workbench() -> dict:
    """Compose existing Phase 4 perception and Phase 5/3 workflow results for the UI."""
    initial_ai_result = analyze_mock_case("low_confidence_milk_tea_spill")
    workflow_event = run_scenario_02()
    return {"asset_manifest": scenario_02_assets(), "initial_ai_result": initial_ai_result, "workflow_event": workflow_event, "multi_view": workflow_event["multi_view_trace"]}
