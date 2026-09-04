import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const presentation = await readFile(resolve(import.meta.dirname, "../src/components/prototype/navigationPresentation.ts"), "utf8");
const workbench = await readFile(resolve(import.meta.dirname, "../src/components/prototype/PrototypeWorkbench.tsx"), "utf8");
const detail = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventDetailPanel.tsx"), "utf8");
const evidence = await readFile(resolve(import.meta.dirname, "../src/components/prototype/EventStageEvidence.tsx"), "utf8");

test("one rAF presentation drives the map and live event location copy", () => {
  assert.equal((presentation.match(/useRoutePlayback\(/g) ?? []).length, 1);
  assert.match(presentation, /visual_route_preview/);
  assert.match(presentation, /routeWaypointAtDistance/);
  assert.match(workbench, /useNavigationPresentation\(spatialEvent\)/);
  assert.match(workbench, /presentation=\{navigationPresentation\}/);
  assert.match(workbench, /navigationPresentation=\{navigationPresentation\}/);
  assert.match(detail, /navigationPresentation\?\.progressLabel/);
  assert.match(evidence, /实时行驶位置/);
  assert.match(evidence, /aria-live="polite"/);
});

test("Demo3 patrol evidence shares the navigation presentation clock", () => {
  assert.match(presentation, /patrolObservation/);
  assert.match(presentation, /isPatrolObservationVisible/);
  assert.match(presentation, /trigger_node_id/);
  assert.match(evidence, /沿途巡检提示/);
  assert.match(evidence, /observation\.finding/);
  assert.match(evidence, /CONTROLLED_RGBD_DEMO/);
});
