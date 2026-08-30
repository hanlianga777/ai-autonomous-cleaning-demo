#!/bin/bash
# Shared safety checks for the local, interview-facing launcher. All process
# termination flows through ownership verification in this file.

RUNTIME_RELEASE_CONTRACT="cleanops.interview.v1"
RUNTIME_REQUIRED_CAPABILITIES=(stage_runtime event_archive analytics robot_operations advanced_observability spatial_v2)

runtime_listener_pids() { lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null | sort -u; }

runtime_listener_pid() {
  local pids count
  pids="$(runtime_listener_pids "$1")"
  count="$(printf '%s\n' "$pids" | sed '/^$/d' | wc -l | tr -d ' ')"
  [[ "$count" == "1" ]] || return 1
  printf '%s\n' "$pids"
}

runtime_port_in_use() { [[ -n "$(runtime_listener_pids "$1")" ]]; }
runtime_process_command() { ps -p "$1" -o command= 2>/dev/null | sed 's/^[[:space:]]*//'; }
runtime_process_cwd() { lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1; }
runtime_process_started_at() { ps -p "$1" -o lstart= 2>/dev/null | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }
runtime_command_signature() { printf '%s' "$1" | LC_ALL=C shasum -a 256 | awk '{print $1}'; }

runtime_command_is_expected() {
  local service="$1" port="$2" command="$3"
  case "$service" in
    # `ps` reports a Vite shell script as either an absolute script path or
    # `node ./node_modules/.bin/vite` after `cd frontend`. Both are exact
    # launcher forms; arbitrary marker substrings are deliberately rejected.
    # macOS may expose the uvicorn shebang interpreter as an absolute, capital
    # `Python` executable. Accept one interpreter token only; the following
    # script path and every server argument remain anchored.
    backend) [[ "$command" =~ ^([^[:space:]]+[[:space:]]+)?[^[:space:]]*/backend/\.venv/bin/uvicorn[[:space:]]+main:app[[:space:]]+--host[[:space:]]+127\.0\.0\.1[[:space:]]+--port[[:space:]]+"$port"[[:space:]]*$ ]] ;;
    frontend) [[ "$command" =~ ^(node[[:space:]]+)?(\./node_modules/\.bin/vite|[^[:space:]]*/frontend/node_modules/\.bin/vite)[[:space:]]+--host[[:space:]]+127\.0\.0\.1[[:space:]]+--port[[:space:]]+"$port"[[:space:]]+--strictPort[[:space:]]*$ ]] ;;
    *) return 1 ;;
  esac
}

runtime_describe_listener() {
  local port="$1" pid command cwd
  pid="$(runtime_listener_pid "$port" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    echo "[runtime] port $port has multiple listeners or no uniquely identifiable listener."
    runtime_listener_pids "$port" | while IFS= read -r item; do
      [[ -n "$item" ]] && echo "[runtime] port $port PID $item command: $(runtime_process_command "$item")"
    done
    return
  fi
  command="$(runtime_process_command "$pid")"; cwd="$(runtime_process_cwd "$pid")"
  echo "[runtime] port $port PID $pid command: $command"
  [[ -n "$cwd" ]] && echo "[runtime] port $port PID $pid cwd: $cwd"
}

runtime_write_pid_record() {
  local file="$1" service="$2" port="$3" pid="$4" cwd="$5" started command actual_cwd signature
  started="$(runtime_process_started_at "$pid")"
  command="$(runtime_process_command "$pid")"; actual_cwd="$(runtime_process_cwd "$pid")"
  [[ -n "$started" && "$actual_cwd" == "$cwd" ]] || return 1
  runtime_command_is_expected "$service" "$port" "$command" || return 1
  signature="$(runtime_command_signature "$command")"
  printf '%s|%s|%s|%s|%s|%s\n' "$service" "$port" "$pid" "$started" "$cwd" "$signature" > "$file"
}

runtime_record_matches_listener() {
  local file="$1" expected_service="$2" expected_port="$3" expected_cwd="$4"
  local service port pid started cwd signature listener command actual_cwd actual_started actual_signature
  [[ -f "$file" ]] || return 1
  IFS='|' read -r service port pid started cwd signature < "$file" || return 1
  [[ "$service" == "$expected_service" && "$port" == "$expected_port" && "$cwd" == "$expected_cwd" && -n "$signature" ]] || return 1
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  listener="$(runtime_listener_pid "$expected_port" 2>/dev/null || true)"
  [[ "$listener" == "$pid" ]] || return 1
  command="$(runtime_process_command "$pid")"; actual_cwd="$(runtime_process_cwd "$pid")"; actual_started="$(runtime_process_started_at "$pid")"; actual_signature="$(runtime_command_signature "$command")"
  runtime_command_is_expected "$expected_service" "$expected_port" "$command" && [[ "$actual_cwd" == "$expected_cwd" && "$actual_started" == "$started" && "$actual_signature" == "$signature" ]]
}

