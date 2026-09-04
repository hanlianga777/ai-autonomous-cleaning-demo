import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../src/components/robot-operations");
const [provider, panel, model] = await Promise.all([
  readFile(resolve(root, "RobotOperationsProvider.tsx"), "utf8"),
  readFile(resolve(root, "RobotOperationsPanel.tsx"), "utf8"),
  readFile(resolve(root, "robotOperationsModel.ts"), "utf8"),
]);

test("latest live assistant reply shows a client-measured duration and types in", () => {
  assert.match(model, /response_duration_ms\?: number/);
  assert.match(provider, /const requestStartedAt = Date\.now\(\)/);
  assert.match(provider, /responseDurations\.current/);
  assert.match(panel, /function useTypewriter/);
  assert.match(panel, /window\.setInterval/);
  assert.match(panel, /回答用时/);
  assert.match(panel, /latestAssistantId/);
  assert.match(panel, /animate=\{message\.id === latestAssistantId\}/);
});

test("assistant copy remains concise and labelled", () => {
  assert.match(panel, /const labels = \["结论", "建议", "提示"\]/);
  assert.match(panel, /sentences\.slice\(0, 3\)/);
});
