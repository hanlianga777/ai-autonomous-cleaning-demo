"""Contract tests for the live-demo composition layer.

The tests mock only the network-bound Qwen calls.  Capability matching and
assignment are deliberately real so a model result cannot bypass the existing
Phase 3 rules.
"""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from demo_v1.service import run_demo


def _review(event_type: str, confidence: float = 0.91) -> dict:
    return {
        "provider": "DashScope Qwen-VL",
        "model": "qwen-vl-max",
        "image_count": 1,
        "elapsed_ms": 120,
        "need_clean": True,
        "event_type": event_type,
        "decision_confidence": confidence,
        "severity": "medium",
        "surface_type": "asphalt" if event_type == "small_litter" else "tile",
        "interference_factors": [],
        "evidence_summary": "mocked live semantic decision",
        "recommended_capabilities": [],
        "next_action": "dispatch_robot",
        "raw": {},
    }


def _verification(*_args, **_kwargs) -> dict:
    return {
        "provider": "DashScope Qwen-VL",
        "verification_pass": True,
        "confidence": 0.95,
        "evidence_summary": "mocked live verification",
        "next_action": "close",
        "elapsed_ms": 130,
        "raw": {},
    }


class DemoV1Tests(unittest.TestCase):
    def test_live_qwen_semantics_flow_through_existing_scheduler(self) -> None:
        cases = (("demo01", "small_litter", "robot-a"), ("demo03", "can", "robot-c"))
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_verification_qwen_vl", side_effect=_verification):
            for demo_id, event_type, expected_robot in cases:
                with patch("demo_v1.service.run_event_qwen_vl", return_value=_review(event_type)):
                    result = run_demo(demo_id)
                self.assertEqual(result["status"], "CLOSED")
                self.assertEqual(result["assignment_decision"]["selected_robot_id"], expected_robot)
                self.assertEqual(result["task_profile"]["object_type"], event_type)

    def test_multiview_uses_one_three_image_qwen_call_then_robot_b(self) -> None:
        multiview = {
            "triggered": True,
            "selected_cameras": [{"camera_id": "CAM-A1-02"}, {"camera_id": "CAM-A1-04"}],
            "tool_calls": [{"tool": "camera_coverage"}, {"tool": "frame_fetch"}, {"tool": "vlm"}],
            "evidence": [],
            "final_confidence": 0.74,
            "decision": "HUMAN_REVIEW",
            "iteration_count": 1,
            "limits": {"max_additional_cameras": 2, "max_agent_iterations": 2},
        }
        review = _review("liquid")
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_multi_view_agent", return_value=multiview), patch("demo_v1.service.run_event_qwen_vl", return_value=review) as qwen_call, patch("demo_v1.service.run_verification_qwen_vl", side_effect=_verification):
            result = run_demo("demo02")
        self.assertEqual(result["status"], "CLOSED")
        self.assertEqual(result["assignment_decision"]["selected_robot_id"], "robot-b")
        self.assertEqual(len(qwen_call.call_args.args[0]), 3)
        self.assertEqual(result["multi_view"]["selected_cameras"], multiview["selected_cameras"])

    def test_large_object_keeps_human_fallback(self) -> None:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("large_object")):
            result = run_demo("demo04")
        self.assertEqual(result["status"], "HUMAN_FALLBACK")
        self.assertIsNone(result["assignment_decision"]["selected_robot_id"])

    def test_cloud_unavailable_never_silently_replays_or_assigns(self) -> None:
        result = run_demo("demo01", force_unavailable=True)
        self.assertEqual(result["status"], "HUMAN_REVIEW")
        self.assertEqual(result["mode"], "LIVE")
        self.assertIsNone(result["assignment_decision"])
        self.assertTrue(result["controlled_yolo"])


if __name__ == "__main__":
    unittest.main()
