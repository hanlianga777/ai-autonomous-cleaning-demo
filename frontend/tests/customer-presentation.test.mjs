import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../src/components");
const workbench = await readFile(resolve(root, "prototype/PrototypeWorkbench.tsx"), "utf8");
const operations = await readFile(resolve(root, "robot-operations/RobotOperationsPanel.tsx"), "utf8");
const model = await readFile(resolve(root, "robot-operations/robotOperationsModel.ts"), "utf8");

test("customer workbench has no header stage badge or internal task controls", () => {
  assert.doesNotMatch(workbench, /CircleDot|stageCopy\[state\]/);
  assert.doesNotMatch(operations, /action !== "advance"/);
  assert.doesNotMatch(model, /taskActions\(task\).*advance/s);
});
