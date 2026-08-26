import os
import tempfile
import unittest
from pathlib import Path

from perception.config import get_runtime
from perception.models import TASK_PROFILE_FIELDS, perception_schema, validate_ai_result_schema
from perception.service import analyze_mock_case, analyze_upload, media_kind


class AiLabTests(unittest.TestCase):
    def test_default_runtime_is_explicit_mock_without_credentials(self):
        old_mode = os.environ.get("AI_LAB_MODE")
        old_key = os.environ.get("DASHSCOPE_API_KEY")
        old_model = os.environ.get("AI_LAB_YOLO_MODEL")
        os.environ["AI_LAB_MODE"] = "mock"
        os.environ.pop("DASHSCOPE_API_KEY", None)
        os.environ.pop("AI_LAB_YOLO_MODEL", None)
        try:
            runtime = get_runtime()
            self.assertEqual(runtime.active_mode, "mock")
            self.assertEqual(runtime.label, "DEMO MOCK MODE")
        finally:
            for key, value in (("AI_LAB_MODE", old_mode), ("DASHSCOPE_API_KEY", old_key), ("AI_LAB_YOLO_MODEL", old_model)):
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_mock_image_result_is_structured_and_does_not_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "coffee-cup.jpg"
            image.write_bytes(b"not-needed-in-mock-mode")
            result = analyze_upload(image, image.name, "CAM-A1-01")
        self.assertEqual(result["mode"], "mock")
        self.assertEqual(result["pipeline"]["keyframes"], 1)
        self.assertEqual(result["perception"]["need_clean"], True)
        self.assertEqual(result["task_profile"]["pollution_form"], "dry_debris")
        self.assertEqual(result["location"]["location"]["building"], "A")
        self.assertIn("separate", result["notes"][1])

    def test_mp4_uses_mock_keyframe_contract_and_rejects_unknown_media(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "lobby.mp4"
            video.write_bytes(b"not-needed-in-mock-mode")
            result = analyze_upload(video, video.name, "CAM-A1-01")
        self.assertEqual(media_kind("lobby.mp4"), "video")
        self.assertEqual(result["pipeline"]["keyframes"], 3)
        with self.assertRaises(ValueError):
            media_kind("unsafe.mov")

    def test_uncalibrated_camera_does_not_claim_a_slam_coordinate(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "lobby.jpg"
            image.write_bytes(b"mock")
            result = analyze_upload(image, image.name, "CAM-A2-01")
        self.assertIsNone(result["location"])
        self.assertIn("no four-point calibration", result["notes"][-1])

    def test_ai_result_to_task_profile_contract_is_complete(self):
        result = analyze_mock_case("heavy_milk_tea_spill")
        contract = perception_schema()
        self.assertTrue(set(contract["required_top_level"]).issubset(result))
        self.assertTrue(set(contract["perception_fields"]).issubset(result["perception"]))
        self.assertEqual(set(TASK_PROFILE_FIELDS), set(result["task_profile"]))
        self.assertEqual(result["workflow_input"]["task_profile"], result["task_profile"])
        self.assertEqual(result["workflow_input"]["location"]["map_id"], "A_1F")

    def test_four_business_cases_reuse_phase_3_capability_and_scheduler(self):
        expected = {
            "outdoor_small_litter": ("ASSIGNED", "Robot A"),
            "heavy_milk_tea_spill": ("ASSIGNED", "Robot B"),
            "indoor_paper_cup": ("ASSIGNED", "Robot C"),
            "oversized_box_or_bag": ("HUMAN_FALLBACK", None),
        }
        for case_name, (status, robot) in expected.items():
            with self.subTest(case=case_name):
                result = analyze_mock_case(case_name)
                self.assertTrue(result["perception"]["need_clean"])
                self.assertIsNotNone(result["workflow_input"])
                self.assertEqual(result["scheduler_preview"]["status"], status)
                self.assertEqual(result["scheduler_preview"]["selected_robot_name"], robot)

    def test_mock_and_real_build_against_one_response_schema(self):
        result = analyze_mock_case("indoor_paper_cup")
        required = set(perception_schema()["required_top_level"])
        self.assertTrue(required.issubset(result))
        self.assertEqual(result["schema_version"], "ai-lab.v1")
        real_shaped_result = result | {"mode": "real", "mode_label": "REAL AI MODE", "pipeline": result["pipeline"] | {"yolo": "yolo26n.pt", "vlm": "qwen-vl-max"}}
        self.assertEqual(validate_ai_result_schema(real_shaped_result)["schema_version"], result["schema_version"])


if __name__ == "__main__":
    unittest.main()
