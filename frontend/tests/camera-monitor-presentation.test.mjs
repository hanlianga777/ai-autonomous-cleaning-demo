import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const grid = await readFile(resolve(import.meta.dirname, "../src/components/prototype/CameraMonitorGrid.tsx"), "utf8");
const viewport = await readFile(resolve(import.meta.dirname, "../src/components/prototype/CameraViewport.tsx"), "utf8");

test("monitor cards use customer locations and a live runtime clock", () => {
  assert.match(grid, /presentationLabel=\{camera\.location\}/);
  assert.match(grid, /Intl\.DateTimeFormat\("zh-CN"/);
  assert.match(grid, /window\.setInterval\(\(\) => setNow\(new Date\(\)\), 1000\)/);
  assert.match(grid, /<time dateTime=\{now\.toISOString\(\)\}/);
});

test("camera viewport never exposes an internal camera identifier in customer UI", () => {
  assert.match(viewport, /const label = presentationLabel \?\? camera\.location/);
  assert.match(viewport, /alt=\{presentationLabel \?\? camera\.location\}/);
  assert.doesNotMatch(viewport, /放大查看 \$\{camera\.id\}|\$\{camera\.id\} 证据放大|\{camera\.id\} · \{camera\.location\}/);
});

test("camera cards keep only location, time and play controls instead of evidence-stage badges", () => {
  assert.doesNotMatch(grid, /处置前证据|处置后证据|实时画面/);
  assert.doesNotMatch(grid, /absolute right-2 top-2/);
  assert.match(grid, /presentationLabel=\{camera\.location\}/);
});

test("detection overlays keep the reviewed source box visible inside the shared image plane", () => {
  assert.match(viewport, /data-testid="detection-overlay"/);
  assert.match(viewport, /Math\.min\(1, x2 \+ paddingX\)/);
  assert.match(viewport, /Math\.max\(0, x1 - paddingX\)/);
});
