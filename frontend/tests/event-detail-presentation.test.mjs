import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const archive = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventArchiveView.tsx"), "utf8");
const detail = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventDetailPanel.tsx"), "utf8");
const evidence = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventStageEvidence.tsx"), "utf8");

test("Event Center is a customer work-order list using the shared read-only detail shell", () => {
  for (const column of ["事件", "发现时间", "地点", "机器人", "工单状态"]) assert.match(archive, new RegExp(`<span>${column}</span>`));
  assert.match(archive, /grid-cols-\[minmax\(0,72fr\)_minmax\(320px,28fr\)\]/);
  assert.match(archive, /if \(!selectedIdRef\.current && incoming\[0\]\) selectEvent\(incoming\[0\]\.event_id, "replace"\)/);
  assert.match(archive, /<EventDetailPanel event=\{detail\} mode="history"/);
  assert.match(detail, /mode === "history" \? "事件处置详情"/);
});

test("event evidence preserves gated timeline semantics and customer-facing cards", () => {
  assert.match(evidence, /case "MULTI_VIEW"/);
  assert.match(evidence, /grid gap-2 sm:grid-cols-2/);
  assert.match(evidence, /case "HUMAN_REVIEW"/);
  assert.match(evidence, /case "EDGE_DETECTED"/);
  assert.match(evidence, /showDetections=\{detections\}/);
});
