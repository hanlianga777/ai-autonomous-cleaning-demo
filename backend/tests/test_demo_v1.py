"""Contract tests for the live-demo composition layer.

The tests mock only the network-bound Qwen calls.  Capability matching and
assignment are deliberately real so a model result cannot bypass the existing
Phase 3 rules.
"""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from database.connection import get_transitions
from demo_v1.service import (
    assign_event,
    cloud_review,
    complete_cleaning,
    complete_navigation,
    create_demo_event,
    edge_review,
    locate_event,
    multi_view_review,
    run_demo,
    start_navigation,
    verify_event,
)


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

    def test_stage_api_never_runs_future_work_early(self) -> None:
        """Cloud, scheduling and verification each have one durable boundary."""
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("small_litter")) as cloud, patch("demo_v1.service.run_verification_qwen_vl", side_effect=_verification) as verify:
            created = create_demo_event("demo01")
            event_id = created["event_id"]
            edge = edge_review(event_id)
            self.assertEqual(edge["state"], "EDGE_DETECTED")
            cloud.assert_not_called()
            reviewed = cloud_review(event_id)
            self.assertEqual(reviewed["state"], "CLOUD_REVIEW")
            self.assertIsNone(reviewed["assignment_decision"])
            self.assertEqual(cloud.call_count, 1)
            verify.assert_not_called()
            located = locate_event(event_id)
            self.assertEqual(located["state"], "LOCATED")
            assigned = assign_event(event_id)
            self.assertEqual(assigned["state"], "ASSIGNED")
            self.assertEqual(assigned["assignment_decision"]["selected_robot_id"], "robot-a")
            verify.assert_not_called()
            self.assertEqual(start_navigation(event_id)["state"], "NAVIGATING")
            self.assertEqual(complete_navigation(event_id)["state"], "ARRIVED")
            self.assertEqual(complete_cleaning(event_id)["state"], "CLEANING_COMPLETED")
            verify.assert_not_called()
            self.assertEqual(verify_event(event_id)["state"], "CLOSED")
            self.assertEqual(verify.call_count, 1)
            self.assertEqual([item["state"] for item in get_transitions(event_id)], ["DETECTED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATED", "ASSIGNED", "NAVIGATING", "ARRIVED", "CLEANING_COMPLETED", "VERIFYING", "CLOSED"])

    def test_demo02_stage_keeps_three_views_before_cloud_and_robot_b_after_assign(self) -> None:
        multiview = {"triggered": True, "selected_cameras": [{"camera_id": "CAM-A1-02"}, {"camera_id": "CAM-A1-04"}], "tool_calls": [], "evidence": [], "final_confidence": 0.74, "decision": "HUMAN_REVIEW", "iteration_count": 1, "limits": {"max_additional_cameras": 2, "max_agent_iterations": 2}}
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_multi_view_agent", return_value=multiview), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("liquid")) as cloud:
            event_id = create_demo_event("demo02")["event_id"]
            edge_review(event_id)
            viewed = multi_view_review(event_id)
            self.assertEqual(viewed["state"], "MULTI_VIEW")
            cloud.assert_not_called()
            reviewed = cloud_review(event_id)
            self.assertEqual(len(cloud.call_args.args[0]), 3)
            self.assertIsNone(reviewed["assignment_decision"])
            locate_event(event_id)
            assigned = assign_event(event_id)
            self.assertEqual(assigned["assignment_decision"]["selected_robot_id"], "robot-b")

    def test_cloud_unavailable_stage_stops_before_scheduler_or_verification(self) -> None:
        event_id = create_demo_event("demo01")["event_id"]
        edge_review(event_id)
        result = cloud_review(event_id, force_unavailable=True)
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertIsNone(result["assignment_decision"])
        self.assertIsNone(result["verification"])


if __name__ == "__main__":
    unittest.main()
