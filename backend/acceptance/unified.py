"""P1-G consecutive acceptance using real stages and an isolated SQLite file.

LIVE is paid and requires --allow-paid-live. Replay blocks the shared transport
as an assertion, not as a substitute provider. Results/failures are append-only
acceptance_runs rows beside the real events/model records. Nothing is retried
or selected away to inflate success rates.
"""
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from unittest.mock import patch
from uuid import uuid4

from database import connection as db
from demo_v1 import service
from observability.errors import classify
from observability.service import trace_view
from perception import qwen
from perception.config import get_runtime
from robot_operations import repository, tasks


def acceptance_failures(demo, result):
    """Scenario-specific assertions live in the test harness, never Runtime."""
    failures = []
    def require(condition, label):
        if not condition:
            failures.append(label)
    assignment = result.get("assignment_decision") or {}
    verification = result.get("verification") or {}
    route = result.get("navigation_plan") or {}
    states = {row["state"] for row in result.get("transitions", [])}
    require(result.get("state") == "CLOSED", "not_closed")
    review = result.get("qwen_review") or {}
    require(review.get("need_action", review.get("need_clean")) is True, "cloud_did_not_require_action")
    require(review.get("event_type") == {"demo01": "small_litter", "demo02": "liquid", "demo03": "can", "demo04": "large_object"}[demo], "wrong_semantic_event_type")
    require(verification.get("verification_pass") is True, "verification_not_passed")
    require("LOCATED" in states, "no_spatial_stage")
    require((result.get("spatial_location") or {}).get("mapping_method") == "four_point_homography", "no_shared_homography")
    if demo == "demo04":
        require(assignment.get("candidate_count") == 0, "not_zero_candidate")
        require(assignment.get("selected_robot_id") is None, "human_has_robot_assignment")
        require("HUMAN_FALLBACK" in states and any(row["state"] == "VERIFYING" and row.get("detail", {}).get("manual_completion") is True for row in result.get("transitions", [])), "no_human_workflow")
        require((result.get("human_work_order") or {}).get("status") == "COMPLETED", "human_not_completed")
        require(not route, "human_has_fake_route")
    else:
        require(assignment.get("selected_robot_id") == {"demo01": "robot-a", "demo02": "robot-b", "demo03": "robot-c"}[demo], "wrong_robot")
        require(route.get("source") == "dijkstra_global_topology_planner", "no_actual_dijkstra")
    if demo == "demo02":
        first = result.get("first_qwen_review") or {}
        multi = result.get("multi_view") or {}
        audit = multi.get("audit") or []
        require(first.get("evidence_sufficient") is False, "single_view_did_not_require_evidence")
        for name in ("find_supporting_cameras", "fetch_camera_evidence"):
            require(any(row.get("name") == name and row.get("source") == "MODEL_TOOL_CALL" and row.get("status") == "OK" for row in audit), "no_model_" + name)
        require(1 <= len(multi.get("selected_cameras") or []) <= 2, "camera_budget_or_no_camera")
        require(1 <= (multi.get("iteration_count") or 0) <= 2, "round_budget_or_no_round")
    if demo == "demo03":
        path = route.get("node_path") or []
        require(path and path[0] == "B_1F" and path[-1] == "A_2F", "wrong_cross_building_endpoints")
        require(any("ELEVATOR" in node for node in path) and any("SKYBRIDGE" in node for node in path), "missing_elevator_or_skybridge")
        require(bool(verification.get("roi")), "missing_target_roi")
    return failures


def run_once(demo, mode, progress=None):
    result = service.create_demo_event(demo, mode)
    if progress is not None:
        progress["event_id"] = result["event_id"]
    event_id = result["event_id"]
    for expected, stage in (("DETECTED", service.edge_review), ("EDGE_DETECTED", service.cloud_review),
                            ("CLOUD_REVIEW", service.locate_event), ("LOCATED", service.assign_event),
                            ("ASSIGNED", service.start_navigation), ("NAVIGATING", service.complete_navigation),
                            ("ARRIVED", service.complete_cleaning), ("CLEANING_COMPLETED", service.verify_event)):
        if result["state"] != expected:
            break
        result = stage(event_id)
    if result["state"] == "HUMAN_FALLBACK":
        result = service.complete_demo04_manual(result["event_id"])
    return result


