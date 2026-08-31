import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const source = await readFile(resolve(import.meta.dirname, "../src/components/prototype/AnalyticsView.tsx"), "utf8");
const chat = await readFile(resolve(import.meta.dirname, "../src/components/robot-operations/RobotOperationsPanel.tsx"), "utf8");

test("analytics is a fixed customer operating view without a filter form or duplicate H1", () => {
  assert.match(source, /const filters = DEFAULT_ANALYTICS_FILTERS/);
  assert.doesNotMatch(source, /useState<AnalyticsFilters>|updateFilters|<h1\b|<select\b/);
  assert.doesNotMatch(source, /Data Composition|数据构成/);
  assert.doesNotMatch(source, /样本：|统计口径|运营概览/);
  assert.match(source, /处置与闭环效率/);
  assert.match(source, /<AnalyticsChart option=\{efficiencyOption\}/);
});

test("analytics hotspot labels and the fixed Chat are customer-facing", () => {
  assert.match(source, /projectAnalyticsHeatmapPoint\(point\)/);
  assert.doesNotMatch(source, /projectMapCoordinate\(point\.map_id/);
  assert.match(source, /title=\{`\$\{mapLabel\(key\)\}：\$\{count\} 条事件`\}/);
  assert.match(source, /hotspotIndex < 3 \? "animate-pulse"/);
  assert.match(source, /border-0 bg-transparent/);
  assert.doesNotMatch(source, /border-white\/90/);
  assert.match(source, /<AnalyticsAgentChat pageContext=\{analyticsAgentContext\}/);
  assert.doesNotMatch(chat, /Microphone|语音输入|Voice/);
});

test("analytics removes auxiliary copy and the floor-button footer while retaining direct map drill-down", () => {
  assert.doesNotMatch(source, /近30天园区运营情况|选择楼层热点查看事件档案|可访问楼层热点列表|点击地图或楼层入口/);
  assert.match(source, /onClick=\{\(\) => navigateToHotspot\(entries\[0\]\.index\)\}/);
  const fixedAnalyticsChat = chat.split("export function AnalyticsAgentChat", 2)[1];
  assert.doesNotMatch(fixedAnalyticsChat, /协助查询事件与执行进度/);
  assert.doesNotMatch(chat, /基于近 30 天运营情况生成/);
  assert.match(chat, /adviceCardLines/);
  assert.doesNotMatch(chat, /line-clamp-2/);
});
