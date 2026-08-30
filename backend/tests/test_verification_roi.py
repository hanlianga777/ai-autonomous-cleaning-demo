"""Regression coverage for generic target-ROI post-cleaning verification."""

from __future__ import annotations

from copy import deepcopy
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import os
import unittest
from unittest.mock import patch

from PIL import Image

from database import connection
from database.connection import get_event, reset_fleet_state, save_event
from demo_v1 import service
from demo_v1.replay import evidence_key
from perception import qwen
from perception.verification_evidence import _crop_png, build_verification_evidence
from perception.yolo import RealInferenceError


def _write_image(path: Path, size: tuple[int, int]) -> None:
    Image.new("RGB", size, color=(230, 230, 230)).save(path, format="PNG")


def _box(*, camera_id: str = "CAM-1", x1: float = .4, y1: float = .4, x2: float = .5, y2: float = .5) -> dict:
    return {"camera_id": camera_id, "class_name": "目标物", "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}}


def _raw_verification(**changes: object) -> dict:
    return {
        "issue_remaining": False,
        "verification_pass": True,
        "confidence": .95,
        "evidence_summary": "目标区域内未见残留。",
        "next_action": "close",
        **changes,
    }


def _verification(*, passed: bool, confidence: float = .95, summary: str = "test verification") -> dict:
    return {
        "provider": "test", "source": "LIVE_MODEL", "issue_remaining": not passed,
        "verification_pass": passed, "confidence": confidence, "next_action": "close" if passed else "human_review",
        "evidence_summary": summary, "elapsed_ms": 1, "raw": {"test": True},
    }


def _review(event_type: str = "small_litter") -> dict:
    return {
        "provider": "test transport", "model": "test-model", "elapsed_ms": 1,
        "need_clean": True, "evidence_sufficient": True, "ambiguity_type": "none",
        "event_type": event_type, "decision_confidence": .92, "severity": "medium",
        "surface_type": "asphalt" if event_type == "small_litter" else "tile", "interference_factors": [],
        "evidence_summary": "test semantic decision", "recommended_capabilities": [],
        "next_action": "dispatch_robot", "raw": {},
    }


class VerificationEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.before = Path(self.temp.name) / "before.png"
        self.after = Path(self.temp.name) / "after.png"
        _write_image(self.before, (1000, 500))
        _write_image(self.after, (400, 800))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _evidence(self, boxes: list[dict] | None = None):
        return build_verification_evidence(
            before=self.before, after=self.after, controlled_yolo=[_box()] if boxes is None else boxes,
            camera_id="CAM-1", object_type="can",
        )

    def test_same_normalized_union_and_padded_crop_apply_to_both_frames(self) -> None:
        evidence = self._evidence([_box(x1=.4, y1=.4, x2=.5, y2=.5), _box(x1=.45, y1=.45, x2=.55, y2=.6)])
        target = evidence.context["target"]
        self.assertEqual(target["bbox_union"], {"x1": .4, "y1": .4, "x2": .55, "y2": .6})
        self.assertEqual(evidence.context["roi_source"], "controlled_yolo_normalized_union")
        self.assertEqual(target["object_type"], "can")
        self.assertEqual(len(target["crop_sha256"]["before"]), 64)
        self.assertNotEqual(evidence.before_roi, evidence.after_roi)
        # The image dimensions differ, but the sole ROI coordinates are
        # normalized once and retained in the evidence contract.
        self.assertTrue(0 <= target["roi"]["x1"] < target["roi"]["x2"] <= 1)
        self.assertTrue(0 <= target["roi"]["y1"] < target["roi"]["y2"] <= 1)

    def test_edge_roi_is_clipped_without_becoming_empty(self) -> None:
        evidence = self._evidence([_box(x1=0, y1=0, x2=.01, y2=.01)])
        roi = evidence.context["target"]["roi"]
        self.assertEqual(roi["x1"], 0.0)
        self.assertEqual(roi["y1"], 0.0)
        self.assertGreater(roi["x2"], roi["x1"])
        self.assertGreater(roi["y2"], roi["y1"])

    def test_crop_uses_ceil_for_the_right_and_bottom_normalized_boundary(self) -> None:
        odd = Path(self.temp.name) / "odd.png"
        _write_image(odd, (997, 991))
        roi = {"x1": .39, "y1": .39, "x2": .51, "y2": .51}
        with Image.open(BytesIO(_crop_png(odd, roi))) as crop:
            self.assertEqual(crop.size, (509 - 388, 506 - 386))

    def test_empty_or_nonfinite_primary_detection_fails_closed(self) -> None:
        for boxes in (
            [],
            [{"camera_id": "CAM-1", "bbox": {}}],
            [_box(x1=float("nan"))],
            [_box(x1=.5, x2=.5)],
            [_box(camera_id="OTHER")],
        ):
            with self.subTest(boxes=boxes):
                with self.assertRaises(RealInferenceError):
                    self._evidence(boxes)

    def test_missing_source_asset_fails_closed(self) -> None:
        self.before.unlink()
        with self.assertRaises(RealInferenceError):
            self._evidence()

    def test_verifier_sends_two_full_frames_and_two_paired_roi_images(self) -> None:
        evidence = self._evidence()
        with patch.object(qwen, "_request_qwen", return_value=(_raw_verification(), 7)) as request:
            result = qwen.run_verification_qwen_vl(
                self.before, self.after, evidence.context, "model",
                before_roi=evidence.before_roi, after_roi=evidence.after_roi,
            )
        content = request.call_args.args[0]
        self.assertEqual(sum(item["type"] == "image_url" for item in content), 4)
        self.assertEqual(result["source"], "LIVE_MODEL")
        self.assertEqual(result["roi"], evidence.context["target"]["roi"])
        self.assertEqual(result["roi_source"], "controlled_yolo_normalized_union")

    def test_verifier_preserves_subthreshold_raw_confidence_without_rounding(self) -> None:
        evidence = self._evidence()
        with patch.object(qwen, "_request_qwen", return_value=(_raw_verification(confidence=.84996), 7)):
            result = qwen.run_verification_qwen_vl(
                self.before, self.after, evidence.context, "model",
                before_roi=evidence.before_roi, after_roi=evidence.after_roi,
            )
        self.assertEqual(result["confidence"], .84996)

    def test_verifier_never_falls_back_to_full_frames_without_paired_roi_evidence(self) -> None:
        evidence = self._evidence()
        with self.assertRaises(RealInferenceError):
            qwen.run_verification_qwen_vl(self.before, self.after, evidence.context, "model")
        with self.assertRaises(RealInferenceError):
            qwen.run_verification_qwen_vl(
                self.before, self.after, evidence.context, "model", before_roi=evidence.before_roi,
            )

    def test_independent_verifier_uses_only_two_roi_images_and_factual_context(self) -> None:
        evidence = self._evidence()
        factual = {**evidence.context, "event_type": "can", "camera_id": "CAM-1"}
        with patch.object(qwen, "_request_qwen", return_value=(_raw_verification(), 7)) as request:
            result = qwen.run_target_roi_verification(evidence.before_roi, evidence.after_roi, factual, "model")
        content = request.call_args.args[0]
        self.assertEqual(sum(item["type"] == "image_url" for item in content), 2)
        self.assertIn("independent target-ROI", content[0]["text"])
        self.assertEqual(result["verification_pass"], True)

    def test_parser_rejects_issue_and_action_contradictions(self) -> None:
        evidence = self._evidence()
        invalid = (
            {"verification_pass": "false"},
            {"confidence": True},
            {"confidence": float("inf")},
            {"issue_remaining": "false"},
            {"verification_pass": True, "issue_remaining": True},
            {"verification_pass": True, "next_action": "human_review"},
            {"verification_pass": False, "next_action": "close"},
            {"next_action": "anything"},
        )
        for changes in invalid:
            with self.subTest(changes=changes), patch.object(qwen, "_request_qwen", return_value=(_raw_verification(**changes), 1)):
                with self.assertRaises(RealInferenceError):
                    qwen.run_verification_qwen_vl(
                        self.before, self.after, evidence.context, "model",
                        before_roi=evidence.before_roi, after_roi=evidence.after_roi,
                    )

    def test_crop_hash_or_roi_contract_change_invalidates_existing_evidence_key(self) -> None:
        evidence = self._evidence()
        original = evidence_key([self.before, self.after], evidence.context, "model")
        changed_hash = deepcopy(evidence.context)
        changed_hash["target"]["crop_sha256"]["after"] = "0" * 64
        changed_roi = deepcopy(evidence.context)
        changed_roi["target"]["roi"]["x1"] = .01
        self.assertNotEqual(original, evidence_key([self.before, self.after], changed_hash, "model"))
        self.assertNotEqual(original, evidence_key([self.before, self.after], changed_roi, "model"))


class VerificationRuntimeRoiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = TemporaryDirectory()
        cls.old_database_path = connection.DATABASE_PATH
        connection.DATABASE_PATH = os.path.join(cls.temp.name, "verification-roi.db")
        connection.initialize_database()

    @classmethod
    def tearDownClass(cls) -> None:
        connection.DATABASE_PATH = cls.old_database_path
        cls.temp.cleanup()

    def setUp(self) -> None:
        reset_fleet_state()

    def _cleaning_completed_event(self) -> str:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-model")), \
                patch("demo_v1.service.run_event_qwen_vl", return_value=_review("can")):
            event_id = service.create_demo_event("demo03")["event_id"]
            service.edge_review(event_id)
            service.cloud_review(event_id)
            service.locate_event(event_id)
            service.assign_event(event_id)
            service.start_navigation(event_id)
            service.complete_navigation(event_id)
            service.complete_cleaning(event_id)
        return event_id

    def test_runtime_passes_generic_roi_context_and_in_memory_crops_to_one_verifier(self) -> None:
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-model")), \
                patch("demo_v1.service.run_event_qwen_vl", return_value=_review("can")), \
                patch("demo_v1.service.run_verification_qwen_vl", return_value={
                    "provider": "test", "source": "LIVE_MODEL", "issue_remaining": False,
                    "verification_pass": True, "confidence": .95, "next_action": "close", "elapsed_ms": 1,
                }) as verify, \
                patch("demo_v1.service.run_target_roi_verification") as independent:
            event_id = service.create_demo_event("demo03")["event_id"]
            service.edge_review(event_id)
            service.cloud_review(event_id)
            service.locate_event(event_id)
            service.assign_event(event_id)
            service.start_navigation(event_id)
            service.complete_navigation(event_id)
            service.complete_cleaning(event_id)
            result = service.verify_event(event_id)
        self.assertEqual(result["state"], "CLOSED")
        context = verify.call_args.args[2]
        self.assertEqual(context["verification_contract"], "target_roi.v1")
        self.assertEqual(context["target"]["object_type"], "can")
        self.assertEqual(verify.call_args.kwargs["before_roi"][:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(verify.call_args.kwargs["after_roi"][:8], b"\x89PNG\r\n\x1a\n")
        independent.assert_not_called()

    def test_failed_primary_uses_one_independent_roi_review_without_first_answer(self) -> None:
        event_id = self._cleaning_completed_event()
        first = _verification(passed=False, summary="PRIMARY_PRIVATE_ANSWER")
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-model")), \
                patch("demo_v1.service.run_verification_qwen_vl", return_value=first) as primary, \
                patch("demo_v1.service.run_target_roi_verification", return_value=_verification(passed=True)) as independent:
            result = service.verify_event(event_id)
        self.assertEqual(result["state"], "CLOSED")
        self.assertEqual(primary.call_count, 1)
        self.assertEqual(independent.call_count, 1)
        self.assertEqual(independent.call_args.args[0][:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(independent.call_args.args[1][:8], b"\x89PNG\r\n\x1a\n")
        second_context = independent.call_args.args[2]
        self.assertNotIn("PRIMARY_PRIVATE_ANSWER", str(second_context))
        self.assertNotIn("first_review", second_context)
        self.assertTrue(result["verification"]["independent_roi_review"])
        self.assertEqual(result["verification"]["first_review"]["evidence_summary"], "PRIMARY_PRIVATE_ANSWER")

    def test_second_roi_failure_or_low_confidence_remains_human_review(self) -> None:
        for second in (RealInferenceError("second transport unavailable"), _verification(passed=False), _verification(passed=True, confidence=.84)):
            with self.subTest(second=type(second).__name__):
                reset_fleet_state()
                event_id = self._cleaning_completed_event()
                target_call = (
                    patch("demo_v1.service.run_target_roi_verification", side_effect=second)
                    if isinstance(second, Exception)
                    else patch("demo_v1.service.run_target_roi_verification", return_value=second)
                )
                with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-model")), \
                        patch("demo_v1.service.run_verification_qwen_vl", return_value=_verification(passed=False)), \
                        target_call:
                    result = service.verify_event(event_id)
                self.assertEqual(result["state"], "HUMAN_REVIEW")
                self.assertTrue(result["verification"]["independent_roi_review"])

    def test_old_failed_replay_record_never_runs_live_target_roi_verifier(self) -> None:
        event_id = self._cleaning_completed_event()
        stored = get_event(event_id)
        assert stored is not None
        stored["demo_v1"]["mode"] = "STABLE_REPLAY"
        save_event(stored)
        with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-model")), \
                patch("demo_v1.service.load_replay_bundle", return_value={"verification": _verification(passed=False)}), \
                patch("demo_v1.service.run_verification_qwen_vl") as primary, \
                patch("demo_v1.service.run_target_roi_verification") as independent:
            result = service.verify_event(event_id)
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertEqual(result["error"]["code"], "VERIFICATION_UNAVAILABLE")
        primary.assert_not_called()
        independent.assert_not_called()

    def test_tampered_independent_replay_contract_cannot_close_event(self) -> None:
        for corrupt in ("missing_first", "wrong_digest", "false_marker", "missing_marker"):
            with self.subTest(corrupt=corrupt):
                reset_fleet_state()
                event_id = self._cleaning_completed_event()
                stored = get_event(event_id)
                assert stored is not None
                stored["demo_v1"]["mode"] = "STABLE_REPLAY"
                save_event(stored)
                replayed = {
                    **_verification(passed=True),
                    "independent_roi_review": True,
                    "first_review": _verification(passed=False),
                    "second_prompt_sha256": service.TARGET_ROI_VERIFICATION_PROMPT_SHA256,
                }
                if corrupt == "missing_first":
                    replayed.pop("first_review")
                elif corrupt == "wrong_digest":
                    replayed["second_prompt_sha256"] = "tampered"
                elif corrupt == "false_marker":
                    replayed["independent_roi_review"] = False
                else:
                    replayed.pop("independent_roi_review")
                    replayed.pop("second_prompt_sha256")
                with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-model")), \
                        patch("demo_v1.service.load_replay_bundle", return_value={"verification": replayed}), \
                        patch("demo_v1.service.run_verification_qwen_vl") as primary, \
                        patch("demo_v1.service.run_target_roi_verification") as independent:
                    result = service.verify_event(event_id)
                self.assertEqual(result["state"], "HUMAN_REVIEW")
                self.assertEqual(result["error"]["code"], "VERIFICATION_UNAVAILABLE")
                primary.assert_not_called()
                independent.assert_not_called()
