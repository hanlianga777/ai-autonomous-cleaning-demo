"""Opt-in paid LIVE Demo02 acquisition and explicit response-only Replay.

Uses an isolated SQLite database and the actual configured DashScope provider.
No semantic answers, tool choices, confidence values or runtime engines mocked.
"""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from database import connection as db
from demo_v1 import service
from perception import qwen


@unittest.skipUnless(os.getenv("RUN_P1C_LIVE_ACCEPTANCE") == "1", "opt in to paid P1-C model calls")
class P1CLiveAcceptance(unittest.TestCase):
    def test_demo02_live_and_response_only_replay(self):
        with TemporaryDirectory(prefix="cleaning-p1c-acceptance-") as folder:
            original = db.DATABASE_PATH
            db.DATABASE_PATH = Path(folder) / "live.sqlite"
            try:
                db.initialize_database()
                live = service.run_demo("demo02", "LIVE")
                self._report(live)
                self.assertEqual(live["state"], "CLOSED", live.get("reason"))
                self.assertFalse(live["first_qwen_review"]["evidence_sufficient"])
                audit = live["multi_view"]["audit"]
                self.assertTrue(any(item["name"] == "find_supporting_cameras" and item["source"] == "MODEL_TOOL_CALL" for item in audit))
                self.assertTrue(any(item["name"] == "fetch_camera_evidence" and item["status"] == "OK" for item in audit))
                self.assertIn(len(live["multi_view"]["selected_cameras"]), (1, 2))
                self.assertLessEqual(live["multi_view"]["iteration_count"], 2)
                self.assertEqual(live["assignment_decision"]["selected_robot_id"], "robot-b")
                with patch.object(qwen, "_request_qwen", side_effect=AssertionError("Replay must not call cloud")):
                    replay = service.run_demo("demo02", "STABLE_REPLAY")
                self._report(replay)
                self.assertEqual(replay["state"], "CLOSED", replay.get("reason"))
                self.assertEqual(replay["qwen_review"]["source"], "REPLAY")
                self.assertEqual(replay["verification"]["source"], "REPLAY")
                self.assertEqual(replay["assignment_decision"]["selected_robot_id"], "robot-b")
                self.assertNotEqual(replay["event_id"], live["event_id"])
            finally:
                db.DATABASE_PATH = original

    @staticmethod
    def _report(result):
        first = result.get("first_qwen_review") or {}
        final = result.get("qwen_review") or {}
        multi = result.get("multi_view") or {}
        print(json.dumps({
            "event_id": result["event_id"], "mode": result["mode"], "state": result["state"],
            "first_confidence": first.get("decision_confidence"), "evidence_sufficient": first.get("evidence_sufficient"),
            "ambiguity": first.get("ambiguity_type"), "final_confidence": final.get("decision_confidence"),
            "fusion": (result.get("evidence_fusion") or {}).get("score"), "selected_cameras": multi.get("selected_cameras"),
            "rounds": multi.get("iteration_count"), "tool_audit": multi.get("audit"),
            "robot": (result.get("assignment_decision") or {}).get("selected_robot_id"),
            "verification_pass": (result.get("verification") or {}).get("verification_pass"),
            "verification_confidence": (result.get("verification") or {}).get("confidence"),
        }, ensure_ascii=False), flush=True)