runtime_wait_for_port_release() {
  local port="$1"
  for _ in {1..30}; do runtime_port_in_use "$port" || return 0; sleep 0.2; done
  return 1
}

runtime_terminate_owned() {
  local service="$1" port="$2" record_file="$3" cwd="$4" pid
  if ! runtime_record_matches_listener "$record_file" "$service" "$port" "$cwd"; then
    echo "[$service] refusing SIGTERM: PID record does not prove current launcher ownership."
    runtime_port_in_use "$port" && runtime_describe_listener "$port"
    return 1
  fi
  pid="$(runtime_listener_pid "$port")"
  echo "[$service] stopping launcher-owned PID $pid on port $port"
  kill -TERM "$pid"
  if ! runtime_wait_for_port_release "$port"; then
    echo "[$service] PID $pid did not release port $port after SIGTERM; refusing to escalate."
    return 1
  fi
  rm -f "$record_file"
}

runtime_health_contract_ok() {
  local expected_contract="$1"
  python3 -c 'import json,sys; payload=json.load(sys.stdin); expected,required=sys.argv[1],set(sys.argv[2].split()); capabilities=payload.get("capabilities"); valid=(payload.get("release_contract")==expected and isinstance(capabilities,list) and all(isinstance(item,str) for item in capabilities) and required.issubset(set(capabilities))); raise SystemExit(0 if valid else 1)' "$expected_contract" "${RUNTIME_REQUIRED_CAPABILITIES[*]}"
}

runtime_fetch_json() {
  local url="$1" response
  response="$(curl --connect-timeout 1 --max-time 3 --silent --show-error --write-out $'\n%{http_code}' "$url" 2>/dev/null || true)"
  RUNTIME_HTTP_STATUS="${response##*$'\n'}"; RUNTIME_HTTP_BODY="${response%$'\n'*}"
  [[ "$RUNTIME_HTTP_STATUS" =~ ^2[0-9][0-9]$ ]] || return 1
  python3 -c 'import json,sys; json.load(sys.stdin)' <<< "$RUNTIME_HTTP_BODY" >/dev/null
}

runtime_openapi_ok() {
  python3 -c 'import json,sys; spec=json.load(sys.stdin); paths=spec.get("paths", {}); required={"/api/event-archive":"get", "/api/robot-operations/sessions":"post", "/api/spatial/overview":"get"}; raise SystemExit(0 if all(method in paths.get(path, {}) for path, method in required.items()) else 1)' <<< "$RUNTIME_HTTP_BODY"
}

runtime_robots_ok() {
  python3 -c 'import json,sys; robots=json.load(sys.stdin); ids={item.get("id") for item in robots if isinstance(item,dict)} if isinstance(robots,list) else set(); raise SystemExit(0 if {"robot-a","robot-b","robot-c","robot-d"}.issubset(ids) else 1)' <<< "$RUNTIME_HTTP_BODY"
}

runtime_preflight_backend() {
  local base="http://127.0.0.1:${1}" check url
  check="health"
  if ! runtime_fetch_json "$base/api/health" || ! runtime_health_contract_ok "$RUNTIME_RELEASE_CONTRACT" <<< "$RUNTIME_HTTP_BODY"; then echo "[preflight] failed: $check (HTTP ${RUNTIME_HTTP_STATUS:-unavailable})"; return 1; fi
  check="robots"; url="$base/api/robots"
  if ! runtime_fetch_json "$url" || ! runtime_robots_ok; then echo "[preflight] failed: $check (HTTP ${RUNTIME_HTTP_STATUS:-unavailable})"; return 1; fi
  for check in spatial event_archive robot_operations_advice advanced_trace; do
    case "$check" in
      spatial) url="$base/api/spatial/overview" ;;
      event_archive) url="$base/api/event-archive?limit=1" ;;
      robot_operations_advice) url="$base/api/robot-operations/advice" ;;
      advanced_trace) url="$base/api/advanced/trace" ;;
    esac
    if ! runtime_fetch_json "$url"; then echo "[preflight] failed: $check (HTTP ${RUNTIME_HTTP_STATUS:-unavailable})"; return 1; fi
  done
  check="openapi"; url="$base/openapi.json"
  if ! runtime_fetch_json "$url" || ! runtime_openapi_ok; then echo "[preflight] failed: $check (HTTP ${RUNTIME_HTTP_STATUS:-unavailable})"; return 1; fi
  echo "[preflight] backend contract, routes, robots and read-only smoke checks passed."
}
