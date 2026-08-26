import os
import tempfile
import unittest
from pathlib import Path

from perception.config import get_runtime
from perception.service import analyze_upload, media_kind


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


if __name__ == "__main__":
    unittest.main()
