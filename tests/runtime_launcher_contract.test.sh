#!/bin/bash
# Isolated contract tests: no production ports, PID files, or processes.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/runtime_launcher_lib.sh
source "$PROJECT_DIR/scripts/runtime_launcher_lib.sh"

TMP_DIR="$(mktemp -d)"
SERVER_PIDS=()
cleanup() {
  for pid in "${SERVER_PIDS[@]:-}"; do
    kill -TERM "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  done
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }
full_health='{"status":"ok","release_contract":"cleanops.interview.v1","capabilities":["stage_runtime","event_archive","analytics","robot_operations","advanced_observability","spatial_v2"]}'

# A: an old contract must not be accepted by a substring or legacy check.
if printf '%s' '{"api_contract":"operations.v1"}' | runtime_health_contract_ok "$RUNTIME_RELEASE_CONTRACT"; then fail "old operations.v1 was accepted"; fi
pass "A old operations.v1 rejected"

# B: contract equality alone is insufficient without every required capability.
if printf '%s' '{"release_contract":"cleanops.interview.v1","capabilities":["stage_runtime","event_archive"]}' | runtime_health_contract_ok "$RUNTIME_RELEASE_CONTRACT"; then fail "incomplete capability set was accepted"; fi
pass "B incomplete capabilities rejected"

# C: exact contract plus full capability set is reusable.
printf '%s' "$full_health" | runtime_health_contract_ok "$RUNTIME_RELEASE_CONTRACT" || fail "full contract rejected"
pass "C full contract accepted"

# D/E: a listener with a fabricated launcher record must not be signaled when
# command identity does not match. These servers are test-owned and cleaned up.
for pair in "18100:backend:uvicorn" "18101:frontend:vite"; do
  IFS=: read -r port service token <<< "$pair"
  (cd "$PROJECT_DIR" && python3 -m http.server "$port" --bind 127.0.0.1 >/dev/null 2>&1) &
  pid=$!; SERVER_PIDS+=("$pid")
  for _ in {1..20}; do runtime_port_in_use "$port" && break; sleep 0.1; done
  record="$TMP_DIR/$service.pid"
  listener="$(runtime_listener_pid "$port")"
  printf '%s|%s|%s|%s|%s|%s\n' "$service" "$port" "$listener" "$(runtime_process_started_at "$listener")" "$PROJECT_DIR" "fabricated-signature" > "$record"
  if runtime_terminate_owned "$service" "$port" "$record" "$PROJECT_DIR" "$token"; then fail "unknown $service listener was terminated"; fi
  kill -0 "$pid" 2>/dev/null || fail "unknown $service listener was killed"
  pass "${service} unknown listener was not killed"
done

# A stale/missing record must not prevent stop from reporting every unknown
# listener, and must never signal either one.
stop_output="$TMP_DIR/stop-output.txt"
DEMO_LOG_DIR="$TMP_DIR/no-records" DEMO_BACKEND_PORT=18100 DEMO_FRONTEND_PORT=18101 "$PROJECT_DIR/stop_demo.command" >"$stop_output" 2>&1 || fail "stop exited non-zero with no PID records"
grep -q 'port 18100 PID' "$stop_output" || fail "stop did not report unknown backend listener"
grep -q 'port 18101 PID' "$stop_output" || fail "stop did not report unknown frontend listener"
pass "stop reports unknown listeners without PID records"

