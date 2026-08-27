#!/bin/bash
# Double-click on macOS to launch the customer demo. It validates the backend
# API contract before reusing a listener, so a stale local server cannot leave
# the current frontend with an empty workbench.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/.demo-logs"
PID_FILE="$PROJECT_DIR/.demo-pids"
BACKEND_PID_FILE="$LOG_DIR/backend.pid"
EXPECTED_API_CONTRACT="operations.v1"

mkdir -p "$LOG_DIR"

port_in_use() {
  lsof -tiTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

backend_contract_ok() {
  local health
  health="$(curl --max-time 2 --silent --fail http://127.0.0.1:8000/api/health 2>/dev/null || true)"
  [[ "$health" == *"\"api_contract\":\"$EXPECTED_API_CONTRACT\""* ]]
}

listener_pid() {
  lsof -tiTCP:"$1" -sTCP:LISTEN | head -n 1
}

stop_owned_backend_if_stale() {
  local listening_pid recorded_pid
  listening_pid="$(listener_pid 8000)"
  recorded_pid="$(cat "$BACKEND_PID_FILE" 2>/dev/null || true)"
  if [[ -n "$listening_pid" && "$listening_pid" == "$recorded_pid" ]]; then
    echo "[backend]  detected stale launcher-owned API; restarting it"
    kill "$listening_pid" 2>/dev/null || true
    for _ in {1..20}; do
      if ! port_in_use 8000; then
        return 0
      fi
      sleep 0.2
    done
  fi
  if port_in_use 8000; then
    echo "[backend]  port 8000 is occupied by an incompatible service (PID $(listener_pid 8000))."
    echo "           Stop that service or use stop_demo.command, then restart this demo."
    exit 1
  fi
}

start_backend() {
  if port_in_use 8000; then
    if backend_contract_ok; then
      echo "[backend]  http://localhost:8000  (compatible service already running)"
      return
    fi
    stop_owned_backend_if_stale
  fi
  if [[ ! -x "$BACKEND_DIR/.venv/bin/python" ]]; then
    echo "[backend]  creating Python virtual environment…"
    python3 -m venv "$BACKEND_DIR/.venv"
    "$BACKEND_DIR/.venv/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
  fi
  if ! "$BACKEND_DIR/.venv/bin/python" -c "import multipart, langgraph" >/dev/null 2>&1; then
    echo "[backend]  installing required API upload support…"
    "$BACKEND_DIR/.venv/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
  fi
  (
    cd "$BACKEND_DIR"
    nohup "$BACKEND_DIR/.venv/bin/uvicorn" main:app --host 127.0.0.1 --port 8000 >"$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
  )
  echo "[backend]  http://localhost:8000  (started)"
}

start_frontend() {
  if port_in_use 5173; then
    echo "[frontend] http://localhost:5173  (already running)"
    return
  fi
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    echo "[frontend] installing npm packages…"
    (cd "$FRONTEND_DIR" && npm install --cache .npm-cache)
  fi
  (
    cd "$FRONTEND_DIR"
    nohup "$FRONTEND_DIR/node_modules/.bin/vite" --host 127.0.0.1 >"$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
  )
  echo "[frontend] http://localhost:5173  (started)"
}

start_backend
start_frontend

for _ in {1..20}; do
  if backend_contract_ok && curl --max-time 2 --silent --fail http://127.0.0.1:8000/api/workbench/scenarios >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done
if ! backend_contract_ok; then
  echo "[backend]  failed compatibility smoke test. See $LOG_DIR/backend.log"
  exit 1
fi

{
  [[ -f "$LOG_DIR/backend.pid" ]] && cat "$LOG_DIR/backend.pid"
  [[ -f "$LOG_DIR/frontend.pid" ]] && cat "$LOG_DIR/frontend.pid"
} > "$PID_FILE" || true

sleep 1
echo
echo "CleanOps customer demo is ready. API: http://localhost:8000/docs"
AI_STATUS="$(curl --max-time 2 --silent --fail http://127.0.0.1:8000/api/system/ai-status 2>/dev/null || true)"
if [[ -n "$AI_STATUS" ]]; then
  echo "AI runtime: $AI_STATUS"
fi
if [[ "${DEMO_NO_OPEN:-}" != "1" ]]; then
  open "http://localhost:5173"
fi
if [[ -t 0 ]]; then
  read -r -n 1 -p "Press any key to close this launcher window (services keep running)…"
  echo
fi
