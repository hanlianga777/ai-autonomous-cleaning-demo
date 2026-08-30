import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { resolve } from "node:path";
import test from "node:test";
import { build } from "esbuild";

const entryPoint = resolve(import.meta.dirname, "../src/components/prototype/analyticsViewModel.ts");
const bundled = await build({ entryPoints: [entryPoint], bundle: true, format: "esm", platform: "node", target: "node20", write: false, logLevel: "silent" });
const source = Buffer.from(bundled.outputFiles[0].text).toString("base64");
const analytics = await import(`data:text/javascript;base64,${source}`);

const overview = {
  source: "DEMO_HISTORY + RUNTIME", period: { days: 30, start: "2026-08-01T00:00:00Z", end: "2026-08-30T00:00:00Z" },
  kpis: { autonomous_closure_rate: 80, human_intervention_rate: 10, first_pass_success_rate: 75, average_response_time_minutes: null, average_closure_time_minutes: 24 },
  denominators: { autonomous_closure_rate: "已终态事件 / 可自主处置终态事件" }, heatmap: [], time_distribution: [], robot_utilization: [], event_structure: [], source_counts: {}, metric_definitions: {},
};

test("Analytics query turns browser-local calendar dates into explicit UTC bounds and locked time slots", () => {
  const query = analytics.analyticsQuery({ eventType: "liquid", since: "2026-08-01", until: "2026-08-29", timeSlot: "14-18" });
  assert.equal(query.get("event_type"), "liquid");
  assert.equal(query.get("since"), new Date("2026-08-01T00:00:00.000").toISOString());
  assert.equal(query.get("until"), new Date("2026-08-29T23:59:59.999").toISOString());
  assert.equal(query.get("time_slot"), "14-18");
  assert.equal(analytics.analyticsQuery({ eventType: "", since: "", until: "", timeSlot: "13-17" }).toString(), "");
});

test("today's local end bound never asks backend for future data", () => {
  const now = new Date("2026-08-30T10:00:00+08:00");
  assert.equal(analytics.localDateToUtcIso("2026-08-30", "end", now), now.toISOString());
  assert.equal(analytics.localDateToUtcIso("2026-08-29", "end", now), new Date("2026-08-29T23:59:59.999").toISOString());
});

test("KPI rendering preserves unavailable values and explicit denominators", () => {
  assert.equal(analytics.formatMetric(null, "分钟"), "—");
  assert.equal(analytics.formatMetric(12.5, "%"), "12.5%");
  assert.equal(analytics.denominatorFor(overview, "autonomous_closure_rate"), "已终态事件 / 可自主处置终态事件");
  assert.equal(analytics.denominatorFor(overview, "average_response_time_minutes"), "统计口径未返回");
  overview.kpis.denominators = { autonomous_closure_rate: 9 };
  overview.metric_definitions.autonomous_closure_rate = "有效业务结论为已形成处置结论的非系统异常事件。";
  assert.deepEqual(analytics.metricEvidence(overview, "autonomous_closure_rate"), { sample: "有效业务结论 9", definition: "有效业务结论为已形成处置结论的非系统异常事件。" });
});

test("hotspot drill-down carries spatial and currently selected evidence filters into Event Center", () => {
  const url = analytics.hotspotDrilldownUrl({ zone_id: "a-lobby", label: "A栋主大堂", map_id: "A_1F", x: 10, y: 20, count: 4, event_type: "liquid", time_slot: "14-18" }, { eventType: "", since: "", until: "", timeSlot: "14-18" }, overview.period);
  assert.equal(url, "/events?map_id=A_1F&x=10&y=20&event_type=liquid&since=2026-08-01T00%3A00%3A00Z&until=2026-08-30T00%3A00%3A00Z&time_slot=14-18");
});

test("server hotspot bounds are authoritative and never overwritten by UI date filters", () => {
  const url = analytics.hotspotDrilldownUrl({ zone_id: "a-lobby", label: "A栋主大堂", map_id: "A_1F", x: 10, y: 20, count: 4, event_type: "liquid", drilldown_url: "/events?map_id=A_1F&x=10&y=20&event_type=liquid&since=2026-08-05T00%3A00%3A00Z&until=2026-08-07T00%3A00%3A00Z&time_slot=10-14" }, { eventType: "can", since: "2026-08-01", until: "2026-08-30", timeSlot: "14-18" }, overview.period);
  assert.match(url, /since=2026-08-05T00%3A00%3A00Z/);
  assert.match(url, /until=2026-08-07T00%3A00%3A00Z/);
  assert.match(url, /time_slot=10-14/);
  assert.doesNotMatch(url, /time_slot=14-18/);
});

test("heat radius is derived from backend event count, not array position", () => {
  assert.ok(analytics.heatmapRadius(16) > analytics.heatmapRadius(1));
  assert.equal(analytics.heatmapRadius(-1), 12);
});
