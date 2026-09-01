import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../src/components/prototype");
const [data, monitor, detail, workbench, archive, analytics, evidence] = await Promise.all([
  readFile(resolve(root, "data.ts"), "utf8"),
  readFile(resolve(root, "CameraMonitorGrid.tsx"), "utf8"),
  readFile(resolve(root, "EventDetailPanel.tsx"), "utf8"),
  readFile(resolve(root, "PrototypeWorkbench.tsx"), "utf8"),
  readFile(resolve(root, "EventArchiveView.tsx"), "utf8"),
  readFile(resolve(root, "AnalyticsView.tsx"), "utf8"),
  readFile(resolve(root, "EventStageEvidence.tsx"), "utf8"),
]);

test("hidden demo controls retain a compact AI cleaning event entry", () => {
  assert.match(monitor, /AI 清洁事件/);
  assert.match(monitor, /\{scenario\.triggerLabel\}/);
  assert.doesNotMatch(monitor, /Demo01|presentationFocus|Live 模型优先/);
  for (const demo of ["Demo01", "Demo02", "Demo03", "Demo04"]) assert.match(data, new RegExp(`demoCode: "${demo}"`));
  assert.match(data, /多视角取证排除反光歧义/);
  assert.match(data, /跨楼、电梯与连廊的路线调度/);
  assert.match(data, /能力不足时转人工，仍保留验收闭环/);
});

test("terminal workbench events can hand off the exact saved event to the read-only archive", () => {
  assert.match(detail, /发现 AI 清洁事件/);
  assert.doesNotMatch(detail, /当前处置链路|回到当前进度/);
  assert.match(workbench, /archiveDemoEntryUrl\(eventId\)/);
  assert.match(workbench, /onViewArchive=\{\(eventId\) => navigate\("events", eventId\)\}/);
  assert.match(evidence, /查看已保存档案/);
  assert.match(archive, /刚完成的演示事件已进入只读档案/);
  assert.match(archive, /不会触发重跑/);
});

test("analytics keeps its insight surface separate from a completed demo event", () => {
  assert.doesNotMatch(analytics, /本次演示的运营价值|RecentDemoInsight/);
  assert.match(analytics, /<AnalyticsAdviceCards \/>/);
});

test("the fixed heatmap uses deterministic organic multicolor density areas without contour rings", () => {
  assert.match(analytics, /function HistoricalHeatmapOverlay/);
  const overlay = analytics.slice(analytics.indexOf("function HistoricalHeatmapOverlay"), analytics.indexOf("function KpiCard"));
  assert.match(overlay, /<path d="M19 58/);
  assert.match(overlay, /heatmap-red/);
  assert.match(overlay, /heatmap-blue/);
  assert.match(overlay, /heatmap-gold/);
  assert.doesNotMatch(overlay, /<ellipse/);
  assert.doesNotMatch(overlay, /strokeDasharray/);
});
