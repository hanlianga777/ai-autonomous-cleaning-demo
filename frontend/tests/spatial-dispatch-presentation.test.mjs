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
  assert.match(source, /projectBackendRoute\(plan, origin, target\)/);
  assert.match(source, /fetch\("\/api\/robots"\)/);
  assert.match(source, /<RouteLayer points=\{routePoints\}/);
});

test("map has a high-contrast route and no obstructing status bubbles", () => {
  assert.match(source, /stroke="#1f5f8b"/);
  assert.match(source, /strokeWidth="3"/);
  assert.match(source, /strokeWidth="5"/);
  assert.doesNotMatch(source, /定位完成后显示前往现场的路线|等待固定摄像头发现事件/);
});

test("Pudu remains at the dedicated overview standby point without changing delivery state", () => {
  assert.match(source, /robot\.id === "robot-d" && !robot\.active_task_id/);
  assert.match(source, /\{ x: 84, y: 81, label: "园区道路" \}/);
});
