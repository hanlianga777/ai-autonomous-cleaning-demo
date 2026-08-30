import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from perception.config import get_runtime
from perception.models import TASK_PROFILE_FIELDS, perception_schema, validate_ai_result_schema
from perception.service import analyze_mock_case, analyze_upload, interview_ai_readiness_probe, media_kind, system_ai_status


class AiLabTests(unittest.TestCase):
    def test_default_runtime_is_explicit_mock_without_credentials(self):
        old_mode = os.environ.get("AI_LAB_MODE")
        old_key = os.environ.get("DASHSCOPE_API_KEY")
        old_model = os.environ.get("AI_LAB_YOLO_MODEL")
        os.environ["AI_LAB_MODE"] = "mock"
        os.environ.pop("DASHSCOPE_API_KEY", None)
        os.environ.pop("AI_LAB_YOLO_MODEL", None)
        try:
            with patch("perception.config._load_project_env"):
                runtime = get_runtime()
            self.assertEqual(runtime.active_mode, "mock")
            self.assertEqual(runtime.label, "DEMO MOCK MODE")
        finally:
            for key, value in (("AI_LAB_MODE", old_mode), ("DASHSCOPE_API_KEY", old_key), ("AI_LAB_YOLO_MODEL", old_model)):
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_dashscope_key_is_reported_ready_without_requiring_local_yolo_weight(self):
        old_mode = os.environ.get("AI_LAB_MODE")
        old_key = os.environ.get("DASHSCOPE_API_KEY")
        old_model = os.environ.get("AI_LAB_YOLO_MODEL")
        os.environ["AI_LAB_MODE"] = "auto"
        os.environ["DASHSCOPE_API_KEY"] = "local-test-key"
        os.environ.pop("AI_LAB_YOLO_MODEL", None)
        try:
            with patch("perception.config._load_project_env"):
                runtime = get_runtime()
            self.assertEqual(runtime.active_mode, "mock")
            self.assertTrue(runtime.qwen_ready)
            self.assertTrue(runtime.interview_live_ready)
            self.assertFalse(runtime.full_ai_lab_ready)
        finally:
            for key, value in (("AI_LAB_MODE", old_mode), ("DASHSCOPE_API_KEY", old_key), ("AI_LAB_YOLO_MODEL", old_model)):
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_yolo_without_dashscope_is_not_interview_live_ready(self):
        old_key = os.environ.get("DASHSCOPE_API_KEY")
        old_model = os.environ.get("AI_LAB_YOLO_MODEL")
        with tempfile.NamedTemporaryFile() as model:
            os.environ.pop("DASHSCOPE_API_KEY", None)
            os.environ["AI_LAB_YOLO_MODEL"] = model.name
            try:
                with patch("perception.config._load_project_env"):
                    runtime = get_runtime()
                self.assertTrue(runtime.local_yolo_ready)
                self.assertFalse(runtime.interview_live_ready)
                self.assertFalse(runtime.full_ai_lab_ready)
            finally:
                if old_key is None: os.environ.pop("DASHSCOPE_API_KEY", None)
                else: os.environ["DASHSCOPE_API_KEY"] = old_key
                if old_model is None: os.environ.pop("AI_LAB_YOLO_MODEL", None)
                else: os.environ["AI_LAB_YOLO_MODEL"] = old_model

    def test_readiness_probe_reports_missing_key_without_secret(self):
        old_key = os.environ.get("DASHSCOPE_API_KEY")
        os.environ.pop("DASHSCOPE_API_KEY", None)
        try:
            with patch("perception.config._load_project_env"):
                runtime = get_runtime()
            with patch("perception.service.get_runtime", return_value=runtime):
                result = interview_ai_readiness_probe()
            self.assertEqual(result["readiness"]["cloud_vlm_reachable"], "KEY_MISSING")
            self.assertFalse(result["readiness"]["interview_live_ready"])
            self.assertNotIn("DASHSCOPE_API_KEY", str(result))
        finally:
            if old_key is not None: os.environ["DASHSCOPE_API_KEY"] = old_key

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

    def test_business_detection_keeps_business_class_separate_from_raw_model_evidence(self):
        result = analyze_mock_case("low_confidence_milk_tea_spill")
        detection = result["business_detections"][0]
        self.assertEqual(detection["business_class"], "liquid")
        self.assertEqual(detection["confidence_source"], "MOCK")
        self.assertIn("raw_yolo_class", detection)
        self.assertIn("vlm_class", detection)
        status = system_ai_status()
        self.assertEqual(status["camera_to_slam"]["mode"], "REAL_CALCULATION")
        self.assertEqual(status["robot"]["mode"], "SIMULATION")


if __name__ == "__main__":
    unittest.main()
