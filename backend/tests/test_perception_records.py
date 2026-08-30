"""P1-C perception-record persistence and safe ReplayFeed tests."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from database import connection
from demo_v1.perception_records import PIPELINE_SCHEMA, RecordedToolTurns, load_perception_record, save_perception_record
from perception.qwen import VISUAL_JUDGMENT_SCHEMA
from perception.yolo import RealInferenceError


def judgment(*, sufficient: bool, confidence: float = 0.91) -> dict:
    return {
        "provider": "DashScope Qwen-VL", "model": "qwen3-vl-plus", "source": "LIVE_MODEL", "image_count": 2,
        "elapsed_ms": 123, "need_action": True, "need_clean": True, "event_type": "liquid",
        "confidence": confidence, "decision_confidence": confidence, "evidence_sufficient": sufficient,
        "ambiguity_type": "none", "severity": "high", "surface_type": "tile", "interference_factors": [],
        "evidence_summary": "固定摄像头受控证据显示地面液体区域，结构化结论已完成。",
        "recommended_capabilities": ["wet_cleaning"], "next_action": "dispatch_robot",
    }


def canonical_judgment() -> dict:
    review = judgment(sufficient=True)
    return {key: review[key] for key in VISUAL_JUDGMENT_SCHEMA["properties"]}


def turn(number: int, name: str, arguments: dict) -> dict:
    return {
        "turn": number, "source": "LIVE_MODEL", "elapsed_ms": 21, "historical_elapsed_ms": None, "role": "assistant",
        "tool_calls": [{"id": f"call-{number}", "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}],
    }


class PerceptionRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.previous_database = connection.DATABASE_PATH
        connection.DATABASE_PATH = Path(self.temp.name) / "records.sqlite"
        connection.initialize_database()
        self.live = {"event_id": "live-record-event", "state": "CLOUD_REVIEW", "demo_v1": {"mode": "LIVE", "source_event_id": "event-beverage-spill-002"}}
        self.replay = {"event_id": "replay-record-event", "state": "EDGE_DETECTED", "demo_v1": {"mode": "STABLE_REPLAY", "source_event_id": "event-beverage-spill-002"}}
        connection.save_event(self.live)
        connection.save_event(self.replay)

    def tearDown(self):
        connection.DATABASE_PATH = self.previous_database
        self.temp.cleanup()

    def _turns(self) -> list[dict]:
        return [
            turn(1, "find_supporting_cameras", {}),
            turn(2, "fetch_camera_evidence", {"camera_id": "CAM-A1-02"}),
            turn(3, "finish_visual_judgment", canonical_judgment()),
        ]

    def test_valid_live_record_loads_as_replay_only_for_matching_event_and_evidence_key(self):
        save_perception_record(self.live, "evidence-key-1", judgment(sufficient=False, confidence=0.61), judgment(sufficient=True), None, self._turns())

        replay = load_perception_record(self.replay, "evidence-key-1")

        self.assertEqual(replay["event_id"], self.live["event_id"])
        self.assertEqual(replay["source_event_id"], self.live["demo_v1"]["source_event_id"])
        self.assertEqual(replay["responses"]["final"]["source"], "REPLAY")
        self.assertIsNone(replay["responses"]["final"]["elapsed_ms"])
        self.assertEqual(replay["responses"]["final"]["historical_elapsed_ms"], 123)
        with self.assertRaises(RealInferenceError):
            load_perception_record(self.replay, "different-evidence-key")

    def test_bad_or_unsafe_record_is_rejected_without_becoming_replay(self):
        unsafe = self._turns()
        unsafe[0]["reasoning_content"] = "do not persist"
        with self.assertRaises(RealInferenceError):
            save_perception_record(self.live, "unsafe-key", judgment(sufficient=False), judgment(sufficient=True), None, unsafe)

        malformed_bundle = {
            "schema": PIPELINE_SCHEMA, "evidence_key": "malformed-key", "event_id": self.live["event_id"],
            "source_event_id": self.live["demo_v1"]["source_event_id"],
            "responses": {"first": judgment(sufficient=False), "final": judgment(sufficient=True), "second": None},
            "model_turns": [{"turn": 1, "source": "LIVE_MODEL", "elapsed_ms": 1, "historical_elapsed_ms": None, "role": "assistant", "content": "not-json"}],
        }
        connection.save_model_record(self.live["demo_v1"]["source_event_id"], "event_review", "LIVE", malformed_bundle)
        with self.assertRaises(RealInferenceError):
            load_perception_record(self.replay, "malformed-key")

    def test_recorded_tool_turns_replays_the_actual_openai_assistant_message_shape(self):
        feed = RecordedToolTurns(self._turns())
        coverage, elapsed = feed([], [], "qwen3-vl-plus")
        fetch, _ = feed([], [], "qwen3-vl-plus")
        finish, _ = feed([], [], "qwen3-vl-plus")

        self.assertEqual(elapsed, 21)
        self.assertEqual(coverage, {"role": "assistant", "tool_calls": [self._turns()[0]["tool_calls"][0]]})
        self.assertEqual(fetch["tool_calls"][0]["function"]["arguments"], '{"camera_id": "CAM-A1-02"}')
        self.assertEqual(finish["tool_calls"][0]["function"]["name"], "finish_visual_judgment")
        feed.assert_consumed()


if __name__ == "__main__":
    unittest.main()
