import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const source = await readFile(resolve(import.meta.dirname, "../src/components/prototype/AdvancedView.tsx"), "utf8");

test("Advanced customer shell contains no default technical trace panels", () => {
  assert.match(source, /技术展示辅助页/);
  assert.match(source, /PENDING USER ASSET/);
  assert.doesNotMatch(source, /advancedTraceUrl|RuntimeInfo|TraceGroup|ToolTrace|RealityMatrix|runtimeModeChange/);
});

test("Advanced placeholder has an accessible, minimal enlargement affordance", () => {
  assert.match(source, /onClick=\{\(\) => setExpanded\(0\)\}/);
  assert.match(source, /role="dialog" aria-modal="true" aria-label="技术图片放大预览"/);
  assert.match(source, /approvedAdvancedAssets\.slice\(0, 2\)/);
  assert.match(source, /className="grid grid-cols-1 gap-4" aria-label="技术讲解图片"/);
});
