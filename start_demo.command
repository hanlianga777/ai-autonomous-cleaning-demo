#!/bin/bash
# Double-click on macOS to launch the Phase 2 demo. It starts only missing
# services and records only the PIDs it owns for stop_demo.command.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/.demo-logs"
PID_FILE="$PROJECT_DIR/.demo-pids"

mkdir -p "$LOG_DIR"

port_in_use() {
  lsof -tiTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

start_backend() {
  if port_in_use 8000; then
    echo "[backend]  http://localhost:8000  (already running)"
    return
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
    echo $! > "$LOG_DIR/backend.pid"
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

{
  [[ -f "$LOG_DIR/backend.pid" ]] && cat "$LOG_DIR/backend.pid"
  [[ -f "$LOG_DIR/frontend.pid" ]] && cat "$LOG_DIR/frontend.pid"
} > "$PID_FILE" || true

sleep 1
echo
echo "CleanOps Phase 8 is ready. API: http://localhost:8000/docs"
if [[ "${DEMO_NO_OPEN:-}" != "1" ]]; then
  open "http://localhost:5173"
fi
if [[ -t 0 ]]; then
  read -r -n 1 -p "Press any key to close this launcher window (services keep running)…"
  echo
fi