runtime_command_is_expected backend 18102 "/tmp/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 18102" || fail "strict backend argv rejected"
runtime_command_is_expected backend 18102 "/Library/Frameworks/Python.framework/Versions/3.14/Resources/Python.app/Contents/MacOS/Python ../backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 18102" || fail "macOS Python wrapper argv rejected"
runtime_command_is_expected frontend 18103 "/tmp/frontend/node_modules/.bin/vite --host 127.0.0.1 --port 18103 --strictPort" || fail "strict frontend argv rejected"
runtime_command_is_expected frontend 18103 "node ./node_modules/.bin/vite --host 127.0.0.1 --port 18103 --strictPort" || fail "real relative Vite argv rejected"
if runtime_command_is_expected backend 18102 "uvicorn main:app --port 18102"; then fail "loose backend argv accepted"; fi
if runtime_command_is_expected frontend 18103 "vite --port 18103"; then fail "loose frontend argv accepted"; fi
if runtime_command_is_expected backend 18102 "/usr/bin/python harmless /backend/.venv/bin/uvicorn marker uvicorn main:app --host 127.0.0.1 --port 18102"; then fail "backend marker argv accepted"; fi
if runtime_command_is_expected frontend 18103 "/usr/bin/python harmless /frontend/node_modules/.bin/vite marker vite --host 127.0.0.1 --port 18103 --strictPort"; then fail "frontend marker argv accepted"; fi
pass "strict expected argv is enforced"

# A manually started real Vite can have the exact project cwd/argv but lacks a
# launcher record. start_demo must report it, never SIGTERM it.
(cd "$PROJECT_DIR/frontend" && ./node_modules/.bin/vite --host 127.0.0.1 --port 18104 --strictPort >/dev/null 2>&1) &
vite_pid=$!; SERVER_PIDS+=("$vite_pid")
for _ in {1..30}; do runtime_port_in_use 18104 && break; sleep 0.1; done
vite_command="$(runtime_process_command "$(runtime_listener_pid 18104)")"
runtime_command_is_expected frontend 18104 "$vite_command" || fail "actual Vite argv was not recognized"
set +e
DEMO_LOG_DIR="$TMP_DIR/no-record-vite" DEMO_BACKEND_PORT=18105 DEMO_FRONTEND_PORT=18104 DEMO_NO_OPEN=1 "$PROJECT_DIR/start_demo.command" >"$TMP_DIR/start-unknown-vite.txt" 2>&1
start_status=$?
set -e
[[ "$start_status" -ne 0 ]] || fail "start accepted unowned Vite"
kill -0 "$vite_pid" 2>/dev/null || fail "start killed unowned Vite"
grep -q 'refusing reuse or termination' "$TMP_DIR/start-unknown-vite.txt" || fail "start did not explain unowned Vite"
pass "matching unowned Vite is reported and not killed"

start_mock_backend() {
  local port="$1" include_openapi="$2"
  python3 - "$port" "$include_openapi" <<'PY' >/dev/null 2>&1 &
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

port, include_openapi = int(sys.argv[1]), sys.argv[2] == "yes"
health = {"status":"ok", "release_contract":"cleanops.interview.v1", "capabilities":["stage_runtime","event_archive","analytics","robot_operations","advanced_observability","spatial_v2"]}
paths = {"/api/event-archive":{"get":{}}, "/api/robot-operations/sessions":{"post":{}}, "/api/spatial/overview":{"get":{}}} if include_openapi else {}
class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
    body = health if self.path == "/api/health" else [{"id":"robot-a"},{"id":"robot-b"},{"id":"robot-c"},{"id":"robot-d"}] if self.path == "/api/robots" else {"paths":paths} if self.path == "/openapi.json" else {}
    self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(json.dumps(body).encode())
  def log_message(self, *_): pass
ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
PY
  SERVER_PIDS+=("$!")
}

# F: an isolated cold service that exposes all required readonly routes passes.
start_mock_backend 18102 yes
for _ in {1..20}; do runtime_port_in_use 18102 && break; sleep 0.1; done
runtime_preflight_backend 18102 >/dev/null || fail "complete cold preflight failed"
pass "F complete cold preflight passed"

# Health can be correct while OpenAPI is incomplete; the launcher must reject it.
start_mock_backend 18103 no
for _ in {1..20}; do runtime_port_in_use 18103 && break; sleep 0.1; done
if runtime_preflight_backend 18103 >/dev/null; then fail "missing OpenAPI routes were accepted"; fi
pass "health-only service with missing routes rejected"

grep -q -- '--port "$FRONTEND_PORT" --strictPort' "$PROJECT_DIR/start_demo.command" || fail "frontend is not locked to the requested official port"
pass "official frontend remains strict-port"
