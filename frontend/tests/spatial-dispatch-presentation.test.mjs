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