def profile(demo, mode):
    return (3, 3) if mode == "STABLE_REPLAY" or demo == "demo04" else (5, 4)


def prepare_cross_building_trial(demo):
    """Recorded PoC return task, never a coordinate write or baseline reset."""
    if demo != "demo03" or tasks.robot("robot-c")["map_id"] == "B_1F":
        return None
    session = repository.new_session()
    task = tasks.create_task(session["id"], "relocation", robot_id="robot-c", destination_poi="b1-lobby")
    tasks.control(task["task_id"], "dispatch")
    for _ in range(4):
        task = tasks.advance(task["task_id"])
        if task["status"] == "CLOSED":
            return {"task_id": task["task_id"], "status": task["status"], "route": task.get("route"), "source": "EXPLICIT_ACCEPTANCE_RELOCATION_TASK"}
    raise ValueError("Acceptance relocation did not complete")


def source_events(batch_id, demo):
    with db.database_session() as connection:
        rows = [json.loads(row["payload"]) for row in connection.execute("SELECT payload FROM acceptance_runs WHERE batch_id=? ORDER BY id", (batch_id,))]
    count, required = profile(demo, "LIVE")
    if len(rows) != count or any(row.get("profile") != "P1G" or row.get("mode") != "LIVE" or row.get("demo") != demo for row in rows) or sum(not row["failures"] for row in rows) < required:
        raise ValueError("Replay requires a complete passing P1G LIVE batch for this demo")
    return {row["event_id"] for row in rows if not row["failures"]}


