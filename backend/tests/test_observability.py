"""P1-H read-only projection and runtime instrumentation contracts."""
from contextlib import ExitStack
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException
from database import connection as db
from demo_v1 import service as workflow
from observability.context import trace_context
from observability.errors import classify, ERROR_TYPES
from observability.redaction import safe
from observability.requests import traced_model_request
from observability.routes import get_trace
from observability.service import trace_view
from perception.multiview.autonomous import _audit_entry
from robot_operations import repository as repo, tasks, agent
from tests import test_p1a_closure as closure


class ObservabilityTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.original = db.DATABASE_PATH
        db.DATABASE_PATH = Path(self.temp.name) / "trace.sqlite"
        db.initialize_database()
        repo.initialize()

    def tearDown(self):
        db.DATABASE_PATH = self.original
        self.temp.cleanup()

    def event(self):
        return workflow.create_demo_event("demo01", "LIVE")["event_id"]

    def database_dump(self):
        with db.database_session() as connection:
            return "\n".join(connection.iterdump())

    def test_new_trace_is_independent_stable_and_persisted_on_transitions(self):
        event_id = self.event()
        trace_id = db.get_event(event_id)["trace_id"]
        self.assertTrue(trace_id.startswith("trace-"))
        self.assertNotEqual(event_id, trace_id)
        workflow.edge_review(event_id)
        db.initialize_database()
        self.assertEqual(db.get_event(event_id)["trace_id"], trace_id)
        self.assertEqual({row["trace_id"] for row in db.get_transitions(event_id)}, {trace_id})
        self.assertNotEqual(db.get_event(self.event())["trace_id"], trace_id)

    def test_legacy_read_has_no_trace_backfill_or_runtime_side_effect(self):
        event_id = self.event()
        event = db.get_event(event_id)
        del event["trace_id"]
        event["demo_v1"].pop("trace_id", None)
        with db.database_session() as connection:
            connection.execute("UPDATE cleaning_events SET payload=? WHERE event_id=?", (json.dumps(event), event_id))
        before = self.database_dump()
        with ExitStack() as stack:
            for name in ("map_pixel_to_slam", "evaluate_capabilities", "make_assignment_decision", "plan_route", "update_fleet_robot", "run_event_qwen_vl"):
                stack.enter_context(patch.object(workflow, name, side_effect=AssertionError("GET may not execute runtime")))
            result = get_trace(event_id)
            get_trace(event_id)
        self.assertEqual(result["trace_status"], "LEGACY_MISSING")
        self.assertIsNone(result["trace_id"])
        self.assertEqual(before, self.database_dump())

    def test_ten_nodes_and_not_executed_sources_are_truthful(self):
        result = trace_view(self.event())
        self.assertEqual(sum(node["group"] == "AI" for node in result["nodes"]), 6)
        self.assertEqual(sum(node["group"] == "SPATIAL" for node in result["nodes"]), 4)
        self.assertEqual(next(node for node in result["nodes"] if node["id"] == "single_view")["source"], "NOT_RECORDED")
        self.assertTrue(all(node["start_time"] is None for node in result["nodes"]))
        self.assertIn("AUTH REQUIRED / NOT CONNECTED", {row["status"] for row in result["reality"]})

    def test_sufficient_evidence_does_not_fabricate_agent_activity(self):
        event_id = self.event()
        event = db.get_event(event_id)
        event["demo_v1"]["first_qwen_review"] = {"evidence_sufficient": True, "confidence": .99}
        db.save_event(event)
        result = trace_view(event_id)
        node = next(node for node in result["nodes"] if node["id"] == "multi_view_agent")
        self.assertEqual(node["status"], "NOT_TRIGGERED / EVIDENCE_ALREADY_SUFFICIENT")
        self.assertEqual(result["tool_calls"], [])

    def test_request_metadata_is_linked_and_never_stores_request_body(self):
        event_id = self.event()
        trace_id = db.get_event(event_id)["trace_id"]
        @traced_model_request
        def transport(content, model, **kwargs):
            return {"answer": True}
        with trace_context(trace_id):
            transport({"secret": "never-store-body"}, "qwen-vl-max", tools=[{}])
        result = trace_view(event_id)
        node = next(node for node in result["nodes"] if node["group"] == "RUNTIME")
        self.assertEqual(node["trace_id"], trace_id)
        self.assertEqual(node["status"], "SUCCESS")
        self.assertIsNotNone(node["start_time"])
        self.assertGreaterEqual(node["duration_ms"], 0)
        self.assertNotIn("never-store-body", self.database_dump())

    def test_failed_request_is_model_error_without_provider_secret(self):
        event_id = self.event()
        @traced_model_request
        def transport(content, model, **kwargs):
            raise ValueError("sk-secret-provider-token")
        with trace_context(db.get_event(event_id)["trace_id"]), self.assertRaises(ValueError):
            transport([], "qwen-vl-max")
        result = trace_view(event_id)
        node = next(node for node in result["nodes"] if node["group"] == "RUNTIME")
        self.assertEqual(node["error"]["type"], "MODEL_ERROR")
        self.assertNotIn("sk-secret", json.dumps(result))

    def test_model_payload_not_modified_by_trace_column(self):
        event_id = self.event()
        payload = {"canonical": [1, 2, 3], "source": "LIVE_MODEL"}
        with trace_context(db.get_event(event_id)["trace_id"]):
            db.save_model_record("source-event", "review", "LIVE", payload)
        with db.database_session() as connection:
            row = connection.execute("SELECT payload,trace_id FROM model_records").fetchone()
        self.assertEqual(json.loads(row["payload"]), payload)
        self.assertEqual(row["trace_id"], db.get_event(event_id)["trace_id"])

    def test_actual_stage_and_tool_durations_not_transition_or_model_latency(self):
        event_id = self.event()
        workflow.edge_review(event_id)
        result = trace_view(event_id)
        span = next(call for call in result["tool_calls"] if call["name"] == "edge_review")
        self.assertEqual(span["trigger_source"], "SYSTEM_WORKFLOW")
        self.assertIsNotNone(span["start_time"])
        self.assertGreaterEqual(span["duration_ms"], 0)
        audit = []
        _audit_entry(audit, {"name": "fetch_camera_evidence", "elapsed_ms": 9999}, None)
        self.assertNotIn("tool_duration_ms", audit[0])

    def test_recursive_api_redaction_and_evidence_urls(self):
        event_id = self.event()
        event = db.get_event(event_id)
        event["demo_v1"]["first_qwen_review"] = {"provider": "test", "confidence": .9,
            "evidence_summary": "Bearer private-token", "reasoning": "PRIVATE_CHAIN", "prompt": "PRIVATE_PROMPT", "raw": "PRIVATE_RAW"}
        event["demo_v1"]["asset_manifest"] = {"assets": [{"role": "before", "camera_id": "CAM-A1-01", "url": "/demo-assets/img.png?api_key=secret"}]}
        db.save_event(event)
        result = json.dumps(trace_view(event_id))
        for hidden in ("private-token", "PRIVATE_CHAIN", "PRIVATE_PROMPT", "PRIVATE_RAW", "api_key=secret"):
            self.assertNotIn(hidden, result)
        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": "opaque-credential"}):
            self.assertEqual(safe({"evidence_summary": "opaque-credential"})["evidence_summary"], "[REDACTED]")
        self.assertEqual(safe({"raw": {"confidence": .9}, "confidence": float("nan")}), {"confidence": None})

    def test_taxonomy_and_normal_human_fallback(self):
        for kind in ERROR_TYPES:
            self.assertEqual(classify({"type": kind})["type"], kind)
        self.assertEqual(classify("mapping_failed")["type"], "SPATIAL_ERROR")
        self.assertEqual(classify("model_tool_turn_failed")["type"], "MODEL_ERROR")
        self.assertNotIn("TOP_SECRET", json.dumps(classify({"type": "MODEL_ERROR", "code": "token=TOP_SECRET"})))
        event_id = self.event()
        event = db.get_event(event_id)
        event.update(state="HUMAN_FALLBACK", assignment_decision={"candidate_count": 0, "status": "HUMAN_FALLBACK"})
        db.save_event(event)
        result = trace_view(event_id)
        self.assertEqual(result["errors"], [])
        self.assertEqual(next(node for node in result["nodes"] if node["id"] == "scheduler")["status"], "ZERO_CANDIDATE / HUMAN_FALLBACK")

    def test_unknown_event_is_404_without_writes(self):
        before = self.database_dump()
        with self.assertRaises(HTTPException) as error:
            get_trace("integrated-unknown")
        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(before, self.database_dump())

    def test_task_has_persisted_event_and_session_trace_links(self):
        event_id = self.event()
        session = repo.new_session()
        task = tasks.create_task(session["id"], "cleaning", event_id=event_id)
        self.assertEqual(task["trace_id"], db.get_event(event_id)["trace_id"])
        self.assertEqual(task["session_trace_id"], session["trace_id"])
        result = trace_view(event_id)
        self.assertEqual(result["linked_tasks"][0]["task_id"], task["task_id"])

    def test_shared_session_does_not_cross_attribute_request_or_task_traces(self):
        session = repo.new_session()
        first_id, second_id = self.event(), self.event()
        @traced_model_request
        def transport(content, model, **kwargs):
            return {"ok": True}
        def run(session_id, messages, instruction):
            transport([], "test-" + instruction)
            task = tasks.create_task(session_id, "delivery", origin_poi="a1-delivery", destination_poi="a2-corridor") if instruction == "delivery" else tasks.create_task(session_id, "cleaning", event_id=instruction)
            repo.audit(session_id, phase="tool", tool="create_task", task_id=task["task_id"], policy="ALLOW")
            return "created", [{"ok": True, "tool": "create_task"}]
        with patch.object(agent, "run_loop", side_effect=run):
            for instruction in (first_id, second_id, "delivery"):
                agent.send_message(session["id"], instruction, {})
        first = trace_view(first_id)
        second = trace_view(second_id)
        first_models = [node for node in first["nodes"] if node["group"] == "RUNTIME"]
        self.assertEqual(len(first_models), 1)
        self.assertEqual(first_models[0]["output_summary"]["model"], "test-" + first_id)
        self.assertNotEqual(first_models[0]["trace_id"], next(node for node in second["nodes"] if node["group"] == "RUNTIME")["trace_id"])
        self.assertEqual(len(first["tool_calls"]), 1)
        self.assertNotIn(second_id, json.dumps(first))
        self.assertEqual(len({task["trace_id"] for task in repo.tasks(session["id"])}), 3)


class ReplayTraceTests(TestCase):
    def test_replay_new_trace_no_new_model_request_and_real_spans(self):
        harness = closure.ClosureTests()
        harness.setUp()
        self.addCleanup(harness.tearDown)
        live_id = harness.reviewed()
        harness.finish(live_id)
        live_trace = db.get_event(live_id)["trace_id"]
        harness.forbid_cloud()
        replay_id = harness.reviewed(mode="STABLE_REPLAY")
        harness.finish(replay_id)
        result = trace_view(replay_id)
        self.assertNotEqual(result["trace_id"], live_trace)
        self.assertEqual(result["runtime"]["last_request_status"], "REPLAY / NO_NEW_MODEL_CALL")
        self.assertIsNone(result["runtime"]["last_latency_ms"])
        single = next(node for node in result["nodes"] if node["id"] == "single_view")
        self.assertEqual(single["source"], "REPLAY")
        self.assertIsNone(single["duration_ms"])
        self.assertIn("locate_event", {call["name"] for call in result["tool_calls"]})
        self.assertIn("verify_event", {call["name"] for call in result["tool_calls"]})
