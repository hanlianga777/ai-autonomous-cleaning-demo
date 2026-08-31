"""Behaviour-level contracts for the customer demo's backend-owned runtime."""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from database import connection
from database.connection import get_event, reset_fleet_state
from demo_v1 import service
from perception import qwen


def wait_for(event_id: str, expected: set[str], timeout: float = 4.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        event = get_event(event_id)
        if event and event["state"] in expected:
            return event
        time.sleep(0.01)
    event = get_event(event_id)
    raise AssertionError(f"{event_id} did not reach {expected}; current={event and event['state']}")


class AutonomousRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.original_database = connection.DATABASE_PATH
        connection.DATABASE_PATH = os.path.join(cls.temp.name, "autonomous-runtime.sqlite")
        connection.initialize_database()

    @classmethod
    def tearDownClass(cls) -> None:
        connection.DATABASE_PATH = cls.original_database
        cls.temp.cleanup()

    def setUp(self) -> None:
        reset_fleet_state()

    @staticmethod
    def _review(event_type: str, *, sufficient: bool = True, confidence: float = 0.93, ambiguity: str = "none") -> dict:
        return {
            "provider": "test-cloud", "model": "test-vlm", "image_count": 1, "elapsed_ms": 1,
            "need_clean": True, "evidence_sufficient": sufficient, "ambiguity_type": ambiguity,
            "event_type": event_type, "decision_confidence": confidence, "severity": "medium",
            "surface_type": "asphalt" if event_type == "small_litter" else "tile",
            "interference_factors": [ambiguity] if ambiguity != "none" else [],
            "evidence_summary": "受控测试云端研判", "recommended_capabilities": [],
            "next_action": "dispatch_robot", "raw": {},
        }

    @staticmethod
    def _verification(*_args: object, **_kwargs: object) -> dict:
        return {
            "provider": "test-cloud", "verification_pass": True, "issue_remaining": False,
            "confidence": 0.96, "evidence_summary": "受控测试验收通过", "next_action": "close",
            "elapsed_ms": 1, "raw": {},
        }

    def _trigger_once(self, demo_id: str) -> tuple[str, dict]:
        created = service.create_demo_event(demo_id, "LIVE")
        event_id = created["event_id"]
        type_by_demo = {"demo01": "small_litter", "demo03": "can", "demo04": "large_object"}
        first = self._review(type_by_demo.get(demo_id, "liquid"), sufficient=demo_id != "demo02", ambiguity="reflection" if demo_id == "demo02" else "none")
        final = {
            "need_action": True, "event_type": "liquid", "confidence": 0.93,
            "evidence_sufficient": True, "ambiguity_type": "none", "severity": "medium",
            "surface_type": "tile", "interference_factors": [],
            "evidence_summary": "补充视角已确认液体污渍", "recommended_capabilities": ["wet_cleaning", "strong_suction"],
        }
        tool_turns = iter([
            {"role": "assistant", "tool_calls": [{"id": "find-1", "type": "function", "function": {"name": "find_supporting_cameras", "arguments": {}}}]},
            {"role": "assistant", "tool_calls": [{"id": "fetch-1", "type": "function", "function": {"name": "fetch_camera_evidence", "arguments": {"camera_id": "CAM-A1-02"}}}]},
            {"role": "assistant", "tool_calls": [{"id": "finish-1", "type": "function", "function": {"name": "finish_visual_judgment", "arguments": final}}]},
        ])
        def tool_transport(*_args: object, **kwargs: object):
            if kwargs.get("tools") is None:
                raise AssertionError("Only the Multi-view tool transport is expected here.")
            return next(tool_turns), 1
        with patch.object(service, "sleep", lambda _seconds: None):
            with patch.object(service, "get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-vlm")), \
                 patch.object(service, "get_agent_model", return_value="test-vlm"), \
                 patch.object(service, "run_event_qwen_vl", return_value=first), \
                 patch.object(service, "run_verification_qwen_vl", side_effect=self._verification), \
                 patch.object(qwen, "_request_qwen", side_effect=tool_transport):
                service.start_autonomous_progression(event_id)
                terminal = wait_for(event_id, {"CLOSED", "HUMAN_REVIEW", "HUMAN_FALLBACK"})
        return event_id, terminal

    def test_demo01_one_trigger_reaches_closed_without_browser_stage_calls(self) -> None:
        _event_id, terminal = self._trigger_once("demo01")
        self.assertEqual(terminal["state"], "CLOSED")

    def test_demo02_one_trigger_acquires_multiview_then_reaches_closed(self) -> None:
        event_id, terminal = self._trigger_once("demo02")
        self.assertEqual(terminal["state"], "CLOSED")
        self.assertTrue((get_event(event_id)["demo_v1"].get("multi_view") or {}).get("evidence_assets"))

    def test_demo03_one_trigger_keeps_cross_building_route_then_reaches_closed(self) -> None:
        event_id, terminal = self._trigger_once("demo03")
        self.assertEqual(terminal["state"], "CLOSED")
        plan = get_event(event_id)["demo_v1"]["navigation_plan"]
        self.assertEqual(plan["start_map"], "B_1F")
        self.assertEqual(plan["target_map"], "A_2F")
        self.assertIn("SKYBRIDGE_B", plan["node_path"])

    def test_demo04_waits_for_explicit_operator_completion_then_verifies(self) -> None:
        event_id, terminal = self._trigger_once("demo04")
        self.assertEqual(terminal["state"], "HUMAN_FALLBACK")
        with patch.object(service, "sleep", lambda _seconds: None):
            closed = service.complete_demo04_manual(event_id)
        self.assertEqual(closed["state"], "CLOSED")
        self.assertEqual(get_event(event_id)["state"], "CLOSED")
