"""P1-C service regression: real runtime composition with provider transport mocked."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from database import connection
from demo_v1 import service
from perception import qwen
from perception.multiview import autonomous
from perception.yolo import RealInferenceError


def raw_review(*, sufficient: bool, confidence: float, ambiguity: str = "none") -> dict:
    return {
        "need_action": True, "event_type": "liquid", "confidence": confidence,
        "evidence_sufficient": sufficient, "ambiguity_type": ambiguity, "severity": "high",
        "surface_type": "tile", "interference_factors": [ambiguity] if ambiguity != "none" else [],
        "evidence_summary": "固定摄像头画面中的地面区域已完成结构化视觉判断。",
        "recommended_capabilities": ["wet_cleaning", "strong_suction"],
    }


def tool_call(name: str, arguments: dict, call_id: str) -> dict:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


class CloudTransport:
    """The sole fake: it replaces the existing Qwen HTTP boundary, never runtime logic."""

    def __init__(self, first: dict, final: dict, second: dict | None = None, tool_responses: list[dict] | None = None):
        self.first = first
        self.final = final
        self.second = second
        self.semantic_calls = 0
        self.tool_calls = 0
        self.tool_images: list[int] = []
        self.semantic_contents: list[list[dict]] = []
        self._tool_responses = deepcopy(tool_responses) if tool_responses is not None else [
            {"role": "assistant", "tool_calls": [tool_call("find_supporting_cameras", {}, "search-1")]},
            {"role": "assistant", "tool_calls": [tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "fetch-2")]},
            {"role": "assistant", "tool_calls": [tool_call("finish_visual_judgment", final, "finish-1")]},
        ]

    @staticmethod
    def _image_count(messages: list[dict]) -> int:
        return sum(
            1 for message in messages for item in (message.get("content") if isinstance(message.get("content"), list) else [])
            if isinstance(item, dict) and item.get("type") == "image_url"
        )

    def __call__(self, content, model, *, messages=None, tools=None):
        if tools is not None:
            self.tool_calls += 1
            self.tool_images.append(self._image_count(messages))
            return self._tool_responses.pop(0), 47
        self.semantic_calls += 1
        self.semantic_contents.append(deepcopy(content))
        response = self.first if self.semantic_calls == 1 else self.second
        if response is None:
            raise AssertionError("unexpected independent second review")
        return response, 73


class P1CPipelineTests(unittest.TestCase):
    def test_agent_prompt_or_tool_contract_change_invalidates_replay(self):
        self._run_live(raw_review(sufficient=False, confidence=.15, ambiguity="reflection"),
                       raw_review(sufficient=True, confidence=.95))
        for field in ("system_prompt", "tools", "max_rounds"):
            with self.subTest(field=field):
                changed = service.acquisition_contract()
                changed[field] = "changed-contract"
                event_id = self._event_at_edge("STABLE_REPLAY")
                with patch.object(service, "acquisition_contract", return_value=changed), patch.object(qwen, "_request_qwen") as transport:
                    result = service.cloud_review(event_id)
                self.assertEqual(result["state"], "HUMAN_REVIEW")
                self.assertEqual(result["error"]["code"], "replay_record_unavailable")
                transport.assert_not_called()

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.original_database = connection.DATABASE_PATH
        connection.DATABASE_PATH = Path(self.temp.name) / "p1c.sqlite"
        connection.initialize_database()
        self.runtime_patch = patch.object(service, "get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen3-vl-plus"))
        self.agent_model_patch = patch.object(service, "get_agent_model", return_value="qwen3-vl-plus")
        self.runtime_patch.start()
        self.agent_model_patch.start()

    def tearDown(self):
        self.agent_model_patch.stop()
        self.runtime_patch.stop()
        connection.DATABASE_PATH = self.original_database
        self.temp.cleanup()

    def _event_at_edge(self, mode: str = "LIVE") -> str:
        event_id = service.create_demo_event("demo02", mode)["event_id"]
        service.edge_review(event_id)
        return event_id

    def _run_live(self, first: dict, final: dict, second: dict | None = None, tool_responses: list[dict] | None = None) -> tuple[dict, CloudTransport]:
        transport = CloudTransport(first, final, second, tool_responses)
        with patch.object(qwen, "_request_qwen", side_effect=transport):
            result = service.cloud_review(self._event_at_edge())
        return result, transport

    def test_low_confidence_insufficiency_runs_model_coverage_fetch_and_final_high_judgment(self):
        result, transport = self._run_live(
            raw_review(sufficient=False, confidence=0.12, ambiguity="reflection"),
            raw_review(sufficient=True, confidence=0.91),
        )
        self.assertEqual(result["state"], "CLOUD_REVIEW")
        self.assertEqual(result["first_qwen_review"]["evidence_sufficient"], False)
        self.assertEqual(result["multi_view"]["selected_cameras"], ["CAM-A1-02"])
        self.assertEqual(transport.tool_calls, 3)
        self.assertEqual(transport.tool_images, [1, 1, 2], "supporting image is not sent until the model fetches it")
        audit = result["multi_view"]["audit"]
        model_audit = [item for item in audit if item["source"] == "MODEL_TOOL_CALL"]
        self.assertEqual([item["name"] for item in model_audit], ["find_supporting_cameras", "fetch_camera_evidence", "finish_visual_judgment"])
        self.assertTrue(all(item["model_source"] == "LIVE_MODEL" for item in model_audit))
        self.assertTrue(all(isinstance(item.get("timestamp"), str) and item["timestamp"].endswith("+00:00") for item in audit))
        self.assertEqual([item["name"] for item in audit if item["source"] == "AGENT_RUNTIME"], ["agent_start"])
        self.assertGreater(model_audit[0]["candidate_count"], 0)

    def test_gray_final_runs_independent_second_review_after_legal_acquisition(self):
        first = raw_review(sufficient=False, confidence=0.2, ambiguity="occlusion")
        first["evidence_summary"] = "FIRST_SECRET: 单视角只能看到反光区域。"
        final = raw_review(sufficient=True, confidence=0.70)
        final["evidence_summary"] = "FINAL_SECRET: 合法补充视角完成确认。"
        result, transport = self._run_live(
            first,
            final,
            raw_review(sufficient=True, confidence=0.95),
        )
        self.assertEqual(result["state"], "CLOUD_REVIEW")
        self.assertEqual(transport.semantic_calls, 2, "the gray final review must receive an independent second cloud review")
        self.assertEqual(result["second_qwen_review"]["decision_confidence"], 0.95)
        self.assertEqual(result["multi_view"]["final_confidence"], 0.95)
        independent_request = json.dumps(transport.semantic_contents[1], ensure_ascii=False)
        self.assertNotIn("FIRST_SECRET", independent_request)
        self.assertNotIn("FINAL_SECRET", independent_request)
        self.assertEqual(sum(item.get("type") == "image_url" for item in transport.semantic_contents[1]), 2)
        self.assertIn("CAM-A1-01", independent_request)
        self.assertIn("CAM-A1-02", independent_request)

    def test_sufficient_final_below_half_does_not_second_review_and_is_human_review(self):
        result, transport = self._run_live(
            raw_review(sufficient=False, confidence=0.1, ambiguity="reflection"),
            raw_review(sufficient=True, confidence=0.49),
        )
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertEqual(result["error"]["code"], "final_evidence_or_confidence_gate")
        self.assertEqual(transport.semantic_calls, 1, "confidence < .50 must not invoke independent second review")

    def test_insufficient_final_with_high_raw_confidence_is_human_review(self):
        result, transport = self._run_live(
            raw_review(sufficient=False, confidence=0.1, ambiguity="reflection"),
            raw_review(sufficient=False, confidence=0.98, ambiguity="reflection"),
        )
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertEqual(result["error"]["code"], "final_evidence_insufficient")
        self.assertEqual(transport.semantic_calls, 1)

    def test_missing_legal_supporting_evidence_fails_human_review_without_tool_transport(self):
        transport = CloudTransport(raw_review(sufficient=False, confidence=0.1, ambiguity="reflection"), raw_review(sufficient=True, confidence=0.91))
        event_id = self._event_at_edge()
        stored = connection.get_event(event_id)
        stored["demo_v1"]["asset_manifest"]["assets"] = [asset for asset in stored["demo_v1"]["asset_manifest"]["assets"] if asset["role"] != "evidence"]
        connection.save_event(stored)
        with patch.object(qwen, "_request_qwen", side_effect=transport):
            result = service.cloud_review(event_id)
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertEqual(result["error"]["code"], "no_legal_supporting_camera")
        self.assertEqual(transport.tool_calls, 0)

    def test_replay_reuses_only_recorded_messages_and_reexecutes_coverage_fetch(self):
        live, _transport = self._run_live(
            raw_review(sufficient=False, confidence=0.15, ambiguity="perspective"),
            raw_review(sufficient=True, confidence=0.92),
        )
        replay_event = self._event_at_edge("STABLE_REPLAY")
        with patch.object(qwen, "_request_qwen", side_effect=AssertionError("Stable Replay must not call cloud transport")), \
                patch.object(autonomous, "find_supporting_cameras", wraps=autonomous.find_supporting_cameras) as coverage:
            replay = service.cloud_review(replay_event)
        self.assertEqual(live["state"], "CLOUD_REVIEW")
        self.assertEqual(replay["state"], "CLOUD_REVIEW")
        self.assertGreaterEqual(coverage.call_count, 2, "Replay must rerun coverage gate and model-selected tool handling")
        self.assertEqual(replay["multi_view"]["selected_cameras"], ["CAM-A1-02"])
        audit = [item for item in replay["multi_view"]["audit"] if item["source"] == "MODEL_TOOL_CALL"]
        self.assertTrue(all(item["model_source"] == "REPLAY" and item["elapsed_ms"] is None and item["historical_elapsed_ms"] == 47 for item in audit))

    def test_tool_budget_enforces_two_unique_cameras_and_two_rounds(self):
        final = raw_review(sufficient=True, confidence=0.92)
        tool_responses = [
            {"role": "assistant", "tool_calls": [tool_call("find_supporting_cameras", {}, "search-1")]},
            {"role": "assistant", "tool_calls": [tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "fetch-2")]},
            {"role": "assistant", "tool_calls": [tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-04"}, "fetch-4")]},
            {"role": "assistant", "tool_calls": [tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "over-budget")]},
            {"role": "assistant", "tool_calls": [tool_call("finish_visual_judgment", final, "finish-1")]},
        ]
        result, transport = self._run_live(
            raw_review(sufficient=False, confidence=0.1, ambiguity="perspective"), final,
            tool_responses=tool_responses,
        )
        self.assertEqual(result["state"], "CLOUD_REVIEW")
        self.assertEqual(result["multi_view"]["selected_cameras"], ["CAM-A1-02", "CAM-A1-04"])
        self.assertEqual(result["multi_view"]["iteration_count"], 2)
        self.assertEqual(transport.tool_calls, 5)
        rejects = [item for item in result["multi_view"]["audit"] if item.get("status") == "REJECTED"]
        self.assertEqual(rejects[-1]["reason"], "acquisition_round_limit")

    def test_duplicate_tool_and_malformed_finish_fail_safe_without_uncaught_error(self):
        duplicate = [
            {"role": "assistant", "tool_calls": [tool_call("find_supporting_cameras", {}, "search-1")]},
            {"role": "assistant", "tool_calls": [tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "fetch-2")]},
            {"role": "assistant", "tool_calls": [tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "duplicate-2")]},
            {"role": "assistant", "tool_calls": [tool_call("finish_visual_judgment", raw_review(sufficient=True, confidence=0.91), "finish-1")]},
        ]
        duplicate_result, _ = self._run_live(
            raw_review(sufficient=False, confidence=0.1, ambiguity="occlusion"), raw_review(sufficient=True, confidence=0.91),
            tool_responses=duplicate,
        )
        self.assertEqual(duplicate_result["state"], "CLOUD_REVIEW")
        self.assertIn("duplicate_camera", [item.get("reason") for item in duplicate_result["multi_view"]["audit"]])

        malformed = [
            {"role": "assistant", "tool_calls": [tool_call("find_supporting_cameras", {}, "search-1")]},
            {"role": "assistant", "tool_calls": [tool_call("finish_visual_judgment", {}, "bad-finish")]},
        ]
        malformed_result, _ = self._run_live(
            raw_review(sufficient=False, confidence=0.1, ambiguity="occlusion"), raw_review(sufficient=True, confidence=0.91),
            tool_responses=malformed,
        )
        self.assertEqual(malformed_result["state"], "HUMAN_REVIEW")
        self.assertEqual(malformed_result["error"]["code"], "final_schema_invalid")

    def test_live_visual_judgment_requires_exact_canonical_fields_and_projection_only_unwraps_storage_envelope(self):
        canonical = raw_review(sufficient=True, confidence=0.91)
        required = set(qwen.VISUAL_JUDGMENT_SCHEMA["required"])
        self.assertEqual(set(canonical), set(qwen.VISUAL_JUDGMENT_SCHEMA["properties"]))
        for field in required:
            with self.subTest(missing=field), self.assertRaises(RealInferenceError):
                qwen.parse_visual_judgment({key: value for key, value in canonical.items() if key != field}, "qwen3-vl-plus", 1, 1)
        with self.assertRaises(RealInferenceError):
            qwen.parse_visual_judgment({**canonical, "unknown_extra": True}, "qwen3-vl-plus", 1, 1)
        with self.assertRaises(RealInferenceError):
            qwen.parse_visual_judgment({**canonical, "need_action": "true"}, "qwen3-vl-plus", 1, 1)
        with self.assertRaises(RealInferenceError):
            qwen.parse_visual_judgment({**canonical, "confidence": float("nan")}, "qwen3-vl-plus", 1, 1)
        envelope = qwen.parse_visual_judgment(canonical, "qwen3-vl-plus", 1, 1)
        with self.assertRaises(RealInferenceError):
            qwen.parse_visual_judgment(envelope, "qwen3-vl-plus", 1, 1)
        projected = qwen.parse_visual_judgment(envelope, "qwen3-vl-plus", 1, 1, projection=True)
        self.assertEqual(projected["need_action"], True)

    def test_invalid_provider_live_schema_stops_at_human_review_without_assignment(self):
        invalid = {**raw_review(sufficient=True, confidence=0.91), "need_action": "true"}
        transport = CloudTransport(invalid, raw_review(sufficient=True, confidence=0.91))
        with patch.object(qwen, "_request_qwen", side_effect=transport):
            result = service.cloud_review(self._event_at_edge())
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertEqual(result["error"]["code"], "cloud_error")
        self.assertIsNone(result["assignment_decision"])

    def test_fusion_counts_only_successful_legal_fetched_evidence(self):
        review = {"decision_confidence": 0.90}
        evidence = [{"class_name": "liquid"}]

        def multi(*, fetched: list[str], assets: list[str], sufficient: bool = True, image_count: int = 2, status: str = "OK"):
            return {
                "audit": [{"name": "fetch_camera_evidence", "status": status, "arguments": {"camera_id": camera}} for camera in fetched],
                "evidence_assets": [{"camera_id": camera} for camera in assets],
                "review": {"evidence_sufficient": sufficient, "image_count": image_count},
            }

        one = service._fusion_score(review, evidence, multi(fetched=["CAM-A1-02"], assets=["CAM-A1-02"]))
        two = service._fusion_score(review, evidence, multi(fetched=["CAM-A1-02", "CAM-A1-04"], assets=["CAM-A1-02", "CAM-A1-04"]))
        self.assertEqual(one["components"]["multi_view_consistency"], 1.0)
        self.assertEqual(two["components"]["multi_view_consistency"], 1.0)
        for name, value in {
            "search_only": {"audit": [{"name": "find_supporting_cameras", "status": "OK", "candidates": [{"camera_id": "CAM-A1-02"}]}], "evidence_assets": [{"camera_id": "CAM-A1-02"}], "review": {"evidence_sufficient": True, "image_count": 2}},
            "failed_fetch": multi(fetched=["CAM-A1-02"], assets=["CAM-A1-02"], status="FAILED"),
            "insufficient": multi(fetched=["CAM-A1-02"], assets=["CAM-A1-02"], sufficient=False),
            "metadata_only": multi(fetched=["CAM-A1-02"], assets=["CAM-A1-04"]),
        }.items():
            with self.subTest(negative=name):
                score = service._fusion_score(review, evidence, value)
                self.assertEqual(score["components"]["multi_view_consistency"], 0.0)

    def test_malformed_tool_call_lists_fail_safe_without_uncaught_exception(self):
        malformed_cases = {
            "none": [None],
            "empty": [],
            "duplicate_ids": [tool_call("find_supporting_cameras", {}, "same"), tool_call("fetch_camera_evidence", {"camera_id": "CAM-A1-02"}, "same")],
            "too_many": [
                tool_call("find_supporting_cameras", {}, "one"),
                tool_call("find_supporting_cameras", {}, "two"),
                tool_call("find_supporting_cameras", {}, "three"),
            ],
        }
        for name, calls in malformed_cases.items():
            with self.subTest(case=name):
                result, _ = self._run_live(
                    raw_review(sufficient=False, confidence=0.1, ambiguity="reflection"), raw_review(sufficient=True, confidence=0.91),
                    tool_responses=[{"role": "assistant", "tool_calls": calls}],
                )
                self.assertEqual(result["state"], "HUMAN_REVIEW")
                self.assertEqual(result["error"]["code"], "invalid_model_tool_calls")


if __name__ == "__main__":
    unittest.main()
