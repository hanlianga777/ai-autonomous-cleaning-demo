import assert from "node:assert/strict";
import { resolve } from "node:path";
import test from "node:test";
import { build } from "esbuild";
const bundle = await build({ entryPoints: [resolve(import.meta.dirname, "../src/components/prototype/runtimeSession.ts")], bundle: true, format: "esm", platform: "node", write: false });
const session = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString("base64")}`);
const stored = (state) => ({ event_id: "saved-id", state, transitions: [{ state, created_at: "2026-08-30 01:00:00" }], demo_v1: { fleet_snapshot: [{ id: "robot-c", map_id: "A_2F", coordinates: { x: 34, y: 29 }, battery: 89 }], navigation_plan: { node_path: ["B_1F", "B_2F", "A_2F"] } } });

test("NAVIGATING restoration loads only the server snapshot with GET", async () => {
  const calls = [];
  const event = await session.loadEventSnapshot("saved-id", undefined, async (url, options) => { calls.push({ url, options }); return { ok: true, json: async () => stored("NAVIGATING") }; });
  assert.equal(event.backendState, "NAVIGATING");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/api/events/saved-id");
  assert.equal(calls[0].options.method, undefined);
  assert.deepEqual(event.liveResult.navigation_plan.node_path, ["B_1F", "B_2F", "A_2F"]);
});
test("same-session in-flight stage guard survives reload and never reclaims the model call", () => {
  const keys = session.readRequestKeys(null);
  assert.equal(session.claimStage(keys, "saved-id", "cloud-review"), true);
  const reloaded = session.readRequestKeys(JSON.stringify([...keys]));
  assert.equal(session.claimStage(reloaded, "saved-id", "cloud-review"), false);
  assert.equal(session.claimStage(reloaded, "new-id", "cloud-review"), true);
});
test("GET 404 safely rejects restoration without fabricating a successful event or route", async () => {
  let parsed = false;
  await assert.rejects(session.loadEventSnapshot("missing", undefined, async () => ({ ok: false, json: async () => { parsed = true; return stored("CLOSED"); } })), /无法恢复/);
  assert.equal(parsed, false);
});
test("terminal restoration retains exact persisted fleet and route and rejects stale or foreign snapshots", async () => {
  const record = stored("CLOSED");
  const event = await session.loadEventSnapshot("saved-id", undefined, async () => ({ ok: true, json: async () => record }));
  assert.deepEqual(event.liveResult.fleet_snapshot, record.demo_v1.fleet_snapshot);
  assert.deepEqual(event.liveResult.navigation_plan, record.demo_v1.navigation_plan);
  assert.equal(session.canApplySnapshot(event, { event_id: "saved-id", transitions: [] }), false);
  assert.equal(session.canApplySnapshot(event, { ...record, event_id: "another-event" }), false);
  assert.equal(session.canApplySnapshot(event, record), true);
});

test("cancelled cleaning restores as terminal and releases subsequent demo controls", async () => {
  const event = await session.loadEventSnapshot("saved-id", undefined, async () => ({ ok: true, json: async () => stored("CANCELLED") }));
  assert.equal(event.backendState, "CANCELLED");
  assert.equal(event.scenario.steps.at(-1), "CANCELLED");
  assert.equal(session.isTerminalEvent(event), true);
  assert.equal(session.canStartDemo(event), true);
  assert.equal(session.canAutoAdvance(event), false);
  assert.equal(session.canStartDemo({ ...event, processing: true }), false);
  assert.equal(session.canStartDemo({ ...event, backendState: "NAVIGATING" }), false);
});

test("Operations-owned cleaning never claims workbench stages, including after pause and resume", () => {
  for (const state of ["DETECTED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATED", "ASSIGNED", "NAVIGATING", "ARRIVED", "CLEANING_COMPLETED"]) {
    const regular = { backendState: state, liveResult: { event_id: "saved-id" } };
    assert.equal(session.canAutoAdvance(regular), true, state);
    const owned = { ...regular, liveResult: { ...regular.liveResult, operations_task_id: "task-owned" } };
    assert.equal(session.canAutoAdvance(owned), false, state);
    assert.equal(session.canAutoAdvance({ ...owned, liveResult: { ...owned.liveResult, operations_control: "PAUSED" } }), false);
    assert.equal(session.canAutoAdvance({ ...owned, liveResult: { ...owned.liveResult, operations_control: null } }), false);
  }
  assert.equal(session.canAutoAdvance({ backendState: "NAVIGATING", liveResult: { operations_control: "PAUSED" } }), false);
});
