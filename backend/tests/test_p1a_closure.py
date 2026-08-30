"""P1-A runtime contract tests; only provider transport is replaced.

These deterministic tests do NOT constitute a real-model acceptance claim.
The separately opt-in live test verifies that boundary using actual cloud calls.
"""
from contextlib import ExitStack
import json
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from database import connection as db
from demo_v1 import service as runtime
from perception.yolo import RealInferenceError
from perception import qwen
from spatial.calibration import CalibrationError, CAMERAS


def _review(event_type, confidence=.91):
    return {"provider": "test transport", "model": "qwen-vl-max", "elapsed_ms": 120,
            "need_clean": True, "evidence_sufficient": True, "ambiguity_type": "none", "event_type": event_type, "decision_confidence": confidence,
            "severity": "medium", "surface_type": "asphalt" if event_type == "small_litter" else "tile",
            "next_action": "dispatch_robot", "evidence_summary": "Deterministic test fixture, not real AI.",
            "interference_factors": [], "recommended_capabilities": []}


def _verification(*args, **kwargs):
    return {"provider": "test transport", "verification_pass": True, "issue_remaining": False, "confidence": .95,
            "next_action": "close", "elapsed_ms": 130}


def _raw_review(event_type, confidence=.91):
    """Provider JSON, without the internal provenance/Phase 3 projection envelope."""
    projected = _review(event_type, confidence)
    return {"need_action": projected["need_clean"], "confidence": confidence,
            **{key: projected[key] for key in ("event_type", "evidence_sufficient", "ambiguity_type", "severity",
               "surface_type", "interference_factors", "evidence_summary", "recommended_capabilities")}}


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.original_db = db.DATABASE_PATH
        db.DATABASE_PATH = Path(self.temp.name) / "closure.sqlite"
        db.initialize_database()
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(runtime, "get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="qwen-vl-max")))
        self.cloud = self.stack.enter_context(patch.object(runtime, "run_event_qwen_vl", return_value=_review("small_litter")))
        self.second = self.stack.enter_context(patch.object(runtime, "run_targeted_event_qwen_vl", return_value=_review("small_litter", .96)))
        self.verify = self.stack.enter_context(patch.object(runtime, "run_verification_qwen_vl", side_effect=_verification))

    def tearDown(self):
        self.stack.close()
        db.DATABASE_PATH = self.original_db
        self.temp.cleanup()

    def reviewed(self, demo="demo01", mode="LIVE"):
        event_id = runtime.create_demo_event(demo, mode)["event_id"]
        runtime.edge_review(event_id)
        result = runtime.cloud_review(event_id)
        self.assertEqual(result["state"], "CLOUD_REVIEW", result.get("reason"))
        return event_id

    def finish(self, event_id):
        runtime.locate_event(event_id)
        assigned = runtime.assign_event(event_id)
        if assigned["state"] == "HUMAN_FALLBACK":
            return runtime.complete_demo04_manual(event_id)
        runtime.start_navigation(event_id)
        runtime.complete_navigation(event_id)
        runtime.complete_cleaning(event_id)
        return runtime.verify_event(event_id)

    def forbid_cloud(self):
        for call in (self.cloud, self.second, self.verify):
            call.reset_mock()
            call.side_effect = AssertionError("Replay must not invoke model transport")

    def test_replay_reruns_algorithms_and_durable_task_transitions(self):
        live_id = self.reviewed()
        live = self.finish(live_id)
        records = db.list_model_records(live["source_event_id"], "event_review")
        self.assertEqual(records[0]["payload"]["event_id"], live_id)
        self.forbid_cloud()
        # A changed Fleet fact must be consumed, not the LIVE assignment snapshot.
        db.update_fleet_robot("robot-a", battery=73, coordinates={"x": 12, "y": 13})
        with ExitStack() as spies:
            calls = {name: spies.enter_context(patch.object(runtime, name, wraps=getattr(runtime, name))) for name in (
                "map_pixel_to_slam", "evaluate_capabilities", "make_assignment_decision", "plan_route", "update_fleet_robot", "save_event", "record_transition",
            )}
            replay_id = self.reviewed(mode="STABLE_REPLAY")
            replay = self.finish(replay_id)
        for name, call in calls.items():
            self.assertGreater(call.call_count, 0, name)
        self.assertNotEqual(replay_id, live_id)
        self.assertEqual(replay["state"], "CLOSED")
        self.assertEqual(replay["qwen_review"]["source"], "REPLAY")
        self.assertEqual(replay["verification"]["source"], "REPLAY")
        self.assertIsNone(replay["qwen_review"]["elapsed_ms"])
        self.assertEqual(replay["qwen_review"]["replay_event_id"], live_id)
        self.assertEqual(next(r for r in db.get_fleet_state() if r["id"] == "robot-a")["battery"], 71)
        self.assertEqual([t["state"] for t in db.get_transitions(replay_id)], ["DETECTED", "EDGE_DETECTED", "SINGLE_VIEW_REVIEW", "CLOUD_REVIEW", "LOCATED", "ASSIGNED", "NAVIGATING", "ARRIVED", "CLEANING_COMPLETED", "VERIFYING", "CLOSED"])
        for call in (self.cloud, self.second, self.verify):
            call.assert_not_called()
        self.assertEqual(len(db.list_model_records(live["source_event_id"], "event_review")), 1)

    def test_replay_plan_uses_current_fleet_map(self):
        self.cloud.return_value = _review("can")
        self.finish(self.reviewed("demo03"))
        db.update_fleet_robot("robot-c", map_id="B_2F", building="B", floor="2F", battery=80)
        self.forbid_cloud()
        result = self.finish(self.reviewed("demo03", "STABLE_REPLAY"))
        self.assertEqual(result["navigation_plan"]["start_map"], "B_2F")
        self.assertEqual(result["navigation_plan"]["target_map"], "A_2F")

    def test_demo04_replay_zero_capability_human_verification_closure(self):
        self.cloud.return_value = _review("large_object")
        live_id = self.reviewed("demo04")
        live = self.finish(live_id)
        self.assertEqual(live["state"], "CLOSED")
        before = db.get_fleet_state()
        self.forbid_cloud()
        with patch.object(runtime, "evaluate_capabilities", wraps=runtime.evaluate_capabilities) as capability:
            replay_id = self.reviewed("demo04", "STABLE_REPLAY")
            replay = self.finish(replay_id)
        capability.assert_called_once()
        decision = replay["assignment_decision"]
        self.assertEqual(decision["candidate_count"], 0)
        self.assertEqual(decision["status"], "HUMAN_FALLBACK")
        self.assertIsNone(decision["selected_robot_id"])
        self.assertEqual(replay["state"], "CLOSED")
        self.assertEqual(replay["human_work_order"]["status"], "COMPLETED")
        self.assertEqual(replay["verification"]["source"], "REPLAY")
        self.assertEqual(db.get_fleet_state(), before)
        self.assertEqual([t["state"] for t in db.get_transitions(replay_id)], ["DETECTED", "EDGE_DETECTED", "SINGLE_VIEW_REVIEW", "CLOUD_REVIEW", "LOCATED", "HUMAN_FALLBACK", "VERIFYING", "CLOSED"])

    def test_confirmed_context_reaches_first_and_independent_review(self):
        event_id = runtime.create_demo_event("demo04")["event_id"]
        runtime.edge_review(event_id)
        with patch.object(runtime, "run_event_qwen_vl", wraps=qwen.run_event_qwen_vl), patch.object(runtime, "run_targeted_event_qwen_vl", wraps=qwen.run_targeted_event_qwen_vl), patch.object(qwen, "_request_qwen", side_effect=[(_raw_review("large_object", .7), 1), (_raw_review("large_object", .95), 2)]) as transport:
            reviewed = runtime.cloud_review(event_id)
        self.assertEqual(transport.call_count, 2)
        for call in transport.call_args_list:
            prompt = call.args[0][0]["text"]
            context = json.loads(prompt.split("Context JSON: ", 1)[1])
            operational = context["cameras"][0]["operational_context"]
            self.assertEqual(operational["zone_type"], "egress_or_public_corridor")
            self.assertEqual(operational["storage_policy"], "objects_not_allowed_to_remain")
            self.assertEqual(operational["object_context"], "confirmed_discarded_items_awaiting_removal")
            self.assertNotIn("expected_robot", prompt)
            self.assertNotIn("HUMAN_FALLBACK", prompt)
            self.assertNotIn("Deterministic test fixture", prompt)  # no prior model answer
        self.assertEqual(reviewed["state"], "CLOUD_REVIEW")
        self.assertIsNone(reviewed["assignment_decision"])
        self.assertEqual(db.get_event(event_id)["demo_v1"]["cloud_context"], reviewed["cloud_context"])

    def test_confirmed_context_does_not_override_model_veto(self):
        self.cloud.return_value = {**_review("large_object", .95), "need_clean": False, "next_action": "ignore"}
        event_id = runtime.create_demo_event("demo04")["event_id"]
        runtime.edge_review(event_id)
        reviewed = runtime.cloud_review(event_id)
        self.assertEqual(reviewed["state"], "HUMAN_REVIEW")
        self.assertFalse(reviewed["qwen_review"]["need_clean"])
        self.assertEqual(reviewed["qwen_review"]["decision_confidence"], .95)
        self.assertIsNone(reviewed["assignment_decision"])

    def test_context_is_event_scoped_and_invalidates_replay_when_changed(self):
        self.cloud.return_value = _review("large_object")
        self.finish(self.reviewed("demo04"))
        event_id = runtime.create_demo_event("demo04", "STABLE_REPLAY")["event_id"]
        stored = db.get_event(event_id)
        stored["demo_v1"]["asset_manifest"]["scene_context"]["object_context"] = "unconfirmed"
        db.save_event(stored)
        runtime.edge_review(event_id)
        self.assertEqual(runtime.cloud_review(event_id)["state"], "HUMAN_REVIEW")
        other = runtime.create_demo_event("demo01")
        self.assertNotIn("object_context", other["asset_manifest"]["scene_context"])

    def test_demo_id_and_cloud_action_cannot_force_human_fallback(self):
        # Deliberate contradictory model recommendation: capability still decides.
        self.cloud.return_value = {**_review("can"), "next_action": "human_review"}
        event_id = self.reviewed("demo04")
        runtime.locate_event(event_id)
        result = runtime.assign_event(event_id)
        self.assertEqual(result["state"], "ASSIGNED")
        self.assertGreater(result["assignment_decision"]["candidate_count"], 0)
        self.assertEqual(result["assignment_decision"]["selected_robot_id"], "robot-c")

    def test_replay_preserves_first_and_independent_second_responses(self):
        self.cloud.return_value = _review("small_litter", .70)
        live_id = self.reviewed()
        self.finish(live_id)
        self.forbid_cloud()
        replay = db.get_event(self.reviewed(mode="STABLE_REPLAY"))["demo_v1"]
        self.assertEqual(replay["first_qwen_review"]["decision_confidence"], .70)
        self.assertEqual(replay["second_qwen_review"]["decision_confidence"], .96)
        self.assertEqual(replay["second_qwen_review"]["source"], "REPLAY")

    def test_missing_replay_fails_safely_without_assign_or_cloud(self):
        self.forbid_cloud()
        event_id = runtime.create_demo_event("demo01", "STABLE_REPLAY")["event_id"]
        runtime.edge_review(event_id)
        result = runtime.cloud_review(event_id)
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertIsNone(result["assignment_decision"])
        self.assertEqual(db.get_transitions(event_id)[-1]["detail"]["reason"], "replay_record_unavailable")

    def test_compatibility_runner_has_no_synthetic_replay(self):
        self.forbid_cloud()
        result = runtime.run_demo("demo01", mode="replay")
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertIsNone(result["qwen_review"])
        self.assertIsNone(result["assignment_decision"])

    def test_raw_provider_bool_and_confidence_types_are_strict(self):
        for adapter in (qwen.run_event_qwen_vl, qwen.run_targeted_event_qwen_vl):
            for change in ({"need_action": "false"}, {"confidence": True}, {"confidence": float("nan")}, {"severity": []}, {"severity": {}}):
                with self.subTest(adapter=adapter.__name__, change=change), patch.object(qwen, "_request_qwen", return_value=({**_raw_review("small_litter"), **change}, 1)):
                    with self.assertRaises(RealInferenceError):
                        adapter([], [], [], "model")
        for change in ({"verification_pass": "false"}, {"confidence": True}, {"confidence": float("inf")}, {"next_action": []}, {"next_action": {}}, {"issue_remaining": True}):
            with self.subTest(change=change), patch.object(qwen, "_request_qwen", return_value=({**_verification(), **change}, 1)) as request, patch.object(qwen, "_image_data_url", return_value="test-image"):
                with self.assertRaises(RealInferenceError):
                    qwen.run_verification_qwen_vl(Path("before"), Path("after"), {}, "model", before_roi=b"before", after_roi=b"after")
                request.assert_called_once()

    def test_replay_verification_rejects_same_contradictions_as_live(self):
        from demo_v1.replay import validate_response
        for change in ({"issue_remaining": True}, {"issue_remaining": "false"}, {"next_action": []}, {"verification_pass": False}):
            with self.subTest(change=change), self.assertRaises(RealInferenceError):
                validate_response({**_verification(), **change}, "verification")

    def test_raw_provider_invalid_boolean_cannot_close_runtime(self):
        event_id = self.reviewed()
        runtime.locate_event(event_id)
        runtime.assign_event(event_id)
        runtime.start_navigation(event_id)
        runtime.complete_navigation(event_id)
        runtime.complete_cleaning(event_id)
        with patch.object(runtime, "run_verification_qwen_vl", wraps=qwen.run_verification_qwen_vl), patch.object(qwen, "_request_qwen", return_value=({**_verification(), "verification_pass": "false", "confidence": True}, 1)):
            result = runtime.verify_event(event_id)
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertEqual(result["error"]["error_type"], "VERIFICATION_ERROR")

    def test_changed_model_or_evidence_cannot_reuse_stale_record(self):
        self.finish(self.reviewed())
        for change in ("model", "image"):
            with self.subTest(change=change):
                event_id = runtime.create_demo_event("demo01", "STABLE_REPLAY")["event_id"]
                runtime.edge_review(event_id)
                with ExitStack() as stack:
                    if change == "model":
                        stack.enter_context(patch.object(runtime, "get_runtime", return_value=SimpleNamespace(qwen_model="different-model", qwen_ready=True)))
                    else:
                        stack.enter_context(patch("demo_v1.replay.Path.read_bytes", return_value=b"different evidence"))
                    self.assertEqual(runtime.cloud_review(event_id)["state"], "HUMAN_REVIEW")

    def test_malformed_or_nonlive_records_never_become_success(self):
        live_id = self.reviewed()
        row = db.list_model_records(db.get_event(live_id)["demo_v1"]["source_event_id"], "event_review")[0]
        for fault in ("schema", "confidence", "missing_second", "source"):
            with self.subTest(fault=fault):
                payload = deepcopy(row["payload"])
                if fault == "schema":
                    payload["schema"] = "unversioned"
                elif fault == "confidence":
                    payload["responses"]["first"]["decision_confidence"] = float("nan")
                elif fault == "missing_second":
                    payload["responses"]["first"]["decision_confidence"] = .7
                else:
                    payload["event_id"] = "missing-event"
                with db.database_session() as connection:
                    connection.execute("DELETE FROM model_records")
                db.save_model_record("event-outdoor-tissue-001", "event_review", "LIVE", payload)
                event_id = runtime.create_demo_event("demo01", "STABLE_REPLAY")["event_id"]
                runtime.edge_review(event_id)
                self.assertEqual(runtime.cloud_review(event_id)["state"], "HUMAN_REVIEW")

    def test_live_failure_never_automatically_loads_existing_replay(self):
        self.finish(self.reviewed())
        for configured in (True, False):
            with self.subTest(configured=configured), patch.object(runtime, "load_perception_record") as replay, patch.object(runtime, "get_runtime", return_value=SimpleNamespace(qwen_ready=configured, qwen_model="qwen-vl-max")):
                self.cloud.side_effect = RealInferenceError("provider unavailable")
                event_id = runtime.create_demo_event("demo01")["event_id"]
                runtime.edge_review(event_id)
                result = runtime.cloud_review(event_id)
                self.assertEqual(result["mode"], "LIVE")
                self.assertEqual(result["state"], "HUMAN_REVIEW")
                replay.assert_not_called()

    def test_malformed_live_response_safely_stops_before_assignment(self):
        for response in (None, {}, {**_review("small_litter"), "event_type": None}, {**_review("small_litter"), "decision_confidence": float("nan")}):
            with self.subTest(response=response):
                self.cloud.return_value = response
                event_id = runtime.create_demo_event("demo01")["event_id"]
                runtime.edge_review(event_id)
                result = runtime.cloud_review(event_id)
                self.assertEqual(result["state"], "HUMAN_REVIEW")
                self.assertIsNone(result["assignment_decision"])

    def test_replay_missing_after_record_is_durable_verification_failure(self):
        self.reviewed()  # LIVE semantic record exists but no verification record.
        self.forbid_cloud()
        event_id = self.reviewed(mode="STABLE_REPLAY")
        result = self.finish(event_id)
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertEqual(result["error"]["error_type"], "VERIFICATION_ERROR")
        self.assertEqual(db.get_transitions(event_id)[-2]["state"], "VERIFYING")
        self.assertIsNone(next(r for r in db.get_fleet_state() if r["id"] == "robot-a")["active_event_id"])

    def assert_spatial_failure(self, event_id):
        fleet = db.get_fleet_state()
        with patch.object(runtime, "make_assignment_decision") as scheduler, patch.object(runtime, "plan_route") as planner:
            result = runtime.locate_event(event_id)
            self.assertEqual(result["state"], "HUMAN_REVIEW")
            self.assertEqual(result["error"]["error_type"], "SPATIAL_ERROR")
            self.assertIsNone(result.get("spatial_location"))
            self.assertIsNone(result["assignment_decision"])
            self.assertIsNone(result["navigation_plan"])
            with self.assertRaises(ValueError):
                runtime.assign_event(event_id)
            with self.assertRaises(ValueError):
                runtime.start_navigation(event_id)
            scheduler.assert_not_called()
            planner.assert_not_called()
        self.assertEqual(db.get_fleet_state(), fleet)
        self.assertEqual(db.get_event(event_id)["demo_v1"]["error"]["error_type"], "SPATIAL_ERROR")
        self.assertEqual(db.get_transitions(event_id)[-1]["detail"]["error_type"], "SPATIAL_ERROR")

    def test_unknown_camera_fails_before_scheduler(self):
        event_id = self.reviewed()
        stored = db.get_event(event_id)
        runtime._primary_asset(stored["demo_v1"])["camera_id"] = "UNKNOWN"
        db.save_event(stored)
        self.assert_spatial_failure(event_id)

    def test_missing_camera_calibration_fails_before_scheduler(self):
        event_id = self.reviewed()
        cameras = deepcopy(CAMERAS)
        for camera in cameras:
            camera["calibration_points"] = []
        with patch("spatial.calibration.CAMERAS", cameras):
            self.assert_spatial_failure(event_id)

    def test_mapping_error_fails_before_scheduler(self):
        event_id = self.reviewed()
        with patch.object(runtime, "map_pixel_to_slam", side_effect=CalibrationError("degenerate calibration")):
            self.assert_spatial_failure(event_id)

    def test_invalid_mapping_output_never_produces_route(self):
        for value in ({}, {"map_id": "OUTDOOR", "x": float("nan"), "y": 1}, {"map_id": "OUTDOOR", "x": 999999, "y": 1}):
            with self.subTest(value=value):
                event_id = self.reviewed()
                with patch.object(runtime, "map_pixel_to_slam", return_value={"location": value}):
                    self.assert_spatial_failure(event_id)

    def test_invalid_bbox_never_produces_route(self):
        for bbox in ({}, {"x1": .8, "y1": .1, "x2": .2, "y2": .5}, {"x1": float("nan"), "y1": .1, "x2": .5, "y2": .5}):
            with self.subTest(bbox=bbox):
                event_id = self.reviewed()
                stored = db.get_event(event_id)
                runtime._primary_asset(stored["demo_v1"])["detection_overlays"][0]["bbox"] = bbox
                db.save_event(stored)
                self.assert_spatial_failure(event_id)

    def test_liquid_representative_point_is_shared_mapping_input(self):
        bbox = {"x1": .2, "y1": .3, "x2": .6, "y2": .7}
        u, v, kind = runtime._ground_point_from_bbox(bbox, "liquid")
        self.assertAlmostEqual(u, 420)
        self.assertAlmostEqual(v, 436)
        self.assertEqual(kind, "region_lower_center")


if __name__ == "__main__":
    unittest.main()
