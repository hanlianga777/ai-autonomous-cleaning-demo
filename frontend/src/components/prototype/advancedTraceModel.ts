/** Pure, deliberately defensive helpers for the read-only Advanced trace projection. */

export type TraceSource = "LIVE MODEL" | "DETERMINISTIC RUNTIME" | "CONTROLLED EVIDENCE" | "POC SIMULATION" | "REPLAY" | "AUTH REQUIRED / NOT CONNECTED" | string;
export type TraceNode = {
  id: string;
  group: "AI" | "SPATIAL" | "RUNTIME";
  label: string;
  status: string;
  source: TraceSource;
  trigger_source?: string | null;
  start_time?: string | null;
  duration_ms?: number | null;
  input_summary?: Record<string, unknown> | null;
  output_summary?: Record<string, unknown> | null;
  evidence?: Array<{ camera_id?: string; role?: string; url?: string }>;
  error?: { type?: string; code?: string; message?: string } | null;
};

export type TraceToolCall = {
  id: string;
  name: string;
  trigger_source?: string | null;
  start_time?: string | null;
  duration_ms?: number | null;
  status: string;
  input_summary?: Record<string, unknown> | null;
  result_summary?: Record<string, unknown> | null;
  trace_id?: string | null;
  source?: TraceSource | null;
};

export type AdvancedTrace = {
  trace_id?: string | null;
  trace_status?: string | null;
  event_id?: string | null;
  mode?: string | null;
  runtime?: { provider?: string | null; model?: string | null; configured?: boolean | null; last_request_status?: string | null; last_latency_ms?: number | null; last_request_at?: string | null } | null;
  events?: Array<{ event_id?: string; trace_id?: string; state?: string }>;
  nodes?: TraceNode[];
  tool_calls?: TraceToolCall[];
  reality?: Array<{ component?: string; status?: TraceSource; execution_status?: string | null; detail?: string; replacement?: string }>;
  errors?: Array<{ type?: string; code?: string; message?: string }>;
  linked_tasks?: Array<Record<string, unknown>>;
  runtime_info?: {
    app_name?: string;
    backend_version?: string;
    release_contract?: string;
    capabilities?: string[];
    cloud_status?: string;
    vlm_model?: string;
    agent_model?: string;
    evidence_mode?: string;
  } | null;
};

const FORBIDDEN_KEY = /api.?key|secret|token|authorization|reasoning|chain.?of.?thought|scratchpad|\benv\b/i;

export function advancedTraceUrl(eventId?: string | null): string {
  return eventId ? `/api/advanced/trace?event_id=${encodeURIComponent(eventId)}` : "/api/advanced/trace";
}

/** A late response must never replace a trace selected by a newer request. */
export function acceptsTraceResponse(request: number, latestRequest: number): boolean {
  return request === latestRequest;
}

export function selectedTraceNode(nodes: TraceNode[], selectedId: string | null): TraceNode | null {
  return nodes.find((node) => node.id === selectedId) ?? null;
}

export function nextSelectedNode(nodes: TraceNode[], currentId: string | null): string | null {
  return nodes.some((node) => node.id === currentId) ? currentId : nodes[0]?.id ?? null;
}

export function sourceBadgeLabel(source?: TraceSource | null): string {
  return source || "SOURCE NOT RECORDED";
}

export function sourceBadgeClass(source?: TraceSource | null): string {
  if (source === "LIVE MODEL") return "border-sky-200 bg-sky-50 text-sky-800";
  if (source === "DETERMINISTIC RUNTIME") return "border-slate-200 bg-slate-100 text-slate-700";
  if (source === "CONTROLLED EVIDENCE") return "border-amber-200 bg-amber-50 text-amber-800";
  if (source === "CONTROLLED EDGE DEMO") return "border-orange-200 bg-orange-50 text-orange-800";
  if (source === "POC SIMULATION") return "border-violet-200 bg-violet-50 text-violet-800";
  if (source === "REPLAY") return "border-indigo-200 bg-indigo-50 text-indigo-800";
  if (source === "AUTH REQUIRED / NOT CONNECTED") return "border-rose-200 bg-rose-50 text-rose-800";
  return "border-slate-200 bg-white text-slate-500";
}

export function traceStatusLabel(status?: string | null): string {
  const labels: Record<string, string> = {
    COMPLETED: "已完成", SUCCESS: "成功", FAILED: "失败", ERROR: "错误", IDLE: "空闲",
    NOT_TRIGGERED: "未触发", EVIDENCE_ALREADY_SUFFICIENT: "证据已充分", RUNNING: "进行中",
  };
  return status ? labels[status] ?? status : "未记录";
}

export function traceIdentityLabel(traceId?: string | null, traceStatus?: string | null): string {
  if (traceStatus === "LEGACY_MISSING") return "历史记录未记录 Trace ID";
  if (traceStatus === "NO_EVENT") return "暂无事件";
  return traceId || "—";
}

function safeValue(value: unknown, depth = 0): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value).slice(0, 240);
  if (Array.isArray(value)) return value.slice(0, 6).map((entry) => safeValue(entry, depth + 1)).join("、");
  if (typeof value === "object") return depth > 1 ? "[结构化对象]" : Object.entries(value as Record<string, unknown>)
    .filter(([key]) => !FORBIDDEN_KEY.test(key))
    .slice(0, 6)
    .map(([key, entry]) => `${key}: ${safeValue(entry, depth + 1)}`).join("；");
  return "[不可展示]";
}

/** No raw JSON: drop all sensitive/reasoning-looking keys before rendering summary facts. */
export function safeSummaryEntries(summary?: Record<string, unknown> | null): Array<[string, string]> {
  if (!summary || typeof summary !== "object") return [];
  return Object.entries(summary)
    .filter(([key]) => !FORBIDDEN_KEY.test(key))
    .slice(0, 12)
    .map(([key, value]) => [key, safeValue(value)]);
}

/** Defensive rendering guard in addition to backend-side safe trace projection. */
export function safeTraceText(value?: string | null): string {
  if (!value) return "—";
  return FORBIDDEN_KEY.test(value) ? "[敏感字段已隐藏]" : value.slice(0, 320);
}

/** Never surface credential-looking evidence URLs in the DOM. */
export function safeEvidenceUrl(value?: string): string | null {
  if (!value || FORBIDDEN_KEY.test(value)) return null;
  try {
    const base = typeof window === "undefined" ? "http://cleanops.local" : window.location.origin;
    const parsed = new URL(value, base);
    return [...parsed.searchParams.keys()].some((key) => FORBIDDEN_KEY.test(key)) ? null : value;
  } catch { return null; }
}

export function formatTraceTime(value?: string | null): string {
  if (!value) return "—";
  const time = Date.parse(value);
  return Number.isFinite(time) ? new Date(time).toLocaleString("zh-CN", { hour12: false }) : value;
}
