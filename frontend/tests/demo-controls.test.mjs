import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const source = await readFile(resolve(import.meta.dirname, "../src/components/prototype/CameraMonitorGrid.tsx"), "utf8");

test("event drill menu exposes every story without prescribing a sequence", () => {
  assert.match(source, /const busy = !canStartDemo\(event\)/);
  assert.match(source, /scenarios\.map\(\(scenario, index\) => <button[^>]*disabled=\{busy\}/);
  assert.doesNotMatch(source, /demo01.*demo02.*demo03.*demo04/s);
});
