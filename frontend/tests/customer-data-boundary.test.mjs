import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const analytics = await readFile(resolve(import.meta.dirname, "../src/components/prototype/AnalyticsView.tsx"), "utf8");
const archive = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventArchiveView.tsx"), "utf8");
const spatial = await readFile(resolve(import.meta.dirname, "../src/components/prototype/SpatialDispatchView.tsx"), "utf8");
const detail = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventDetailPanel.tsx"), "utf8");
const evidence = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventStageEvidence.tsx"), "utf8");
const monitor = await readFile(resolve(import.meta.dirname, "../src/components/prototype/CameraMonitorGrid.tsx"), "utf8");

test("customer pages expose no data-source or runtime-mode selector", () => {
  const customerShell = `${analytics}\n${archive}`;
  assert.doesNotMatch(customerShell, /数据源\s*<select|数据来源\s*<select|runtimeMode|sourceMode/i);
  assert.doesNotMatch(customerShell, /DEMO_HISTORY|INTERVIEW_RUNTIME|ACCEPTANCE|DEBUG|LEGACY/);
});

test("customer route and event-detail copy omit algorithm names and tiny operational text", () => {
  const customerSurface = `${spatial}\n${detail}\n${evidence}\n${monitor}`;
  assert.doesNotMatch(customerSurface, /aria-label="[^"]*(?:Dijkstra|runtime|trace|telemetry)[^"]*"/i);
  assert.doesNotMatch(customerSurface, /演示控制|\b(?:mock|replay|debug|poc)\b/i);
  assert.doesNotMatch(customerSurface, /text-\[(?:8|9|10|11)px\]/);
});
