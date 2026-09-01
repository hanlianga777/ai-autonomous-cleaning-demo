"""Operations tests inject model transport only; task/Fleet/SQLite stay real."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
from unittest.mock import patch

from database import connection as db
from demo_v1 import service as workflow
from robot_operations import agent, repository as repo, tasks, tools
from robot_operations.catalog import DELIVERY_ADAPTERS
from robot_operations.coordination import task_lease
from robot_operations.routes import action
from api.routes import post_demo_v1_manual_completion
from fastapi import HTTPException


def call(name, args, id="call-1"):
    return {"role": "assistant", "tool_calls": [{"id": id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}, 12


class RobotOperationsTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.original = db.DATABASE_PATH
        db.DATABASE_PATH = Path(self.temp.name) / "operations.sqlite"
        db.initialize_database()
        repo.initialize()
        self.session_id = repo.new_session()["id"]

    def tearDown(self):
        db.DATABASE_PATH = self.original
        self.temp.cleanup()

    def delivery(self):
        return tasks.create_task(self.session_id, "delivery", origin_poi="a1-delivery", destination_poi="a2-corridor")

    def test_new_show_session_resets_only_current_fleet_and_agent_context(self):
        task = self.delivery()
        tasks.control(task["task_id"], "dispatch")
        first = repo.begin_show_session()
        second = repo.begin_show_session()
        self.assertNotEqual(first["id"], second["id"])
        self.assertNotEqual(first["agent_session_id"], second["agent_session_id"])
        self.assertEqual(repo.current_show_session()["id"], second["id"])
        self.assertFalse(any(robot.get("active_task_id") for robot in db.get_fleet_state()))
        self.assertEqual(repo.snapshot(second["agent_session_id"])["messages"], [])
        # Existing audit/task storage is retained for historical accountability.
        self.assertEqual(repo.get("task", task["task_id"])["status"], "ASSIGNED")

    def test_chat_history_is_newest_first_and_read_only_projection(self):
        first = self.session_id
        repo.message(repo.get("session", first), "user", "先前的问题")
        second = repo.new_session()["id"]
        repo.message(repo.get("session", second), "assistant", "最新的答复")
        index = repo.session_history_index()["sessions"]
        self.assertEqual(index[0]["id"], second)
        self.assertEqual(index[0]["preview"], "最新的答复")
        detail = repo.session_history(first)
        self.assertEqual(detail["id"], first)
        self.assertEqual(detail["messages"][0]["content"], "先前的问题")
        self.assertNotIn("tasks", detail)
        self.assertNotIn("audits", detail)
        self.assertNotIn("page_context", detail)

    def test_delivery_real_state_machine_atomic_fleet_and_restart(self):
        task = self.delivery()
        task = tasks.control(task["task_id"], "dispatch")
        self.assertEqual(task["status"], "ASSIGNED")
        self.assertEqual(tasks.robot("robot-d")["active_task_id"], task["task_id"])
        visited = []
        while task["status"] != "CLOSED":
            task = tasks.advance(task["task_id"])
            visited.append(task["status"])
        self.assertIn("ELEVATOR_TRANSIT", visited)
        self.assertEqual(tasks.robot("robot-d")["map_id"], "A_2F")
        self.assertIsNone(tasks.robot("robot-d")["active_task_id"])
        expected = tasks.robot("robot-d")
        # New interpreter + new SQLite connection, not the same object lifetime.
        script = "import json,sys; from pathlib import Path; from database import connection as d; d.DATABASE_PATH=Path(sys.argv[1]); d.initialize_database(); print(json.dumps(d.get_fleet_state()))"
        restored = json.loads(subprocess.check_output([sys.executable, "-c", script, str(db.DATABASE_PATH)], text=True))
        self.assertEqual(next(robot for robot in restored if robot["id"] == "robot-d"), expected)
        self.assertEqual(repo.get("task", task["task_id"])["status"], "CLOSED")

    def test_pause_resume_cancel_and_reset_do_not_teleport_robot(self):
        task = self.delivery()
        tasks.control(task["task_id"], "dispatch")
        tasks.advance(task["task_id"])
        tasks.control(task["task_id"], "pause")
        with self.assertRaises(ValueError):
            tasks.advance(task["task_id"])
        with self.assertRaises(ValueError):
            db.reset_fleet_state()
        tasks.control(task["task_id"], "resume")
        tasks.advance(task["task_id"])
        location = tasks.robot("robot-d")["coordinates"]
        tasks.control(task["task_id"], "cancel")
        self.assertEqual(tasks.robot("robot-d")["coordinates"], location)
        self.assertIsNone(tasks.robot("robot-d")["active_task_id"])
        with self.assertRaises(ValueError):
            tasks.control(task["task_id"], "dispatch")

    def test_concurrent_dispatch_only_one_reservation(self):
        first, second = self.delivery(), self.delivery()
        def dispatch(task):
            try:
                return tasks.control(task["task_id"], "dispatch")["task_id"]
            except ValueError:
                return None
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(dispatch, [first, second]))
        self.assertEqual(sum(bool(item) for item in results), 1)
        self.assertIn(tasks.robot("robot-d")["active_task_id"], results)

    def test_relocation_approved_poi_scope_and_dijkstra(self):
        with self.assertRaises(ValueError):
            tasks.create_task(self.session_id, "relocation", robot_id="robot-b", destination_poi="b1-lobby")
        task = tasks.create_task(self.session_id, "relocation", robot_id="robot-b", destination_poi="a1-lobby")
        dispatched = tasks.control(task["task_id"], "dispatch")
        self.assertEqual(dispatched["route"]["to_origin"]["node_path"], ["A_1F"])
        while tasks.get_task(task["task_id"])["status"] != "CLOSED":
            tasks.advance(task["task_id"])
        self.assertEqual(tasks.robot("robot-b")["coordinates"], {"x": 52, "y": 29})

    def test_policy_denies_configuration_coordinates_robot_selection_and_foreign_session(self):
        common = {"session_id": self.session_id, "instruction": "帮我处理"}
        for name in ("update_slam_map", "modify_no_go_zone", "change_scheduler_policy", "change_threshold", "change_robot_capability"):
            with self.assertRaises(ValueError):
                tools.execute(name, {}, **common)
        with self.assertRaises(ValueError):
            tools.execute("create_relocation_task", {"robot_id": "robot-b", "destination_poi": "a1-lobby"}, **common)
        with self.assertRaises(ValueError):
            tools.execute("create_relocation_task", {"robot_id": "robot-b", "destination_poi": "a1-lobby", "x": 3}, session_id=self.session_id, instruction="高仙去大堂")
        with self.assertRaises(ValueError):
            tools.execute("create_delivery_task", {"origin_poi": "a1-delivery", "destination_poi": "a2-corridor"}, read_only=True, **common)
        task = self.delivery()
        with self.assertRaises(ValueError):
            tools.execute("dispatch_task", {"task_id": task["task_id"]}, session_id=repo.new_session()["id"], instruction="派发")

    def test_cleaning_uses_persisted_event_never_synthesizes_or_selects_robot(self):
        with self.assertRaises(ValueError):
            tasks.create_task(self.session_id, "cleaning", event_id="invented")
        event = workflow.create_demo_event("demo01")
        task = tasks.create_task(self.session_id, "cleaning", event_id=event["event_id"])
        with self.assertRaises(ValueError):
            tasks.create_task(self.session_id, "cleaning", event_id=event["event_id"])
        tasks.control(task["task_id"], "dispatch")
        advanced = tasks.advance(task["task_id"])
        self.assertEqual(advanced["status"], "EDGE_DETECTED")
        self.assertIsNone(advanced["robot_id"])
        self.assertIsNone(db.get_event(event["event_id"])["task_profile"])
        tasks.control(task["task_id"], "pause")
        with self.assertRaises(ValueError):
            workflow.cloud_review(event["event_id"], force_unavailable=True)
        tasks.control(task["task_id"], "resume")
        result = workflow.cloud_review(event["event_id"], force_unavailable=True)
        self.assertEqual(result["state"], "HUMAN_REVIEW")
        self.assertFalse(any(item.get("active_event_id") for item in db.get_fleet_state()))

    def test_agent_reads_only_customer_boundary_events_and_evidence(self):
        customer = workflow.create_demo_event("demo01")
        self.assertEqual(tools.read("event", customer["event_id"])["source"], "INTERVIEW_RUNTIME")
        engineering = db.get_event(customer["event_id"])
        engineering["event_id"] = "test-engineering-event"
        engineering["source"] = "TEST"
        db.save_event(engineering)
        with self.assertRaises(ValueError):
            tools.read("event", "test-engineering-event")
        with self.assertRaises(ValueError):
            tools.camera_evidence("test-engineering-event")

    def test_fresh_agent_session_queries_customer_history_through_read_tool(self):
        archived = workflow.create_demo_event("demo01")
        fresh_session = repo.new_session()["id"]
        sequence = [
            call("read_operations", {"resource": "events"}),
            ({"content": "已查询历史事件，可继续查看该事件的处置记录。"}, 8),
        ]
        with patch("robot_operations.agent.request_qwen_tool_turn", side_effect=sequence):
            snapshot = agent.send_message(fresh_session, "查询最近的历史事件", {"page": "archive"})
        self.assertEqual(snapshot["id"], fresh_session)
        self.assertTrue(any(row["role"] == "assistant" and "已查询历史事件" in row["content"] for row in snapshot["messages"]))
        audit = next(row for row in snapshot["audits"] if row.get("tool") == "read_operations")
        self.assertEqual(audit["args"].get("resource"), "events")
        self.assertIn(archived["event_id"], {item["event_id"] for item in tools.read("events")["items"]})

    def test_original_workbench_endpoint_cannot_bypass_task_lease(self):
        event = workflow.create_demo_event("demo01")
        task = tasks.create_task(self.session_id, "cleaning", event_id=event["event_id"])
        with self.assertRaises(ValueError):
            workflow.edge_review(event["event_id"])
        tasks.control(task["task_id"], "dispatch")
        with task_lease(task["task_id"]):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(workflow.edge_review, event["event_id"])
                with self.assertRaises(ValueError):
                    future.result()
            with self.assertRaises(ValueError):
                tasks.control(task["task_id"], "cancel")
        self.assertEqual(db.get_event(event["event_id"])["state"], "DETECTED")
        self.assertEqual(tasks.advance(task["task_id"])["status"], "EDGE_DETECTED")

    def test_cleaning_pause_resume_projects_same_fleet_state(self):
        event = workflow.create_demo_event("demo01")
        task = tasks.create_task(self.session_id, "cleaning", event_id=event["event_id"])
        tasks.control(task["task_id"], "dispatch")
        # This fixture isolates task-control invariants, not semantic accuracy.
        stored = db.get_event(event["event_id"])
        stored.update(state="NAVIGATING", assignment_decision={"selected_robot_id": "robot-a"})
        db.save_event(stored)
        db.update_fleet_robot("robot-a", status="navigating", active_event_id=event["event_id"], active_task_id=task["task_id"])
        with patch.object(repo, "now", return_value="2026-08-30T04:00:00+00:00"):
            tasks.control(task["task_id"], "pause")
        self.assertEqual(tasks.robot("robot-a")["status"], "paused")
        db.initialize_database()
        paused = workflow._snapshot(db.get_event(event["event_id"]))
        self.assertEqual(paused["operations_pause_started_at"], "2026-08-30T04:00:00+00:00")
        self.assertEqual(paused["operations_control"], "PAUSED")
        with self.assertRaises(ValueError):
            workflow.complete_navigation(event["event_id"])
        with patch.object(repo, "now", return_value="2026-08-30T04:00:12+00:00"):
            tasks.control(task["task_id"], "resume")
        resumed = workflow._snapshot(db.get_event(event["event_id"]))
        self.assertIsNone(resumed["operations_pause_started_at"])
        self.assertEqual(resumed["operations_paused_ms"], 12000)
        self.assertEqual(tasks.robot("robot-a")["status"], "navigating")
        self.assertEqual(tasks.get_task(task["task_id"])["status"], "NAVIGATING")

    def test_direct_action_route_enforces_session_ownership(self):
        task = self.delivery()
        with self.assertRaises(HTTPException) as error:
            action(task["task_id"], "dispatch", "foreign-session")
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(tasks.get_task(task["task_id"])["status"], "CREATED")
        self.assertEqual(action(task["task_id"], "dispatch", self.session_id)["status"], "ASSIGNED")

    def task_owned_human_fallback(self):
        """Create a durable zero-candidate event without invoking Cloud I/O."""
        event = workflow.create_demo_event("demo04")
        task = tasks.create_task(self.session_id, "cleaning", event_id=event["event_id"])
        tasks.control(task["task_id"], "dispatch")
        stored = db.get_event(event["event_id"])
        stored.update(state="HUMAN_FALLBACK", assignment_decision={
            "status": "HUMAN_FALLBACK", "candidate_count": 0, "selected_robot_id": None,
        })
        db.save_event(stored)
        return task, event

    def test_task_owned_manual_completion_requires_explicit_session_action_and_lease(self):
        task, event = self.task_owned_human_fallback()
        closed = {**db.get_event(event["event_id"]), "state": "CLOSED"}
        # The workflow function is still invoked by the task action.  Its
        # provider-dependent verifier is replaced only for this ownership test.
        with patch("demo_v1.service._verify_stored_event", return_value=closed) as verify:
            with self.assertRaises(HTTPException) as foreign:
                action(task["task_id"], "manual_complete", "foreign-session")
            self.assertEqual(foreign.exception.status_code, 409)
            with task_lease(task["task_id"]):
                # A separate request context sees the durable busy lease; the
                # current context is intentionally re-entrant for the stage
                # wrapper itself.
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(action, task["task_id"], "manual_complete", self.session_id)
                    with self.assertRaises(HTTPException) as leased:
                        future.result()
                self.assertEqual(leased.exception.status_code, 409)
            result = action(task["task_id"], "manual_complete", self.session_id)
        self.assertEqual(result["status"], "CLOSED")
        self.assertEqual(repo.get("task", task["task_id"])["status"], "CLOSED")
        verify.assert_called_once()

    def test_legacy_manual_endpoint_cannot_bypass_task_owned_event(self):
        task, event = self.task_owned_human_fallback()
        with self.assertRaises(HTTPException) as rejected:
            post_demo_v1_manual_completion(event["event_id"])
        self.assertEqual(rejected.exception.status_code, 409)
        self.assertEqual(repo.get("task", task["task_id"])["status"], "DETECTED")
        self.assertEqual(db.get_event(event["event_id"])["state"], "HUMAN_FALLBACK")

    def test_task_owned_manual_completion_rejects_pause_and_cancelled_task(self):
        task, _ = self.task_owned_human_fallback()
        # HUMAN_FALLBACK cannot be paused, and this action must not silently
        # turn into an Agent advance while the explicit human action is blocked.
        with self.assertRaises(ValueError):
            tasks.control(task["task_id"], "pause")
        tasks.control(task["task_id"], "cancel")
        with self.assertRaises(ValueError):
            tasks.complete_manual(task["task_id"])

    def test_missing_or_denied_delivery_route_policy_never_reserves(self):
        task = self.delivery()
        for policy in ({}, {"robot-d": {"elevator": False, "skybridge": False}}):
            with patch.dict("robot_operations.tasks.DELIVERY_DEPLOYMENT_POLICY", policy, clear=True):
                with self.assertRaises(ValueError):
                    tasks.control(task["task_id"], "dispatch")
        self.assertIsNone(tasks.robot("robot-d").get("active_task_id"))

    def test_complete_relocation_instruction_dispatches_without_a_second_model_turn(self):
        sequence = [call("read_operations", {"resource": "pois"}),
                    call("create_relocation_task", {"robot_id": "robot-b", "destination_poi": "a1-lobby"}, "call-2"),
                    ({"content": "已安排机器人前往待命点，系统将持续同步进度。"}, 8)]
        with patch("robot_operations.agent.request_qwen_tool_turn", side_effect=sequence):
            snapshot = agent.send_message(self.session_id, "让高仙 Omnie 去 A栋1F大堂待命", {"page": "workbench"})
        self.assertEqual(len(snapshot["tasks"]), 1)
        self.assertNotEqual(snapshot["tasks"][0]["status"], "CREATED")
        for _ in range(30):
            if tasks.get_task(snapshot["tasks"][0]["task_id"])["status"] == "CLOSED":
                break
            __import__("time").sleep(0.1)
        self.assertEqual(tasks.get_task(snapshot["tasks"][0]["task_id"])["status"], "CLOSED")
        self.assertTrue(any(row.get("task_id") == snapshot["tasks"][0]["task_id"] for row in snapshot["audits"]))
        self.assertEqual(snapshot["messages"][0]["role"], "user")
        self.assertFalse(snapshot["asr"]["available"])

    def test_agent_delivery_dispatches_and_backend_completes_without_ui_advance(self):
        sequence = [
            call("create_delivery_task", {"origin_poi": "a1-delivery", "destination_poi": "a2-corridor"}),
            call("dispatch_task", {"task_id": "TASK_ID_PLACEHOLDER"}, "call-2"),
        ]
        # The model learns the generated ID only through the first tool result;
        # model the second turn dynamically to preserve that truthful contract.
        def turns(messages, *_args, **_kwargs):
            if len([row for row in messages if row.get("role") == "tool"]) == 0:
                return sequence[0]
            task_id = json.loads([row for row in messages if row.get("role") == "tool"][-1]["content"])["result"]["task_id"]
            if len([row for row in messages if row.get("role") == "tool"]) == 1:
                return call("dispatch_task", {"task_id": task_id}, "call-2")
            return {"content": "配送任务已开始，将持续同步进度。"}, 8
        with patch("robot_operations.agent.request_qwen_tool_turn", side_effect=turns):
            snapshot = agent.send_message(self.session_id, "让普渡 FlashBot Max 从A栋1F前台把物料送到A栋2F会议室", {})
        task_id = snapshot["tasks"][0]["task_id"]
        for _ in range(30):
            if tasks.get_task(task_id)["status"] == "CLOSED":
                break
            __import__("time").sleep(0.1)
        self.assertEqual(tasks.get_task(task_id)["status"], "CLOSED")

    def test_agent_policy_acceptance_incomplete_relocation_controls_and_human_guard(self):
        # B / D: no synthetic task is created when the model asks a business
        # clarification instead of inventing missing places or a robot.
        with patch("robot_operations.agent.request_qwen_tool_turn", return_value=({"content": "请说明取件点和送达点。"}, 8)):
            incomplete = agent.send_message(self.session_id, "帮我配送", {})
        self.assertEqual(incomplete["tasks"], [])
        with patch("robot_operations.agent.request_qwen_tool_turn", return_value=({"content": "请明确指定需要待命调度的机器人。"}, 8)):
            relocation = agent.send_message(self.session_id, "去A栋1F大堂待命", {})
        self.assertEqual(relocation["tasks"], [])
        # E: durable explicit controls remain the only state changes.
        task = self.delivery(); tasks.control(task["task_id"], "dispatch")
        self.assertEqual(tasks.control(task["task_id"], "pause")["status"], "PAUSED")
        self.assertEqual(tasks.control(task["task_id"], "resume")["status"], "ASSIGNED")
        self.assertEqual(tasks.control(task["task_id"], "cancel")["status"], "CANCELLED")
        # G: no Agent tool can manufacture explicit human completion.
        task, _ = self.task_owned_human_fallback()
        with self.assertRaises(ValueError):
            tools.execute("complete_manual_task", {"task_id": task["task_id"]}, session_id=self.session_id, instruction="请自动完成人工处置")

    def test_provider_failure_is_visible_without_fake_reply_or_task(self):
        with patch("robot_operations.agent.request_qwen_tool_turn", side_effect=RuntimeError("provider down")):
            result = agent.send_message(self.session_id, "配送", {})
        self.assertEqual(result["error"]["code"], "AGENT_UNAVAILABLE")
        self.assertEqual([row["role"] for row in result["messages"]], ["user"])
        self.assertEqual(result["tasks"], [])

    def test_illegal_model_call_rejected_and_audited(self):
        with patch("robot_operations.agent.request_qwen_tool_turn", side_effect=[call("change_threshold", {"confidence": .01}), ({"content": "此操作不允许。"}, 5)]):
            result = agent.send_message(self.session_id, "把阈值改成0.01", {})
        audit = next(row for row in result["audits"] if row.get("tool") == "change_threshold")
        self.assertEqual(audit["policy"], "REJECT")
        self.assertEqual(result["tasks"], [])

    def test_advice_is_explicit_cached_read_only_and_validates_references(self):
        self.assertIsNone(repo.advice_snapshot()["snapshot"])
        items = [{"finding": "当前样本不足", "evidence": "统计窗口内无已闭环事件", "recommendation": "补充真实事件后再评估", "related_events": []} for _ in range(3)]
        sequence = [call("read_operations", {"resource": "analytics"}), ({"content": json.dumps({"items": items})}, 8)]
        with patch("robot_operations.agent.request_qwen_tool_turn", side_effect=sequence) as model:
            result = agent.regenerate_advice()
            cached = repo.advice_snapshot()
            self.assertEqual(model.call_count, 2)
        self.assertEqual(result, cached)
        self.assertEqual(result["snapshot"]["tool_calls"], 1)
        self.assertFalse(repo.tasks())
        items[0]["related_events"] = ["invented-event"]
        with patch("robot_operations.agent.request_qwen_tool_turn", side_effect=[call("read_operations", {"resource": "analytics"}), ({"content": json.dumps({"items": items})}, 8)]):
            with self.assertRaises(ValueError):
                agent.regenerate_advice()
        self.assertEqual(repo.advice_snapshot(), cached)

    def test_restart_marks_request_interrupted_without_retry_or_reset(self):
        session = repo.get("session", self.session_id)
        session["busy"] = True
        repo.save("session", session)
        task = self.delivery()
        tasks.control(task["task_id"], "dispatch")
        fleet = db.get_fleet_state()
        with patch("robot_operations.agent.request_qwen_tool_turn") as model:
            repo.initialize()
            repo.recover_interrupted_requests()
            model.assert_not_called()
        self.assertFalse(repo.get("session", self.session_id)["busy"])
        self.assertEqual(repo.get("session", self.session_id)["error"]["code"], "AGENT_INTERRUPTED")
        self.assertEqual(db.get_fleet_state(), fleet)

    def test_external_adapters_never_claim_connected(self):
        for adapter in DELIVERY_ADAPTERS.values():
            self.assertFalse(adapter.status()["connected"])
            self.assertEqual(adapter.status()["authorization"], "AUTH REQUIRED")
            with self.assertRaises(ValueError):
                adapter.submit({"order_id": "fake"})
