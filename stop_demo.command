#!/bin/bash
# Stops only services whose PIDs were recorded by start_demo.command.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$PROJECT_DIR/.demo-pids"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No CleanOps services were started by this launcher. Nothing to stop."
  exit 0
fi

stopped=0
while IFS= read -r pid; do
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "Stopped process $pid"
    stopped=1
  fi
done < "$PID_FILE"

rm -f "$PID_FILE" "$PROJECT_DIR/.demo-logs/backend.pid" "$PROJECT_DIR/.demo-logs/frontend.pid"
if [[ "$stopped" -eq 0 ]]; then
  echo "No launcher-owned process is currently running."
fi
if [[ -t 0 ]]; then
  read -r -n 1 -p "Press any key to close this stopper window…"
  echo
fi
