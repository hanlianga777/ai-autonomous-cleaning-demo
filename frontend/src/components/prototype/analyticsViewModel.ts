/** Pure contracts and formatting for the read-only P1-E operations analytics view. */

export type AnalyticsFilters = { eventType: string; since: string; until: string; timeSlot: string };

export type AnalyticsKpis = {
  autonomous_closure_rate: number | null;
  human_intervention_rate: number | null;
  first_pass_success_rate: number | null;
  average_response_time_minutes: number | null;
  average_closure_time_minutes: number | null;
  period_days?: number;
  total_events?: number;
  denominators?: Record<string, string | number | null>;
};

export type AnalyticsHeatmapPoint = {
  zone_id: string;
  label: string;
  map_id: string;
  x: number;
  y: number;
  count: number;
  event_type?: string;
  time_slot?: string;
  average_closure_time_minutes?: number | null;
  drilldown_url?: string;
};

export type AnalyticsOverview = {
  source: string;
  period: { days: number; start?: string; end?: string; ending?: string };
  kpis: AnalyticsKpis;
  denominators?: Record<string, string | number | null>;
  heatmap: AnalyticsHeatmapPoint[];
  time_distribution: Array<{ hour: number; label: string; count: number }>;
  robot_utilization: Array<{ robot_id: string; robot_name: string; tasks: number; active_minutes: number; available_minutes: number; utilization: number | null }>;
  event_structure: Array<{ event_type: string; label: string; count: number }>;
  source_counts: Record<string, number>;
  metric_definitions: Record<string, string>;
  prediction_plan: {
    source: string;
    disclaimer: string;
    prepositioning: Array<{ signal: string; risk: string; time: string; robot_id: string; robot_name: string; location: string; action: string }>;
    cleaning_playbooks: Array<{ object: string; action: string; guardrail: string }>;
  };
};

export const DEFAULT_ANALYTICS_FILTERS: AnalyticsFilters = { eventType: "", since: "", until: "", timeSlot: "" };
export const TIME_SLOTS = ["", "06-10", "10-14", "14-18", "18-22"] as const;

function validHour(value: string): string {
  return /^\d{1,2}$/.test(value) && Number(value) >= 0 && Number(value) <= 23 ? String(Number(value)) : "";
}

export function analyticsQuery(filters: AnalyticsFilters): URLSearchParams {
  const query = new URLSearchParams();
  if (filters.eventType) query.set("event_type", filters.eventType);
  const since = localDateToUtcIso(filters.since, "start");
  const until = localDateToUtcIso(filters.until, "end");
  if (since) query.set("since", since);
  if (until) query.set("until", until);
  if ((TIME_SLOTS as readonly string[]).includes(filters.timeSlot) && filters.timeSlot) query.set("time_slot", filters.timeSlot);
  return query;
}

/** Convert the browser's local calendar day to an explicit backend UTC boundary. */
export function localDateToUtcIso(value: string, edge: "start" | "end", now = new Date()): string {
  if (!value) return "";
  if (!/^\d{4}-\d\d-\d\d$/.test(value)) return value;
  let instant = new Date(`${value}T${edge === "start" ? "00:00:00.000" : "23:59:59.999"}`);
  if (!Number.isFinite(instant.getTime())) return "";
  const sameLocalDay = instant.getFullYear() === now.getFullYear() && instant.getMonth() === now.getMonth() && instant.getDate() === now.getDate();
  if (edge === "end" && sameLocalDay && instant > now) instant = now;
  return instant.toISOString();
}

export function formatMetric(value: number | null | undefined, unit: "%" | "分钟"): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return unit === "%" ? `${value}%` : `${value} 分钟`;
}

export function denominatorFor(overview: AnalyticsOverview, metric: string): string {
  const value = overview.denominators?.[metric] ?? overview.kpis.denominators?.[metric] ?? overview.metric_definitions?.[metric];
  return value === null || value === undefined || value === "" ? "统计口径未返回" : String(value);
}

const SAMPLE_LABELS: Record<string, string> = {
  autonomous_closure_rate: "有效业务结论", human_intervention_rate: "有效业务结论",
  first_pass_success_rate: "首次验收已记录", average_response_time_minutes: "已观测响应", average_closure_time_minutes: "有效已闭环",
};

export function metricEvidence(overview: AnalyticsOverview, metric: string): { sample: string; definition: string } {
  const value = overview.kpis.denominators?.[metric] ?? overview.denominators?.[metric];
  const sample = typeof value === "number" && Number.isFinite(value) ? `${SAMPLE_LABELS[metric] ?? "有效样本"} ${value}` : denominatorFor(overview, metric);
  return { sample, definition: overview.metric_definitions?.[metric] ?? "统计口径未返回" };
}

/** Analytics has no route logic: it only projects its selected source facts into Event Center query state. */
export function hotspotDrilldownUrl(point: AnalyticsHeatmapPoint, filters: AnalyticsFilters, period: AnalyticsOverview["period"]): string {
  const backend = point.drilldown_url ? new URL(point.drilldown_url, "http://cleanops.local") : new URL("/events", "http://cleanops.local");
  backend.pathname = "/events";
  const setFallback = (key: string, value: string | undefined) => { if (!backend.searchParams.has(key) && value) backend.searchParams.set(key, value); };
  setFallback("map_id", point.map_id);
  setFallback("x", String(point.x));
  setFallback("y", String(point.y));
  setFallback("event_type", point.event_type || filters.eventType);
  // Backend builds these bounds from the exact aggregation window. Never replace them with UI date strings.
  setFallback("since", localDateToUtcIso(filters.since, "start") || period.start);
  setFallback("until", localDateToUtcIso(filters.until, "end") || period.end || period.ending);
  setFallback("time_slot", point.time_slot === "all" ? "" : point.time_slot || filters.timeSlot);
  return `${backend.pathname}${backend.search}`;
}

export function heatmapRadius(count: number): number {
  return Math.min(31, Math.max(12, 9 + Math.sqrt(Math.max(0, count)) * 5));
}
