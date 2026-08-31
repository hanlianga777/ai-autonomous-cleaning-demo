import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { resolve } from "node:path";
import test from "node:test";
import { build } from "esbuild";

const entryPoint = resolve(import.meta.dirname, "../src/components/prototype/spatialProjection.ts");
const bundled = await build({
  entryPoints: [entryPoint],
  bundle: true,
  format: "esm",
  platform: "node",
  target: "node20",
  write: false,
  logLevel: "silent",
});
const source = Buffer.from(bundled.outputFiles[0].text).toString("base64");
const projection = await import(`data:text/javascript;base64,${source}`);

function approximately(actual, expected, message) {
  assert.ok(Math.abs(actual - expected) < 0.0001, `${message}: expected ${expected}, got ${actual}`);
}

test("object-contain frame handles horizontal and vertical letterbox", () => {
  const horizontal = projection.calculateContainedFrame(1000, 500, 1600, 900);
  approximately(horizontal.width, 888.8888888889, "horizontal width");
  approximately(horizontal.height, 500, "horizontal height");
  approximately(horizontal.left, 55.5555555556, "horizontal side letterbox");
  approximately(horizontal.top, 0, "horizontal top");

  const vertical = projection.calculateContainedFrame(500, 1000, 1600, 900);
  approximately(vertical.width, 500, "vertical width");
  approximately(vertical.height, 281.25, "vertical height");
  approximately(vertical.left, 0, "vertical left");
  approximately(vertical.top, 359.375, "vertical top letterbox");
});

test("robot and event at the same Phase 2 coordinate share one projection", () => {
  const robot = projection.projectMapCoordinate("A_1F", 50, 30);
  const marker = projection.projectMapCoordinate("A_1F", 50, 30);
  assert.deepEqual(robot, marker);
  assert.deepEqual(robot, projection.CAMPUS_TOPOLOGY_ANCHORS.A_1F);

  const moved = projection.projectMapCoordinate("A_1F", 70, 40);
  assert.notDeepEqual(moved, marker);
  assert.ok(moved.x > marker.x && moved.y > marker.y);
});

test("five canonical analytics zones land in their verified campus white-model areas", () => {
  const zones = [
    ["a1-east-entrance", "A_1F", 43, 25, { minX: 37, maxX: 43, minY: 54, maxY: 61 }],
    ["a1-main-lobby", "A_1F", 29.5, 27, { minX: 27, maxX: 36, minY: 44, maxY: 53 }],
    ["b1-west-lobby", "B_1F", 18, 21, { minX: 62, maxX: 70, minY: 54, maxY: 63 }],
    ["outdoor-east-road", "OUTDOOR", 58, 18, { minX: 82, maxX: 92, minY: 72, maxY: 81 }],
    ["a2-corridor", "A_2F", 16, 18, { minX: 25, maxX: 34, minY: 26, maxY: 35 }],
  ];
  for (const [zone_id, map_id, x, y, bounds] of zones) {
    const projected = projection.projectAnalyticsHeatmapPoint({ zone_id, map_id, x, y });
    assert.ok(projected.x >= bounds.minX && projected.x <= bounds.maxX, `${zone_id} x is inside its visual area`);
    assert.ok(projected.y >= bounds.minY && projected.y <= bounds.maxY, `${zone_id} y is inside its visual area`);
  }
});

test("backend route includes persisted Fleet start, Dijkstra nodes and SLAM target continuously", () => {
  const fleet = { id: "robot-c", map_id: "B_1F", coordinates: { x: 24, y: 26 } };
  const target = { map_id: "A_2F", x: 20, y: 23 };
  const plan = {
    node_path: ["B_1F", "B_ELEVATOR_1F", "B_ELEVATOR_2F", "B_2F", "SKYBRIDGE_B", "SKYBRIDGE_A", "A_2F"],
    segments: [{ type: "local" }, { from: "B_ELEVATOR_1F", to: "B_ELEVATOR_2F", type: "elevator" }, { type: "local" }, { type: "skybridge" }, { type: "local" }],
  };
  const route = projection.projectBackendRoute(plan, fleet, target);
  assert.deepEqual(route[0], projection.projectMapCoordinate("B_1F", 24, 26));
  assert.equal(route[2].nodeId, "B_ELEVATOR_1F");
  assert.equal(route.at(-2).nodeId, "A_2F");
  assert.deepEqual(route.at(-1), projection.projectMapCoordinate("A_2F", 20, 23));
  assert.ok(projection.routeLength(route) > 0);
});

