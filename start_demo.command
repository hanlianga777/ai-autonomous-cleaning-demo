#!/bin/bash
# Starts the one official local Interview Demo runtime. It never silently
# adopts, kills, or reroutes around a process it cannot prove it launched.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="${DEMO_LOG_DIR:-$PROJECT_DIR/.demo-logs}"
PID_FILE="$PROJECT_DIR/.demo-pids"
BACKEND_PID_FILE="$LOG_DIR/backend.pid"
FRONTEND_PID_FILE="$LOG_DIR/frontend.pid"
BACKEND_PORT="${DEMO_BACKEND_PORT:-8000}"
FRONTEND_PORT="${DEMO_FRONTEND_PORT:-5173}"

# shellcheck source=scripts/runtime_launcher_lib.sh
source "$PROJECT_DIR/scripts/runtime_launcher_lib.sh"
mkdir -p "$LOG_DIR"

ensure_backend() {
  if runtime_port_in_use "$BACKEND_PORT"; then
    if runtime_preflight_backend "$BACKEND_PORT"; then
      if runtime_record_matches_listener "$BACKEND_PID_FILE" backend "$BACKEND_PORT" "$BACKEND_DIR"; then
        echo "[backend] http://localhost:$BACKEND_PORT (verified launcher-owned runtime reused)"
        return
      fi
      echo "[backend] compatible API is not launcher-owned; refusing silent reuse or termination."
      runtime_describe_listener "$BACKEND_PORT"
      exit 1
    fi
    if runtime_port_in_use "$BACKEND_PORT"; then
      if runtime_record_matches_listener "$BACKEND_PID_FILE" backend "$BACKEND_PORT" "$BACKEND_DIR"; then
        echo "[backend] incompatible launcher-owned API detected; restarting it."
        runtime_terminate_owned backend "$BACKEND_PORT" "$BACKEND_PID_FILE" "$BACKEND_DIR"
      else
        echo "[backend] incompatible or unknown service; refusing to terminate it."
        runtime_describe_listener "$BACKEND_PORT"
        exit 1
      fi
    fi
  else
    rm -f "$BACKEND_PID_FILE"
  fi
  if [[ ! -x "$BACKEND_DIR/.venv/bin/python" ]]; then
    echo "[backend] creating Python virtual environment…"
    python3 -m venv "$BACKEND_DIR/.venv"
    "$BACKEND_DIR/.venv/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
  fi
  if ! "$BACKEND_DIR/.venv/bin/python" -c "import multipart, langgraph, PIL" >/dev/null 2>&1; then
    echo "[backend] installing required API and image-evidence support…"
    "$BACKEND_DIR/.venv/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
  fi
  local launched_pid
  (
    cd "$BACKEND_DIR"
    nohup "$BACKEND_DIR/.venv/bin/uvicorn" main:app --host 127.0.0.1 --port "$BACKEND_PORT" >"$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$LOG_DIR/backend.spawn.pid"
  )
  launched_pid="$(cat "$LOG_DIR/backend.spawn.pid")"; rm -f "$LOG_DIR/backend.spawn.pid"
  for _ in {1..30}; do
    local pid
    pid="$(runtime_listener_pid "$BACKEND_PORT" 2>/dev/null || true)"
    if [[ "$pid" == "$launched_pid" ]] && runtime_write_pid_record "$BACKEND_PID_FILE" backend "$BACKEND_PORT" "$pid" "$BACKEND_DIR"; then
      echo "[backend] http://localhost:$BACKEND_PORT (started PID $pid)"
      return
    fi
    sleep 0.2
  done
  echo "[backend] failed to create a verified listener. See $LOG_DIR/backend.log"
  exit 1
}

ensure_frontend_slot() {
  if ! runtime_port_in_use "$FRONTEND_PORT"; then return; fi
  if runtime_record_matches_listener "$FRONTEND_PID_FILE" frontend "$FRONTEND_PORT" "$FRONTEND_DIR"; then return; fi
  echo "[frontend] port $FRONTEND_PORT is not a verified launcher-owned Vite; refusing reuse or termination."
  runtime_describe_listener "$FRONTEND_PORT"; exit 1
}

ensure_frontend() {
  if runtime_port_in_use "$FRONTEND_PORT" && runtime_record_matches_listener "$FRONTEND_PID_FILE" frontend "$FRONTEND_PORT" "$FRONTEND_DIR"; then
    echo "[frontend] http://localhost:$FRONTEND_PORT (verified launcher-owned Vite reused)"
    return
  fi
  if runtime_port_in_use "$FRONTEND_PORT"; then
    echo "[frontend] port $FRONTEND_PORT changed after slot validation; refusing reuse."
    runtime_describe_listener "$FRONTEND_PORT"; exit 1
  fi
  rm -f "$FRONTEND_PID_FILE"
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    echo "[frontend] installing npm packages…"
    (cd "$FRONTEND_DIR" && npm install --cache .npm-cache)
  fi
  local launched_pid
  (
    cd "$FRONTEND_DIR"
    nohup "$FRONTEND_DIR/node_modules/.bin/vite" --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort >"$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$LOG_DIR/frontend.spawn.pid"
  )
  launched_pid="$(cat "$LOG_DIR/frontend.spawn.pid")"; rm -f "$LOG_DIR/frontend.spawn.pid"
  for _ in {1..30}; do
    local pid
    pid="$(runtime_listener_pid "$FRONTEND_PORT" 2>/dev/null || true)"
    if [[ "$pid" == "$launched_pid" ]] && runtime_write_pid_record "$FRONTEND_PID_FILE" frontend "$FRONTEND_PORT" "$pid" "$FRONTEND_DIR"; then
      echo "[frontend] http://localhost:$FRONTEND_PORT (started PID $pid)"
      return
    fi
    sleep 0.2
  done
  echo "[frontend] failed to create verified Vite on port $FRONTEND_PORT. See $LOG_DIR/frontend.log"
  exit 1
}

# Guard the frontend slot before creating a backend process that the user did
# not ask to keep when an unknown browser service blocks the official entry.
ensure_frontend_slot
ensure_backend
ensure_frontend

if ! runtime_preflight_backend "$BACKEND_PORT" || ! runtime_record_matches_listener "$BACKEND_PID_FILE" backend "$BACKEND_PORT" "$BACKEND_DIR"; then
  echo "CleanOps demo was not opened because the backend preflight failed."
  exit 1
fi
if ! runtime_record_matches_listener "$FRONTEND_PID_FILE" frontend "$FRONTEND_PORT" "$FRONTEND_DIR"; then
  echo "[frontend] verified Vite ownership disappeared before browser open."
  runtime_describe_listener "$FRONTEND_PORT"
  exit 1
fi

cat "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE" > "$PID_FILE"
echo
echo "CleanOps customer demo is ready. API: http://localhost:$BACKEND_PORT/docs"
if [[ "${DEMO_NO_OPEN:-}" != "1" ]]; then
  open "http://localhost:$FRONTEND_PORT"
fi
if [[ -t 0 ]]; then
  read -r -n 1 -p "Press any key to close this launcher window (services keep running)…"
  echo
fi
