"""P1-C bounded autonomous multi-view acquisition tests.

All model turns are injected fixtures. They exercise policy and tool boundaries
without providing a runtime fallback or sending any request to a provider.
"""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from typing import Any

from perception.multiview.autonomous import run_autonomous_acquisition


LOCATION = {
    "building": "A", "floor": "1F", "zone": "Main Lobby", "map_id": "A_1F", "x": 29.5, "y": 27.0,
}
PRIMARY = {"camera_id": "CAM-A1-01", "event_id": "event-beverage-spill-002", "filename": "before.png", "role": "before"}
SUPPORTING = [
    {"camera_id": "CAM-A1-02", "event_id": "event-beverage-spill-002", "filename": "view-02.png", "role": "evidence", "source": "CONTROLLED_EVIDENCE"},
    {"camera_id": "CAM-A1-04", "event_id": "event-beverage-spill-002", "filename": "view-04.png", "role": "evidence", "source": "CONTROLLED_EVIDENCE"},
]


def judgment(*, sufficient: bool, need_action: bool = True, ambiguity: str = "none", confidence: float = 0.9) -> dict[str, Any]:
    return {
        "need_action": need_action,
        "event_type": "liquid",
        "confidence": confidence,
        "evidence_sufficient": sufficient,
        "ambiguity_type": ambiguity,
        "severity": "high",
        "surface_type": "tile",
        "interference_factors": ["reflection"] if ambiguity != "none" else [],
        "evidence_summary": "固定摄像头画面显示地面区域，已按可用视角完成结构化判断。",
        "recommended_capabilities": ["wet_cleaning", "strong_suction"],
    }


def tool_call(name: str, arguments: dict[str, Any], call_id: str) -> dict[str, Any]:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


class FixtureTransport:
    def __init__(self, responses: list[dict[str, Any]]):
        self.responses = list(responses)
        self.requests: list[tuple[list[dict[str, Any]], list[dict[str, Any]], str]] = []

    def __call__(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str) -> tuple[dict[str, Any], int]:
        self.requests.append((copy.deepcopy(messages), copy.deepcopy(tools), model))
        if not self.responses:
            raise AssertionError("unexpected model turn")
        return self.responses.pop(0), 321


def image_count(messages: list[dict[str, Any]]) -> int:
    count = 0
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            count += sum(1 for item in content if isinstance(item, dict) and item.get("type") == "image_url")
    return count


class AutonomousMultiViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.image = Path(self.temp.name) / "frame.png"
        # Minimal valid PNG header is sufficient because the production code
        # treats assets as opaque bytes before a provider consumes them.
        self.image.write_bytes(b"\x89PNG\r\n\x1a\nfixture")

    def tearDown(self):
        self.temp.cleanup()

    def _resolve(self, asset: dict[str, Any]) -> Path:
        self.assertEqual(asset["role"], "evidence")
        return self.image

    def test_model_autonomously_finds_then_fetches_two_legal_views_and_finishes(self):
        transport = FixtureTransport([
            {"role": "assistant", "tool_calls": [tool_call("find_supporting_cameras", {}, "search-1")]},
            {"role": "assistant", "tool_calls": [
                tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "fetch-2"),
                tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-04"}, "fetch-4"),
            ]},
            {"role": "assistant", "tool_calls": [tool_call("finish_visual_judgment", judgment(sufficient=True), "finish-1")]},
        ])
        callback: list[dict[str, Any]] = []

        result = run_autonomous_acquisition(
            initial_review=judgment(sufficient=False, ambiguity="reflection", confidence=0.12),
            primary_asset=PRIMARY, primary_path=self.image, location=LOCATION, supporting_assets=SUPPORTING,
            model="qwen3-vl-plus", resolve_asset=self._resolve, on_audit=callback.append, request_turn=transport,
        )

        self.assertEqual(result["decision"], "CONFIRM")
        self.assertEqual(result["selected_cameras"], ["CAM-A1-02", "CAM-A1-04"])
        self.assertEqual(result["iteration_count"], 1)
        self.assertEqual(len(result["model_turns"]), 3)
        self.assertEqual(result["model_turns"][0]["tool_calls"][0]["function"]["name"], "find_supporting_cameras")
        self.assertEqual(result["model_turns"][-1]["tool_calls"][0]["function"]["name"], "finish_visual_judgment")
        self.assertEqual(result["review"]["need_clean"], result["review"]["need_action"])
        self.assertEqual(result["review"]["decision_confidence"], result["review"]["confidence"])
        self.assertEqual(image_count(transport.requests[0][0]), 1, "the first model turn receives only the primary image")
        self.assertEqual(image_count(transport.requests[2][0]), 3, "fetched images are appended only after model-selected fetches")
        self.assertEqual({item["function"]["name"] for item in transport.requests[0][1]}, {"find_supporting_cameras", "fetch_camera_evidence", "finish_visual_judgment"})
        self.assertTrue(all(item["source"] == "MODEL_TOOL_CALL" for item in result["audit"] if item["source"] == "MODEL_TOOL_CALL"))
        self.assertEqual(callback, result["audit"])
        self.assertNotIn("base64", repr(result["audit"]).lower())
        self.assertNotIn("data:image", repr(result["model_turns"]).lower())

    def test_sufficient_low_confidence_does_not_trigger_acquisition(self):
        def forbidden(*_args, **_kwargs):
            raise AssertionError("evidence-sufficient input must not call the Agent")

        result = run_autonomous_acquisition(
            initial_review=judgment(sufficient=True, confidence=0.01), primary_asset=PRIMARY, primary_path=self.image,
            location=LOCATION, supporting_assets=SUPPORTING, model="qwen3-vl-plus", resolve_asset=self._resolve,
            request_turn=forbidden,
        )
        self.assertEqual(result["decision"], "HUMAN_REVIEW")
        self.assertEqual(result["iteration_count"], 0)
        self.assertEqual(result["audit"][0]["status"], "NOT_TRIGGERED")

    def test_unauthorised_fetch_is_rejected_and_never_loads_an_image(self):
        transport = FixtureTransport([
            {"role": "assistant", "tool_calls": [tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "bad-fetch")]},
            {"role": "assistant", "content": "not structured JSON"},
        ])
        result = run_autonomous_acquisition(
            initial_review=judgment(sufficient=False, ambiguity="occlusion"), primary_asset=PRIMARY, primary_path=self.image,
            location=LOCATION, supporting_assets=SUPPORTING, model="qwen3-vl-plus", resolve_asset=lambda _asset: (_ for _ in ()).throw(AssertionError("must not fetch")),
            request_turn=transport,
        )
        self.assertEqual(result["decision"], "HUMAN_REVIEW")
        self.assertEqual(result["selected_cameras"], [])
        self.assertIn("model_did_not_finish", result["error"])
        self.assertTrue(any(item.get("reason") == "unauthorised_camera" for item in result["audit"]))

    def test_agent_cannot_turn_initial_insufficiency_into_auto_action_without_fetching_evidence(self):
        transport = FixtureTransport([
            {"role": "assistant", "tool_calls": [tool_call("find_supporting_cameras", {}, "search-1")]},
            {"role": "assistant", "tool_calls": [tool_call("finish_visual_judgment", judgment(sufficient=True), "finish-1")]},
        ])
        result = run_autonomous_acquisition(
            initial_review=judgment(sufficient=False, ambiguity="reflection"), primary_asset=PRIMARY, primary_path=self.image,
            location=LOCATION, supporting_assets=SUPPORTING, model="qwen3-vl-plus", resolve_asset=self._resolve,
            request_turn=transport,
        )
        self.assertEqual((result["decision"], result["error"]), ("HUMAN_REVIEW", "no_evidence_acquired"))

    def test_replay_revalidates_tools_with_historical_latency_not_live_latency(self):
        transport = FixtureTransport([
            {"role": "assistant", "tool_calls": [tool_call("find_supporting_cameras", {}, "search-1")]},
            {"role": "assistant", "tool_calls": [tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "fetch-2")]},
            {"role": "assistant", "content": __import__("json").dumps(judgment(sufficient=True))},
        ])
        result = run_autonomous_acquisition(
            initial_review=judgment(sufficient=False, ambiguity="perspective"), primary_asset=PRIMARY, primary_path=self.image,
            location=LOCATION, supporting_assets=SUPPORTING, model="qwen3-vl-plus", resolve_asset=self._resolve,
            request_turn=transport, response_source="REPLAY",
        )
        self.assertEqual(result["decision"], "CONFIRM")
        self.assertEqual(result["selected_cameras"], ["CAM-A1-02"])
        self.assertIn("content", result["model_turns"][-1], "normal JSON final replies remain replayable")
        self.assertTrue(all(turn["source"] == "REPLAY" and turn["elapsed_ms"] is None and turn["historical_elapsed_ms"] == 321 for turn in result["model_turns"]))
        tool_audit = [item for item in result["audit"] if item["source"] == "MODEL_TOOL_CALL"]
        self.assertTrue(all(item["model_source"] == "REPLAY" and item["elapsed_ms"] is None and item["historical_elapsed_ms"] == 321 for item in tool_audit))

    def test_no_legal_camera_or_unrecoverable_ambiguity_goes_to_human_review_without_transport(self):
        def forbidden(*_args, **_kwargs):
            raise AssertionError("policy should end before model transport")

        no_camera = run_autonomous_acquisition(
            initial_review=judgment(sufficient=False, ambiguity="reflection"), primary_asset=PRIMARY, primary_path=self.image,
            location=LOCATION, supporting_assets=[], model="qwen3-vl-plus", resolve_asset=self._resolve, request_turn=forbidden,
        )
        unrecoverable = run_autonomous_acquisition(
            initial_review=judgment(sufficient=False, ambiguity="other"), primary_asset=PRIMARY, primary_path=self.image,
            location=LOCATION, supporting_assets=SUPPORTING, model="qwen3-vl-plus", resolve_asset=self._resolve, request_turn=forbidden,
        )
        self.assertEqual((no_camera["decision"], no_camera["error"]), ("HUMAN_REVIEW", "no_legal_supporting_camera"))
        self.assertEqual((unrecoverable["decision"], unrecoverable["error"]), ("HUMAN_REVIEW", "unrecoverable_ambiguity"))


if __name__ == "__main__":
    unittest.main()
