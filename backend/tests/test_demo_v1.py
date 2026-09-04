"""Contract tests for the live-demo composition layer.

The tests mock only the network-bound Qwen calls.  Capability matching and
assignment are deliberately real so a model result cannot bypass the existing
Phase 3 rules.
"""

from types import SimpleNamespace
import os
import tempfile
import unittest
from unittest.mock import patch

from database import connection
from database.connection import get_event, get_fleet_state, get_transitions, reset_fleet_state
from spatial.spatial_data import VISUAL_ROUTE_VERSION, robot_visual_endpoint
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
        "need_clean": True, "evidence_sufficient": True, "ambiguity_type": "none",
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
        "issue_remaining": False,
        "confidence": 0.95,
        "evidence_summary": "mocked live verification",
        "next_action": "close",
        "elapsed_ms": 130,
        "raw": {},
    }


class DemoV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp_dir = tempfile.TemporaryDirectory()
        cls._database_path = connection.DATABASE_PATH
        connection.DATABASE_PATH = os.path.join(cls._temp_dir.name, "demo-v1-test.db")
        connection.initialize_database()

    @classmethod
    def tearDownClass(cls) -> None:
        connection.DATABASE_PATH = cls._database_path
        cls._temp_dir.cleanup()

    def setUp(self) -> None:
        reset_fleet_state()
    def test_live_qwen_semantics_flow_through_existing_scheduler(self) -> None:
        cases = (("demo01", "small_litter", "robot-a"), ("demo03", "can", "robot-c"))
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_verification_qwen_vl", side_effect=_verification):
            for demo_id, event_type, expected_robot in cases:
                with patch("demo_v1.service.run_event_qwen_vl", return_value=_review(event_type)):
                    result = run_demo(demo_id)
                self.assertEqual(result["status"], "CLOSED")
                self.assertEqual(result["assignment_decision"]["selected_robot_id"], expected_robot)
                self.assertEqual(result["task_profile"]["object_type"], event_type)

    def test_sufficient_single_view_never_calls_agent_even_for_liquid(self) -> None:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_autonomous_acquisition") as agent, patch("demo_v1.service.run_event_qwen_vl", return_value=_review("liquid")) as cloud, patch("demo_v1.service.run_verification_qwen_vl", side_effect=_verification):
            result = run_demo("demo02")
        self.assertEqual(result["status"], "CLOSED")
        self.assertEqual(result["assignment_decision"]["selected_robot_id"], "robot-b")
        self.assertEqual(len(cloud.call_args.args[0]), 1)
        self.assertEqual(len(cloud.call_args.args[2]), 1)
        agent.assert_not_called()

    def test_new_formal_demo_event_has_explicit_customer_runtime_source(self) -> None:
        created = create_demo_event("demo01")
        self.assertEqual(get_event(created["event_id"])["source"], "INTERVIEW_RUNTIME")

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
            self.assertEqual([item["state"] for item in get_transitions(event_id)], ["DETECTED", "EDGE_DETECTED", "SINGLE_VIEW_REVIEW", "CLOUD_REVIEW", "LOCATED", "ASSIGNED", "NAVIGATING", "ARRIVED", "CLEANING_COMPLETED", "VERIFYING", "CLOSED"])

    def test_public_evidence_projection_never_releases_future_assets(self) -> None:
        """Asset storage is complete; external snapshots are strictly temporal."""
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("small_litter")), patch("demo_v1.service.run_verification_qwen_vl", side_effect=_verification):
            created = create_demo_event("demo01")
            event_id = created["event_id"]
            self.assertEqual([asset["role"] for asset in created["asset_manifest"]["assets"]], ["before"])
            edge = edge_review(event_id)
            self.assertEqual([asset["role"] for asset in edge["asset_manifest"]["assets"]], ["before"])
            cloud_review(event_id); locate_event(event_id); assign_event(event_id); start_navigation(event_id); complete_navigation(event_id)
            cleaned = complete_cleaning(event_id)
            self.assertNotIn("after", [asset["role"] for asset in cleaned["asset_manifest"]["assets"]])
            verified = verify_event(event_id)
            self.assertIn("after", [asset["role"] for asset in verified["asset_manifest"]["assets"]])

    def test_manual_multiview_entry_cannot_bypass_single_view(self) -> None:
        event_id = create_demo_event("demo02")["event_id"]
        edge_review(event_id)
        with self.assertRaisesRegex(ValueError, "evidence-gated"):
            multi_view_review(event_id)
        self.assertEqual(get_event(event_id)["state"], "EDGE_DETECTED")

    def test_cloud_unavailable_stage_stops_before_scheduler_or_verification(self) -> None:
        event_id = create_demo_event("demo01")["event_id"]
        edge_review(event_id)
        result = cloud_review(event_id, force_unavailable=True)
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertIsNone(result["assignment_decision"])
        self.assertIsNone(result["verification"])

    def test_locate_uses_primary_bbox_and_persists_phase2_mapping(self) -> None:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("can")):
            event_id = create_demo_event("demo03")["event_id"]
            edge_review(event_id)
            cloud_review(event_id)
            located = locate_event(event_id)
        self.assertEqual(located["state"], "LOCATED")
        spatial = located["spatial_location"]
        self.assertEqual(spatial["camera_id"], "CAM-A2-08")
        self.assertEqual(spatial["mapping_method"], "four_point_homography")
        self.assertEqual(spatial["representative_point"], "bbox_bottom_center")
        self.assertEqual(spatial["map_id"], "A_2F")
        self.assertEqual(get_event(event_id)["location"]["map_id"], "A_2F")

    def test_navigation_uses_shared_fleet_map_and_dijkstra_result(self) -> None:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("can")):
            event_id = create_demo_event("demo03")["event_id"]
            edge_review(event_id)
            cloud_review(event_id)
            locate_event(event_id)
            assigned = assign_event(event_id)
            self.assertEqual(assigned["assignment_decision"]["selected_robot_id"], "robot-c")
            plan = start_navigation(event_id)["navigation_plan"]
        self.assertEqual(plan["source"], "dijkstra_global_topology_planner")
        self.assertEqual(plan["start_map"], "B_1F")
        self.assertEqual(plan["target_map"], "A_2F")
        self.assertIn("SKYBRIDGE_B", plan["node_path"])
        self.assertGreater(plan["total_cost"], 0)

    def test_demo03_persists_one_controlled_skybridge_patrol_observation(self) -> None:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("can")):
            event_id = create_demo_event("demo03")["event_id"]
            edge_review(event_id)
            cloud_review(event_id)
            locate_event(event_id)
            assign_event(event_id)
            plan = start_navigation(event_id)["navigation_plan"]
        observation = plan["patrol_observation"]
        self.assertEqual(observation["trigger_node_id"], "SKYBRIDGE_B")
        self.assertEqual(observation["location"], "B栋2F连廊入口")
        self.assertEqual(observation["finding"], "单元门未关闭")
        self.assertEqual(observation["source"], "CONTROLLED_RGBD_DEMO")
        self.assertTrue(observation["asset_url"].endswith("door-ajar-rgbd.png"))
        self.assertEqual(get_event(event_id)["demo_v1"]["navigation_plan"]["patrol_observation"], observation)

    def test_demo04_reaches_human_fallback_only_after_capability_evaluation(self) -> None:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("large_object")):
            event_id = create_demo_event("demo04")["event_id"]
            edge_review(event_id)
            self.assertEqual(cloud_review(event_id)["state"], "CLOUD_REVIEW")
            locate_event(event_id)
            result = assign_event(event_id)
        self.assertEqual(result["state"], "HUMAN_FALLBACK")
        self.assertIsNone(result["assignment_decision"]["selected_robot_id"])
        self.assertEqual(result["assignment_decision"]["candidate_count"], 0)
        self.assertFalse(any(item["eligible"] for item in result["assignment_decision"]["candidates"]))

    def test_closed_event_retains_shared_fleet_terminal_location(self) -> None:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")), patch("demo_v1.service.run_event_qwen_vl", return_value=_review("small_litter")), patch("demo_v1.service.run_verification_qwen_vl", side_effect=_verification):
            event_id = create_demo_event("demo01")["event_id"]
            edge_review(event_id)
            cloud_review(event_id)
            locate_event(event_id)
            assign_event(event_id)
            start_navigation(event_id)
            complete_navigation(event_id)
            complete_cleaning(event_id)
            verify_event(event_id)
        robot = next(item for item in get_fleet_state() if item["id"] == "robot-a")
        self.assertEqual(robot["status"], "idle")
        self.assertEqual(robot["map_id"], "OUTDOOR")
        self.assertNotEqual(robot["coordinates"], {"x": 24, "y": 40})
        self.assertEqual(robot["overview_position"], robot_visual_endpoint("robot-a"))
        self.assertEqual(robot["overview_position_version"], VISUAL_ROUTE_VERSION)


if __name__ == "__main__":
    unittest.main()
