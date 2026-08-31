import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const archive = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventArchiveView.tsx"), "utf8");
const detail = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventStageEvidence.tsx"), "utf8");
const chat = await readFile(resolve(import.meta.dirname, "../src/components/robot-operations/robotOperationsModel.ts"), "utf8");

test("a durable HUMAN_REVIEW outcome has one customer projection across workbench, archive and Chat", () => {
  assert.match(detail, /case "HUMAN_REVIEW"/);
  assert.match(detail, /自动流程停止，转人工复核/);
  assert.match(archive, /<EventDetailPanel event=\{detail\} mode="history"/);
  assert.match(chat, /HUMAN_REVIEW/);
  assert.match(chat, /taskStatusLabel/);
});
