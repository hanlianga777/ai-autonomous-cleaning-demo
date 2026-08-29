import os
import tempfile
import unittest

from database import connection
from workbench.service import list_scenario_assets, run_scenario_02_workbench, run_workbench_event, run_workbench_upload, scenario_02_assets


class WorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._database_path = connection.DATABASE_PATH
        cls._temp_dir = tempfile.TemporaryDirectory()
        connection.DATABASE_PATH = os.path.join(cls._temp_dir.name, "workbench-test.db")
        connection.initialize_database()

    @classmethod
    def tearDownClass(cls):
        connection.DATABASE_PATH = cls._database_path
        cls._temp_dir.cleanup()

    def test_asset_manifests_expose_all_supplied_views_and_the_human_completion_after_image(self):
        manifest = scenario_02_assets()
        self.assertEqual(manifest["event_id"], "event-beverage-spill-002")
        self.assertEqual({asset["camera_id"] for asset in manifest["assets"]}, {"CAM-A1-01", "CAM-A1-02", "CAM-A1-04"})
        self.assertEqual(manifest["missing_assets"], [])
        self.assertEqual(manifest["metadata"]["expected_robot"], "ROBOT_B")
        all_scenarios = {scenario["event_id"]: scenario for scenario in list_scenario_assets()}
        self.assertEqual(set(all_scenarios), {"event-outdoor-tissue-001", "event-beverage-spill-002", "event-indoor-can-003", "event-oversized-box-004"})
        self.assertEqual(all_scenarios["event-oversized-box-004"]["verification_mode"], "HUMAN_REQUIRED")
        self.assertTrue(any(asset["role"] == "after" for asset in all_scenarios["event-oversized-box-004"]["assets"]))

    def test_workbench_composes_existing_ai_schema_multiview_and_robot_b_workflow(self):
        result = run_scenario_02_workbench()
        self.assertEqual(result["initial_ai_result"]["schema_version"], "ai-lab.v1")
        self.assertEqual(result["initial_ai_result"]["perception"]["confidence"], 0.67)
        self.assertEqual(result["multi_view"]["decision"], "CONFIRM")
        self.assertEqual(result["multi_view"]["final_confidence"], 0.92)
        self.assertEqual(result["workflow_event"]["assignment_decision"]["selected_robot_name"], "Robot B")
        self.assertEqual(result["workflow_event"]["verification"]["result"], "PASS")
        primary = next(asset for asset in result["asset_manifest"]["assets"] if asset["role"] == "before")
        overlay = primary["detection_overlays"][0]
        self.assertEqual(overlay["label"], "液体污渍")
        self.assertEqual(overlay["source"], "CONTROLLED_REPLAY")
        self.assertEqual(result["initial_ai_result"]["business_detections"][0]["confidence_source"], "CONTROLLED_REPLAY")

    def test_other_image_backed_scenarios_reuse_scheduler_and_preserve_human_boundary(self):
        robot_c = run_workbench_event("event-indoor-can-003")
        self.assertEqual(robot_c["initial_ai_result"]["task_profile"]["object_type"], "aluminum_can")
        self.assertEqual(robot_c["workflow_event"]["assignment_decision"]["selected_robot_name"], "Robot C")
        self.assertIn("Skybridge", robot_c["workflow_event"]["navigation_plan"]["display_path"])
        human = run_workbench_event("event-oversized-box-004")
        self.assertEqual(human["workflow_event"]["assignment_decision"]["status"], "HUMAN_FALLBACK")
        self.assertEqual(human["asset_manifest"]["verification_mode"], "HUMAN_REQUIRED")

    def test_before_image_hash_runs_its_matching_scenario_and_rejects_unknown_upload(self):
        primary_path = "../sample_data/camera_events/CAM-OUT-01/event-outdoor-tissue-001/primary.png"
        with open(primary_path, "rb") as image:
            result = run_workbench_upload("用户上传的室外纸巾.png", image.read())
        self.assertEqual(result["upload_match"]["event_id"], "event-outdoor-tissue-001")
        self.assertEqual(result["workflow_event"]["assignment_decision"]["selected_robot_name"], "Robot A")
        with self.assertRaisesRegex(ValueError, "不属于当前四个"):
            run_workbench_upload("unknown.png", b"not-an-approved-demo-image")


if __name__ == "__main__":
    unittest.main()
