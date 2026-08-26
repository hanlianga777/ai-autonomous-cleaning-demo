import os
import tempfile
import unittest

from database import connection
from workbench.service import run_scenario_02_workbench, scenario_02_assets


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

    def test_asset_manifest_keeps_camera_event_view_contract_without_fabricating_files(self):
        manifest = scenario_02_assets()
        self.assertEqual(manifest["event_id"], "event-beverage-spill-002")
        self.assertEqual({asset["camera_id"] for asset in manifest["assets"]}, {"CAM-A1-01", "CAM-A1-02", "CAM-A1-03"})
        self.assertEqual(len(manifest["missing_assets"]), 4)
        self.assertEqual(manifest["metadata"]["expected_robot"], "ROBOT_B")

    def test_workbench_composes_existing_ai_schema_multiview_and_robot_b_workflow(self):
        result = run_scenario_02_workbench()
        self.assertEqual(result["initial_ai_result"]["schema_version"], "ai-lab.v1")
        self.assertEqual(result["initial_ai_result"]["perception"]["confidence"], 0.67)
        self.assertEqual(result["multi_view"]["decision"], "CONFIRM")
        self.assertEqual(result["multi_view"]["final_confidence"], 0.92)
        self.assertEqual(result["workflow_event"]["assignment_decision"]["selected_robot_name"], "Robot B")
        self.assertEqual(result["workflow_event"]["verification"]["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
