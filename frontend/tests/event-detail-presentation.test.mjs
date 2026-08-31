import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const archive = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventArchiveView.tsx"), "utf8");
const detail = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventDetailPanel.tsx"), "utf8");
const evidence = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventStageEvidence.tsx"), "utf8");

test("Event Center is a customer work-order list using the shared read-only detail shell", () => {
  assert.match(archive, /事件 \/ 发生位置/);
  assert.match(archive, /发现时间 \/ 处置方式/);
  assert.match(archive, /执行对象 \/ 状态/);
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
