"""Acceptance integrity: no shortcuts or small-sample false PASS."""
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from types import SimpleNamespace

from acceptance import unified
from database import connection as db
from robot_operations import repository, tasks
from tests import test_p1a_closure as closure


class AcceptanceHarnessTests(TestCase):
    def setUp(self):
        self.harness = closure.ClosureTests()
        self.harness.setUp()
        repository.initialize()

    def tearDown(self):
        self.harness.tearDown()

    def test_fixed_profiles(self):
        for demo in ("demo01", "demo02", "demo03"):
            self.assertEqual(unified.profile(demo, "LIVE"), (5, 4))
            self.assertEqual(unified.profile(demo, "STABLE_REPLAY"), (3, 3))
        self.assertEqual(unified.profile("demo04", "LIVE"), (3, 3))

    def test_consecutive_runtime_preserves_terminal_fleet_without_reset(self):
        with patch.object(db, "reset_fleet_state", side_effect=AssertionError("No per-run reset")):
            first = unified.run_once("demo01", "LIVE")
            battery = tasks.robot("robot-a")["battery"]
            second = unified.run_once("demo01", "LIVE")
        self.assertFalse(unified.acceptance_failures("demo01", first))
        self.assertFalse(unified.acceptance_failures("demo01", second))
        self.assertEqual(tasks.robot("robot-a")["battery"], battery - 2)

    def test_human_completion_uses_actual_manual_transition_not_invented_state(self):
        self.harness.cloud.return_value = closure._review("large_object")
        result = unified.run_once("demo04", "LIVE")
        self.assertEqual(unified.acceptance_failures("demo04", result), [])
        result["transitions"] = [row for row in result["transitions"] if row["state"] != "VERIFYING"]
        self.assertIn("no_human_workflow", unified.acceptance_failures("demo04", result))

    def test_return_setup_is_real_task_not_coordinate_reset(self):
        # First use the existing public Task Runtime to put SC50 on A2F.
        session = repository.new_session()
        task = tasks.create_task(session["id"], "relocation", robot_id="robot-c", destination_poi="a2-corridor")
        tasks.control(task["task_id"], "dispatch")
        while tasks.get_task(task["task_id"])["status"] != "CLOSED":
            tasks.advance(task["task_id"])
        battery = tasks.robot("robot-c")["battery"]
        with patch.object(db, "reset_fleet_state", side_effect=AssertionError("No reset")):
            setup = unified.prepare_cross_building_trial("demo03")
        self.assertEqual(setup["status"], "CLOSED")
        self.assertEqual(tasks.robot("robot-c")["map_id"], "B_1F")
        self.assertEqual(tasks.robot("robot-c")["battery"], battery - 1)
        self.assertIn("SKYBRIDGE_A", setup["route"]["to_origin"]["node_path"])

    def test_replay_requires_complete_passing_selected_batch(self):
        with db.database_session() as connection:
            connection.execute("CREATE TABLE acceptance_runs (id INTEGER PRIMARY KEY,batch_id TEXT,payload TEXT)")
        with self.assertRaises(ValueError):
            unified.source_events("missing", "demo01")
        for index in range(5):
            row = {"profile": "P1G", "mode": "LIVE", "demo": "demo01", "event_id": str(index), "failures": []}
            with db.database_session() as connection:
                connection.execute("INSERT INTO acceptance_runs(batch_id,payload) VALUES(?,?)", ("batch", json.dumps(row)))
        self.assertEqual(len(unified.source_events("batch", "demo01")), 5)
        with self.assertRaises(ValueError):
            unified.source_events("batch", "demo02")

    def test_all_exceptions_are_persisted_without_retry_or_short_pass(self):
        output = StringIO()
        path = db.DATABASE_PATH.parent / "exception-acceptance.sqlite"
        argv = ["acceptance", "--db", str(path), "--demo", "demo01", "--mode", "LIVE", "--allow-paid-live"]
        with patch("sys.argv", argv), patch.object(unified, "get_runtime", return_value=SimpleNamespace(qwen_ready=True)), patch.object(unified, "run_once", side_effect=ValueError("token=private")) as run, redirect_stdout(output), self.assertRaises(SystemExit) as exited:
            unified.main()
        self.assertEqual(exited.exception.code, 1)
        self.assertEqual(run.call_count, 5)
        with db.database_session() as connection:
            rows = connection.execute("SELECT payload FROM acceptance_runs").fetchall()
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(json.loads(row["payload"])["failures"] for row in rows))
        self.assertNotIn("private", output.getvalue())
        self.assertEqual(json.loads(output.getvalue().splitlines()[-1])["status"], "BLOCK")