test("route projection rejects a missing or unknown backend topology rather than inventing a direct line", () => {
  const fleet = { id: "robot-a", map_id: "A_1F", coordinates: { x: 22, y: 18 } };
  const target = { map_id: "A_1F", x: 66, y: 40 };
  assert.deepEqual(projection.projectBackendRoute(undefined, fleet, target), []);
  assert.deepEqual(projection.projectBackendRoute({ node_path: ["A_1F", "UNKNOWN_NODE"] }, fleet, target), []);
});

test("route motion resumes from elapsed time, ends exactly at target and keeps elevator pause for one second", () => {
  const points = [
    { x: 10, y: 50 },
    { x: 25, y: 50, nodeId: "B_1F" },
    { x: 40, y: 45, nodeId: "B_ELEVATOR_1F" },
    { x: 40, y: 25, nodeId: "B_ELEVATOR_2F" },
    { x: 70, y: 25, nodeId: "A_2F" },
  ];
  const plan = projection.buildMotionPlan(points, [
    { type: "local" },
    { from: "B_ELEVATOR_1F", to: "B_ELEVATOR_2F", type: "elevator" },
    { type: "local" },
  ]);
  assert.equal(plan.elevatorPause.durationMs, 1000);
  const beforePauseMs = plan.travelDurationMs * (plan.elevatorPause.atDistance / plan.totalDistance);
  const holding = projection.sampleRouteMotion(plan, beforePauseMs + 500);
  assert.equal(holding.isElevatorPause, true);
  approximately(holding.travelledDistance, plan.elevatorPause.atDistance, "pause distance");
  assert.deepEqual(holding.position, points[2], "elevator pause stays at the entry node");
  const afterPause = projection.sampleRouteMotion(plan, beforePauseMs + 1000);
  assert.equal(afterPause.isElevatorPause, false);

  // The hook uses Date.now() - persisted NAVIGATING transition time. Calling
  // this fresh after an Event Center unmount must therefore resume, not reset.
  const resumed = projection.sampleRouteMotion(plan, Math.min(plan.totalDurationMs - 1, beforePauseMs + 1400));
  assert.ok(resumed.travelledDistance >= holding.travelledDistance);
  const terminal = projection.sampleRouteMotion(plan, plan.totalDurationMs);
  assert.equal(terminal.complete, true);
  assert.deepEqual(terminal.position, points.at(-1));
});

test("traversed SVG path retains every completed corner and the current partial segment", () => {
  const points = [
    { x: 10, y: 50 },
    { x: 25, y: 50 },
    { x: 40, y: 45 },
    { x: 40, y: 25 },
  ];
  const elapsedDistance = projection.distanceBetween(points[0], points[1])
    + projection.distanceBetween(points[1], points[2])
    + 5;
  const path = projection.svgPath(points, elapsedDistance);
  assert.match(path, /^M10\.00,50\.00 L25\.00,50\.00 L40\.00,45\.00 L40\.00,40\.00$/);
});

test("missing route is safe: no position, no animation and completed state", () => {
  assert.deepEqual(projection.projectBackendRoute(undefined, undefined, undefined), []);
  const plan = projection.buildMotionPlan([], []);
  const sample = projection.sampleRouteMotion(plan, 2500);
  assert.equal(sample.position, null);
  assert.equal(sample.complete, true);
  assert.equal(sample.isElevatorPause, false);
});

test("persisted navigation pause freezes across refresh and resume excludes every paused interval", () => {
  const start = Date.parse("2026-08-30T01:00:00Z");
  const plan = projection.buildMotionPlan([{ x: 10, y: 10 }, { x: 90, y: 80 }]);
  const pausedAt = start + 2000;
  const pausedElapsed = projection.navigationElapsedMs(start, start + 5000, true, pausedAt, 0);
  const restoredElapsed = projection.navigationElapsedMs(start, start + 12000, true, pausedAt, 0);
  assert.equal(pausedElapsed, 2000);
  assert.equal(restoredElapsed, pausedElapsed);
  assert.deepEqual(projection.sampleRouteMotion(plan, pausedElapsed), projection.sampleRouteMotion(plan, restoredElapsed));
  const resumedElapsed = projection.navigationElapsedMs(start, start + 12000, false, NaN, 10000);
  assert.equal(resumedElapsed, pausedElapsed);
  assert.equal(projection.navigationElapsedMs(start, start + 13000, false, NaN, 10000), 3000);
  assert.equal(projection.navigationElapsedMs(start, start + 16000, true, start + 14000, 10000), 4000);
  assert.equal(projection.navigationElapsedMs(start, start + 17000, false, NaN, 13000), 4000);
  assert.equal(projection.navigationElapsedMs(start, start + 17000, true, NaN, 0), 0, "missing pause clock fails stationary");
});
