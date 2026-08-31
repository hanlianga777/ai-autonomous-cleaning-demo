import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const source = await readFile(resolve(import.meta.dirname, "../src/components/prototype/SpatialDispatchView.tsx"), "utf8");

test("map keeps business fleet detail in hover and has no duplicate navigation status card", () => {
  assert.match(source, /group-hover:block/);
  assert.match(source, /服务范围：/);
  assert.match(source, /适用范围：/);
  assert.doesNotMatch(source, /Navigation size=\{11\}|selectedRobot && isNavigating && <div className="absolute right/);
});

test("map projection remains driven by persisted backend route and fleet state", () => {
  assert.match(source, /presentation: NavigationPresentation/);
  assert.match(source, /fetch\("\/api\/robots"\)/);
  assert.match(source, /<RouteLayer points=\{routePoints\}/);
});

test("map has a high-contrast route and no obstructing status bubbles", () => {
  assert.match(source, /style\?\.planned/);
  assert.match(source, /style\?\.completed/);
  assert.match(source, /strokeWidth="3"/);
  assert.match(source, /strokeWidth="5"/);
  assert.match(source, /strokeDasharray="7 5"/);
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

test("event marker uses the visual route endpoint rather than the business SLAM coordinate", () => {
  assert.match(source, /routePoints\.at\(-1\)/);
  assert.match(source, /overview_position/);
});
