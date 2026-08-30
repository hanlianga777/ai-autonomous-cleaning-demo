"""Process-boundary persistence checks for the shared PoC fleet state.

Each assertion crosses a fresh Python interpreter boundary.  The children use
only mocked provider-stage functions: they neither load project ``.env`` files
nor make a network request.  SQLite remains the sole persistence mechanism
under test.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]


REVIEW = {
    "provider": "test-provider",
    "model": "test-model",
    "image_count": 1,
    "elapsed_ms": 1,
    "need_clean": True, "evidence_sufficient": True, "ambiguity_type": "none",
    "event_type": "can",
    "decision_confidence": 0.93,
    "severity": "medium",
    "surface_type": "tile",
    "interference_factors": [],
    "evidence_summary": "test structured review",
    "recommended_capabilities": [],
    "next_action": "dispatch_robot",
    "raw": {},
}

VERIFICATION = {
    "provider": "test-provider",
    "verification_pass": True,
    "issue_remaining": False,
    "confidence": 0.95,
    "evidence_summary": "test verification pass",
    "next_action": "close",
    "elapsed_ms": 1,
    "raw": {},
}


def _child_environment() -> dict[str, str]:
    """Use a minimal child environment so test processes never consume keys."""
    return {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(BACKEND_ROOT),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }


class FleetRestartPersistenceTests(unittest.TestCase):
    def _run_child(self, database_path: Path, program: str, *args: str) -> dict:
        completed = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(program), str(database_path), *args],
            cwd=BACKEND_ROOT,
            env=_child_environment(),
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"child process failed:\nstdout={completed.stdout}\nstderr={completed.stderr}",
        )
        return json.loads(completed.stdout)

    def _create_arrived_event(self, database_path: Path) -> dict:
        return self._run_child(
            database_path,
            """
            import json
            import sys
            from pathlib import Path
            from types import SimpleNamespace
            from unittest.mock import patch

            from database import connection
            connection.DATABASE_PATH = Path(sys.argv[1])
            connection.initialize_database()
            from database.connection import get_fleet_state
            from demo_v1.service import (
                assign_event, cloud_review, complete_navigation, create_demo_event,
                edge_review, locate_event, start_navigation,
            )

            review = %s
            with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-model")), patch("demo_v1.service.run_event_qwen_vl", return_value=review):
                event_id = create_demo_event("demo03")["event_id"]
                edge_review(event_id)
                cloud_review(event_id)
                locate_event(event_id)
                assign_event(event_id)
                start_navigation(event_id)
                complete_navigation(event_id)

            robot = next(item for item in get_fleet_state() if item["id"] == "robot-c")
            assert robot["status"] == "arrived"
            assert robot["active_event_id"] == event_id
            print(json.dumps({"event_id": event_id, "robot": robot}, ensure_ascii=False))
            """ % repr(REVIEW),
        )

    def test_fleet_location_and_active_assignment_survive_real_restart(self) -> None:
        """A fresh interpreter must retain mutable fleet facts from SQLite."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "fleet-restart.db"
            started = self._create_arrived_event(database_path)
            restored = self._run_child(
                database_path,
                """
                import json
                import sys
                from pathlib import Path
                from database import connection
                connection.DATABASE_PATH = Path(sys.argv[1])
                connection.initialize_database()
                from database.connection import get_fleet_state, get_event

                event_id = sys.argv[2]
                event = get_event(event_id)
                robot = next(item for item in get_fleet_state() if item["id"] == "robot-c")
                assert event is not None and event["state"] == "ARRIVED"
                assert robot["status"] == "arrived"
                assert robot["active_event_id"] == event_id
                print(json.dumps({"robot": robot, "event_state": event["state"]}, ensure_ascii=False))
                """,
                started["event_id"],
            )
            self.assertEqual(restored["event_state"], "ARRIVED")
            for field in ("map_id", "coordinates", "battery", "status", "active_event_id"):
                self.assertEqual(restored["robot"][field], started["robot"][field])

    def test_closed_event_snapshot_survives_restart_and_reset_preserves_history(self) -> None:
        """Reset returns only the mutable fleet to baseline, never historic snapshots."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "fleet-terminal.db"
            started = self._create_arrived_event(database_path)
            closed = self._run_child(
                database_path,
                """
                import json
                import sys
                from pathlib import Path
                from types import SimpleNamespace
                from unittest.mock import patch

                from database import connection
                connection.DATABASE_PATH = Path(sys.argv[1])
                connection.initialize_database()
                from database.connection import get_event, get_fleet_state
                from demo_v1.service import complete_cleaning, verify_event

                verification = %s
                event_id = sys.argv[2]
                with patch("demo_v1.service.get_runtime", return_value=SimpleNamespace(qwen_ready=True, qwen_model="test-model")), patch("demo_v1.service.run_verification_qwen_vl", return_value=verification):
                    result = complete_cleaning(event_id)
                    assert result["state"] == "CLEANING_COMPLETED"
                    result = verify_event(event_id)

                event = get_event(event_id)
                robot = next(item for item in get_fleet_state() if item["id"] == "robot-c")
                assert result["state"] == "CLOSED"
                assert event is not None and event["state"] == "CLOSED"
                assert robot["status"] == "idle" and robot["active_event_id"] is None
                assert event["demo_v1"]["fleet_snapshot"] == get_fleet_state()
                print(json.dumps({"event_id": event_id, "event": event, "robot": robot}, ensure_ascii=False))
                """ % repr(VERIFICATION),
                started["event_id"],
            )
            restarted = self._run_child(
                database_path,
                """
                import json
                import sys
                from pathlib import Path
                from database import connection
                connection.DATABASE_PATH = Path(sys.argv[1])
                connection.initialize_database()
                from database.connection import get_event, get_fleet_state

                event_id = sys.argv[2]
                event = get_event(event_id)
                robot = next(item for item in get_fleet_state() if item["id"] == "robot-c")
                assert event is not None and event["state"] == "CLOSED"
                assert event["demo_v1"]["fleet_snapshot"] == get_fleet_state()
                assert robot["status"] == "idle" and robot["active_event_id"] is None
                print(json.dumps({"event": event, "robot": robot}, ensure_ascii=False))
                """,
                closed["event_id"],
            )
            self.assertEqual(restarted["robot"], closed["robot"])
            self.assertEqual(restarted["event"]["demo_v1"]["fleet_snapshot"], closed["event"]["demo_v1"]["fleet_snapshot"])

            reset = self._run_child(
                database_path,
                """
                import json
                import sys
                from pathlib import Path
                from database import connection
                connection.DATABASE_PATH = Path(sys.argv[1])
                connection.initialize_database()
                from database.connection import get_event, get_fleet_state, reset_fleet_state

                event_id = sys.argv[2]
                event_before = get_event(event_id)
                baseline = reset_fleet_state()
                event_after = get_event(event_id)
                current = get_fleet_state()
                robot = next(item for item in current if item["id"] == "robot-c")
                assert baseline == current
                assert event_before == event_after
                assert event_after is not None and event_after["state"] == "CLOSED"
                assert robot["status"] == "idle"
                assert robot.get("active_event_id") is None
                assert robot["map_id"] == "B_1F"
                assert robot["coordinates"] == {"x": 24, "y": 26}
                print(json.dumps({"fleet": current, "event": event_after}, ensure_ascii=False))
                """,
                closed["event_id"],
            )
            self.assertEqual(reset["event"], restarted["event"])
            reset_robot = next(item for item in reset["fleet"] if item["id"] == "robot-c")
            self.assertEqual(reset_robot["map_id"], "B_1F")


if __name__ == "__main__":
    unittest.main()
