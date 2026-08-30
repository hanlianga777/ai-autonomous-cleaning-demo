"""Opt-in P1-A LIVE → Stable Replay acceptance against the configured Qwen runtime.

This suite is intentionally skipped unless ``RUN_P1A_LIVE_ACCEPTANCE=1`` is
set.  It uses a temporary SQLite database, never reads a dotenv file directly,
and reports only state, confidence and record counts—never credentials, headers
or raw model content.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from database import connection
from database.connection import get_event, list_model_records, reset_fleet_state
from demo_v1.service import (
    SCENARIO_IDS,
    assign_event,
    cloud_review,
    complete_cleaning,
    complete_demo04_manual,
    complete_navigation,
    create_demo_event,
    edge_review,
    locate_event,
    start_navigation,
    verify_event,
)
from perception.config import get_runtime


RUN_LIVE_ACCEPTANCE = os.getenv("RUN_P1A_LIVE_ACCEPTANCE") == "1"


def _forbid_transport(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("Stable Replay must not invoke a cloud transport.")


@unittest.skipUnless(RUN_LIVE_ACCEPTANCE, "set RUN_P1A_LIVE_ACCEPTANCE=1 to run paid LIVE Qwen acceptance")
class P1ALiveAcceptanceTests(unittest.TestCase):
    """Run real stage functions; only the replay pass blocks network transports."""

    @classmethod
    def setUpClass(cls) -> None:
        runtime = get_runtime()
        if not runtime.qwen_ready:
            raise unittest.SkipTest("Qwen runtime is not configured for LIVE acceptance.")
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls._original_database_path = connection.DATABASE_PATH
        connection.DATABASE_PATH = os.path.join(cls._temporary_directory.name, "p1a-live-acceptance.db")
        connection.initialize_database()

    @classmethod
    def tearDownClass(cls) -> None:
        connection.DATABASE_PATH = cls._original_database_path
        cls._temporary_directory.cleanup()

    def setUp(self) -> None:
        reset_fleet_state()

    def _record_count(self, source_event_id: str, phase: str) -> int:
        return len(list_model_records(source_event_id, phase))

    def _require_cloud_pass(self, demo_id: str, reviewed: dict) -> None:
        """Fail with a compact, non-sensitive observation when LIVE does not pass."""
        if reviewed["state"] == "CLOUD_REVIEW":
            return
        decision = reviewed.get("qwen_review") or {}
        fusion = reviewed.get("evidence_fusion") or {}
        print(
            f"P1A LIVE {demo_id} cloud_gate_failed "
            f"state={reviewed['state']} "
            f"confidence={decision.get('decision_confidence', 'unavailable')} "
            f"event_type={decision.get('event_type', 'unavailable')} "
            f"fusion_score={fusion.get('score', 'unavailable')} "
            f"event_records={self._record_count(SCENARIO_IDS[demo_id], 'event_review')}"
        )
        self.fail(f"{demo_id} LIVE cloud gate did not reach CLOUD_REVIEW: {reviewed['state']}")

    def _run_autonomous_stages(self, demo_id: str, mode: str) -> dict:
        event_id = create_demo_event(demo_id, mode)["event_id"]
        self.assertEqual(edge_review(event_id)["state"], "EDGE_DETECTED")
        reviewed = cloud_review(event_id)
        self._require_cloud_pass(demo_id, reviewed)
        self.assertEqual(locate_event(event_id)["state"], "LOCATED")
        assigned = assign_event(event_id)
        self.assertEqual(assigned["state"], "ASSIGNED")
        self.assertEqual(start_navigation(event_id)["state"], "NAVIGATING")
        self.assertEqual(complete_navigation(event_id)["state"], "ARRIVED")
        self.assertEqual(complete_cleaning(event_id)["state"], "CLEANING_COMPLETED")
        closed = verify_event(event_id)
        self.assertEqual(closed["state"], "CLOSED")
        return closed

    def _run_demo04_human_stages(self, mode: str) -> dict:
        event_id = create_demo_event("demo04", mode)["event_id"]
        self.assertEqual(edge_review(event_id)["state"], "EDGE_DETECTED")
        reviewed = cloud_review(event_id)
        self._require_cloud_pass("demo04", reviewed)
        self.assertEqual(locate_event(event_id)["state"], "LOCATED")
        fallback = assign_event(event_id)
        self.assertEqual(fallback["state"], "HUMAN_FALLBACK")
        self.assertEqual(fallback["assignment_decision"]["candidate_count"], 0)
        self.assertIsNone(fallback["assignment_decision"]["selected_robot_id"])
        closed = complete_demo04_manual(event_id)
        self.assertEqual(closed["state"], "CLOSED")
        return closed

    def test_demo01_live_then_stable_replay_without_transport(self) -> None:
        """LIVE records must be replayed while deterministic stages execute again."""
        live = self._run_autonomous_stages("demo01", "LIVE")
        self.assertEqual(live["qwen_review"]["provider"], "DashScope Qwen-VL")
        self.assertEqual(live["verification"]["provider"], "DashScope Qwen-VL")
        self.assertGreaterEqual(self._record_count(SCENARIO_IDS["demo01"], "event_review"), 1)
        self.assertGreaterEqual(self._record_count(SCENARIO_IDS["demo01"], "verification"), 1)
        live_counts = (
            self._record_count(SCENARIO_IDS["demo01"], "event_review"),
            self._record_count(SCENARIO_IDS["demo01"], "verification"),
        )

        reset_fleet_state()
        with patch("demo_v1.service.run_event_qwen_vl", side_effect=_forbid_transport), patch(
            "demo_v1.service.run_targeted_event_qwen_vl", side_effect=_forbid_transport
        ), patch("demo_v1.service.run_verification_qwen_vl", side_effect=_forbid_transport):
            replay = self._run_autonomous_stages("demo01", "STABLE_REPLAY")

        self.assertEqual(replay["qwen_review"]["source_badge"], "REPLAY")
        self.assertEqual(replay["verification"]["source_badge"], "REPLAY")
        self.assertEqual(
            (
                self._record_count(SCENARIO_IDS["demo01"], "event_review"),
                self._record_count(SCENARIO_IDS["demo01"], "verification"),
            ),
            live_counts,
        )
        persisted = get_event(replay["event_id"])
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted["state"], "CLOSED")
        print(
            "P1A LIVE demo01 "
            f"cloud_confidence={live['qwen_review']['decision_confidence']:.4f} "
            f"verification_confidence={live['verification']['confidence']:.4f} "
            f"records=event:{live_counts[0]},verification:{live_counts[1]}"
        )

    def test_demo04_live_human_closure_then_stable_replay_zero_candidate(self) -> None:
        """Human fallback remains a capability result in both LIVE and Replay."""
        live = self._run_demo04_human_stages("LIVE")
        self.assertEqual(live["qwen_review"]["provider"], "DashScope Qwen-VL")
        self.assertEqual(live["verification"]["provider"], "DashScope Qwen-VL")
        self.assertGreaterEqual(self._record_count(SCENARIO_IDS["demo04"], "event_review"), 1)
        self.assertGreaterEqual(self._record_count(SCENARIO_IDS["demo04"], "verification"), 1)
        live_counts = (
            self._record_count(SCENARIO_IDS["demo04"], "event_review"),
            self._record_count(SCENARIO_IDS["demo04"], "verification"),
        )

        reset_fleet_state()
        with patch("demo_v1.service.run_event_qwen_vl", side_effect=_forbid_transport), patch(
            "demo_v1.service.run_targeted_event_qwen_vl", side_effect=_forbid_transport
        ), patch("demo_v1.service.run_verification_qwen_vl", side_effect=_forbid_transport):
            replay = self._run_demo04_human_stages("STABLE_REPLAY")

        self.assertEqual(replay["qwen_review"]["source_badge"], "REPLAY")
        self.assertEqual(replay["verification"]["source_badge"], "REPLAY")
        self.assertEqual(replay["assignment_decision"]["candidate_count"], 0)
        self.assertIsNone(replay["assignment_decision"]["selected_robot_id"])
        self.assertEqual(
            (
                self._record_count(SCENARIO_IDS["demo04"], "event_review"),
                self._record_count(SCENARIO_IDS["demo04"], "verification"),
            ),
            live_counts,
        )
        persisted = get_event(replay["event_id"])
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted["state"], "CLOSED")
        print(
            "P1A LIVE demo04 "
            f"cloud_confidence={live['qwen_review']['decision_confidence']:.4f} "
            f"verification_confidence={live['verification']['confidence']:.4f} "
            f"records=event:{live_counts[0]},verification:{live_counts[1]}"
        )


if __name__ == "__main__":
    unittest.main()