def implementation_fingerprint():
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root, text=True).splitlines()
    digest = sha256()
    for name in sorted(set(names)):
        path = root / name
        if path.suffix in {".py", ".ts", ".tsx", ".json"} and path.is_file():
            digest.update(name.encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def summary(demo, mode, result):
    first, final = result.get("first_qwen_review") or {}, result.get("qwen_review") or {}
    multi = result.get("multi_view") or {}
    verification = result.get("verification") or {}
    trace = trace_view(result["event_id"])
    return {"demo": demo, "mode": mode, "event_id": result["event_id"], "trace_id": trace["trace_id"],
            "state": result["state"], "failures": acceptance_failures(demo, result),
            "first_confidence": first.get("decision_confidence"), "first_sufficient": first.get("evidence_sufficient"),
            "final_confidence": final.get("decision_confidence"), "event_type": final.get("event_type"), "need_action": final.get("need_action", final.get("need_clean")),
            "second_confidence": (result.get("second_qwen_review") or {}).get("decision_confidence"),
            "fusion": (result.get("evidence_fusion") or {}).get("score"), "selected_cameras": multi.get("selected_cameras"),
            "rounds": multi.get("iteration_count"), "tools": [{key: row.get(key) for key in ("name", "status", "source", "tool_duration_ms")} for row in multi.get("audit") or []],
            "robot": (result.get("assignment_decision") or {}).get("selected_robot_id"), "candidate_count": (result.get("assignment_decision") or {}).get("candidate_count"),
            "route": (result.get("navigation_plan") or {}).get("node_path"), "verification_pass": verification.get("verification_pass"),
            "verification_confidence": verification.get("confidence"), "verification_next_action": verification.get("next_action"), "roi": verification.get("roi"),
            "error": classify(result.get("error")), "model_requests": [{"request_id": node["id"], "duration_ms": node["duration_ms"], "status": node["status"]} for node in trace["nodes"] if node["group"] == "RUNTIME"],
            "stages": [call["name"] for call in trace["tool_calls"] if call["trigger_source"] != "MODEL_TOOL_CALL"],
            "response_source": final.get("source"), "verification_source": verification.get("source"),
            "replay_event_id": final.get("replay_event_id"), "verification_replay_event_id": verification.get("replay_event_id")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path, help="Dedicated acceptance SQLite file (not application database)")
    parser.add_argument("--demo", choices=tuple(service.SCENARIO_IDS), required=True)
    parser.add_argument("--mode", choices=("LIVE", "STABLE_REPLAY"), required=True)
    parser.add_argument("--profile", choices=("P1G", "DIAGNOSTIC"), default="P1G")
    parser.add_argument("--source-live-batch-id")
    parser.add_argument("--allow-paid-live", action="store_true")
    args = parser.parse_args()
    count, required = profile(args.demo, args.mode) if args.profile == "P1G" else (1, 1)
    if args.db.resolve() == Path(db.DATABASE_PATH).resolve():
        parser.error("Use a dedicated acceptance database")
    if args.mode == "LIVE" and (not args.allow_paid_live or not get_runtime().qwen_ready):
        parser.error("LIVE requires explicit paid opt-in and configured Qwen")
    db.DATABASE_PATH = args.db
    db.initialize_database()
    repository.initialize()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    code_fingerprint = implementation_fingerprint()
    batch_id = "acceptance-" + uuid4().hex
    with db.database_session() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS acceptance_runs (id INTEGER PRIMARY KEY, batch_id TEXT, payload TEXT NOT NULL)")
    allowed_sources = set()
    if args.mode == "STABLE_REPLAY":
        if not args.source_live_batch_id:
            parser.error("Replay requires --source-live-batch-id")
        try:
            allowed_sources = source_events(args.source_live_batch_id, args.demo)
        except ValueError as error:
            parser.error(str(error))
    successes = 0
    for iteration in range(1, count + 1):
        print(json.dumps({"batch_id": batch_id, "iteration": iteration, "demo": args.demo, "mode": args.mode, "status": "STARTED"}), flush=True)
        guard = patch.object(qwen, "_request_qwen", side_effect=AssertionError("Replay attempted Cloud transport")) if args.mode == "STABLE_REPLAY" else nullcontext()
        progress = {}
        report = {"batch_id": batch_id, "iteration": iteration, "revision": revision, "code_fingerprint": code_fingerprint, "profile": args.profile,
                  "demo": args.demo, "mode": args.mode, "started_at": datetime.now(timezone.utc).isoformat(),
                  "baseline": "PERSISTED_FLEET_NO_RESET", "source_live_batch_id": args.source_live_batch_id}
        try:
            report["setup_task"] = prepare_cross_building_trial(args.demo)
            report["fleet_before"] = db.get_fleet_state()
            with guard:
                result = run_once(args.demo, args.mode, progress)
            report.update(summary(args.demo, args.mode, result))
            if args.mode == "STABLE_REPLAY":
                if report["replay_event_id"] not in allowed_sources or report["verification_replay_event_id"] not in allowed_sources:
                    report["failures"].append("replay_not_from_selected_live_batch")
                if report["model_requests"]:
                    report["failures"].append("replay_has_new_cloud_request")
        except Exception as error:
            report.update(event_id=progress.get("event_id"), state="ACCEPTANCE_ERROR", failures=["exception_" + type(error).__name__], error=classify({"type": "TOOL_ERROR"}))
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        report["fleet_after"] = db.get_fleet_state()
        successes += not report["failures"]
        with db.database_session() as connection:
            connection.execute("INSERT INTO acceptance_runs(batch_id,payload) VALUES(?,?)", (batch_id, json.dumps(report)))
        print(json.dumps({key: value for key, value in report.items() if key not in {"fleet_before", "fleet_after"}}, ensure_ascii=False), flush=True)
    print(json.dumps({"batch_id": batch_id, "profile": args.profile, "passed": successes, "total": count, "required": required,
                      "status": "DIAGNOSTIC_ONLY" if args.profile == "DIAGNOSTIC" else "PASS" if successes >= required else "BLOCK"}), flush=True)
    raise SystemExit(0 if successes >= required else 1)


if __name__ == "__main__":
    main()
