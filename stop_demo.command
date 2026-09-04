#!/bin/bash
# Stops only PID records that still prove launcher ownership at signal time.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="${DEMO_LOG_DIR:-$PROJECT_DIR/.demo-logs}"
BACKEND_PID_FILE="$LOG_DIR/backend.pid"
FRONTEND_PID_FILE="$LOG_DIR/frontend.pid"
PID_FILE="$PROJECT_DIR/.demo-pids"
BACKEND_PORT="${DEMO_BACKEND_PORT:-8002}"
FRONTEND_PORT="${DEMO_FRONTEND_PORT:-5176}"

# shellcheck source=scripts/runtime_launcher_lib.sh
source "$PROJECT_DIR/scripts/runtime_launcher_lib.sh"

stop_if_owned() {
  local service="$1" port="$2" record="$3" cwd="$4"
  if [[ ! -f "$record" ]]; then return 0; fi
  if runtime_record_matches_listener "$record" "$service" "$port" "$cwd"; then
    if ! runtime_terminate_owned "$service" "$port" "$record" "$cwd"; then
      STOP_FAILURES=1
    fi
  else
    echo "[$service] stale or untrusted PID record removed without signaling a process."
    rm -f "$record"
  fi
}

STOP_FAILURES=0
stop_if_owned backend "$BACKEND_PORT" "$BACKEND_PID_FILE" "$BACKEND_DIR"
stop_if_owned frontend "$FRONTEND_PORT" "$FRONTEND_PID_FILE" "$FRONTEND_DIR"
rm -f "$PID_FILE"

for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
  if runtime_port_in_use "$port"; then
    echo "[runtime] service remains on port $port and is not launcher-owned:"
    runtime_describe_listener "$port"
  fi
done
if [[ -t 0 ]]; then
  read -r -n 1 -p "Press any key to close this stopper window…"
  echo
fi
exit "$STOP_FAILURES"
