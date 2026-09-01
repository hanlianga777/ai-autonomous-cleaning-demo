import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const source = await readFile(resolve(import.meta.dirname, "../src/components/prototype/SpatialDispatchView.tsx"), "utf8");

test("map keeps business fleet detail in hover and has no duplicate navigation status card", () => {
  assert.match(source, /group-hover:block/);
  assert.match(source, /function FleetSummary/);
  assert.match(source, /<FleetSummary robot=\{robot\} translucent \/>/);
  assert.doesNotMatch(source, /Navigation size=\{11\}|selectedRobot && isNavigating && <div className="absolute right/);
});

test("map projection remains driven by persisted backend route and fleet state", () => {
  assert.match(source, /presentation: NavigationPresentation/);
  assert.match(source, /fetch\("\/api\/robots"\)/);
  assert.match(source, /<RouteLayer points=\{routePoints\}/);
});

test("map has one terminal-style dashed route and no obstructing status bubbles", () => {
  assert.match(source, /style\?\.route/);
  assert.match(source, /style\?\.opacity/);
  assert.match(source, /style\?\.stroke_width/);
  assert.match(source, /strokeDasharray=\{style\?\.dasharray \?\? "7 5"\}/);
  assert.doesNotMatch(source, /style\?\.planned|style\?\.completed/);
  assert.doesNotMatch(source, /routeArrowPoints|pointAtRouteDistance/);
  assert.doesNotMatch(source, /定位完成后显示前往现场的路线|等待固定摄像头发现事件/);
});

test("Pudu remains at the dedicated overview standby point without changing delivery state", () => {
  assert.match(source, /robot\.id === "robot-d" && !robot\.active_task_id/);
  assert.match(source, /\{ x: 84, y: 81, label: "园区道路" \}/);
});

test("every map robot has a bound label bubble and indoor cleaners are translucent", () => {
  assert.match(source, /w-\[104px\].*bg-white\/55.*scale-\[0\.92\].*\{robot\.name\}/);
  assert.match(source, /robot\.id === "robot-b" \|\| robot\.id === "robot-c"/);
  assert.match(source, /isIndoor \? "opacity-60" : "opacity-100"/);
});

test("map robot hover reuses the aligned fleet card and opens inward", () => {
  assert.match(source, /grid-cols-\[32px_minmax\(0,1fr\)_auto\]/);
  assert.match(source, /FLEET_LIST_ASSET_OFFSETS/);
  assert.match(source, /tabIndex=\{0\}/);
  assert.match(source, /expandInward/);
});

test("only the workbench fleet list uses the four supplied replacement photos", () => {
  assert.match(source, /workbench-fleet\/\$\{robot\.id\}\.jpg/);
  assert.match(source, /<FleetSummary robot=\{robot\} workbenchList \/>/);
  assert.match(source, /h-7 w-8 shrink-0 items-center justify-center overflow-hidden/);
  assert.match(source, /object-contain \$\{workbenchList \? "mix-blend-multiply" : ""\}/);
  assert.match(source, /\/visual-assets\/robots\/\$\{robot\.id\}\.png/);
});

test("event marker uses the visual route endpoint rather than the business SLAM coordinate", () => {
  assert.match(source, /routePoints\.at\(-1\)/);
  assert.match(source, /overview_position/);
});
