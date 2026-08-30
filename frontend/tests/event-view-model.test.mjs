import assert from "node:assert/strict";
import { resolve } from "node:path";
import test from "node:test";
import { build } from "esbuild";

const bundle = await build({ entryPoints: [resolve(import.meta.dirname, "../src/components/prototype/eventViewModel.ts")], bundle: true, format: "esm", platform: "node", write: false });
const view = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString("base64")}`);
const asset = (camera, role) => ({ camera_id: camera, role, available: true, url: `/evidence/${camera}-${role}.png`, detection_overlays: [] });
function stored(camera, states) {
  return { event_id: "audit-event", state: states.at(-1), created_at: "2026-08-30 01:00:00", updated_at: "2026-08-30 01:01:00", transitions: states.map((state) => ({ state, created_at: "2026-08-30 01:00:01", detail: { saved: true } })), demo_v1: { mode: "LIVE", asset_manifest: { assets: [asset(camera, "before"), asset(camera, "after")] }, fleet_snapshot: [{ id: "robot-c", battery: 89 }] } };
}

test("history keeps full zero-candidate manual closure timeline and persisted snapshots", () => {
  const states = ["DETECTED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATED", "HUMAN_FALLBACK", "VERIFYING", "CLOSED"];
  const event = view.fromStoredEvent(stored("CAM-A2-11", states));
  assert.deepEqual(view.timelineFor(event, "history").map((t) => t.state), states);
  assert.equal(event.liveResult.fleet_snapshot[0].battery, 89);
  assert.equal(event.scenario.cameraId, "CAM-A2-11");
});
test("verification HUMAN_REVIEW never truncates navigation or assignment", () => {
  const states = ["DETECTED", "CLOUD_REVIEW", "LOCATED", "ASSIGNED", "NAVIGATING", "ARRIVED", "CLEANING_COMPLETED", "VERIFYING", "HUMAN_REVIEW"];
  assert.deepEqual(view.timelineFor(view.fromStoredEvent(stored("CAM-A2-08", states))).map((t) => t.state), states);
});
test("only live can add a pending request row; history is snapshot-only", () => {
  const event = { ...view.fromStoredEvent(stored("CAM-OUT-01", ["DETECTED"])), processing: true, inFlightState: "EDGE_DETECTED" };
  assert.equal(view.timelineFor(event).length, 2);
  assert.equal(view.timelineFor(event, "history").length, 1);
  assert.equal(view.timelineFor(event)[1].timestamp, undefined);
});
test("all four monitor pairs show primary before, idle clean, and after even on failed verification", () => {
  for (const camera of ["CAM-OUT-01", "CAM-A1-01", "CAM-A2-08", "CAM-A2-11"]) {
    const before = view.fromStoredEvent(stored(camera, ["DETECTED", "EDGE_DETECTED"]));
    const pair = view.monitorViews(before);
    assert.equal(pair.length, 2);
    assert.equal(pair.filter((v) => v.eventView).length, 1);
    assert.equal(pair.find((v) => v.eventView).camera.image, `/evidence/${camera}-before.png`);
    assert.equal(pair.find((v) => !v.eventView).after, true);
    assert.equal(pair.some((v) => ["CAM-A1-02", "CAM-A1-04"].includes(v.camera.id)), false);
    const after = view.monitorViews(view.fromStoredEvent(stored(camera, ["VERIFYING", "HUMAN_REVIEW"])));
    assert.equal(after.find((v) => v.eventView).camera.image, `/evidence/${camera}-after.png`);
    assert.equal(after.find((v) => v.eventView).detections, false);
  }
});
test("archive evidence is never replaced by a scenario success asset", () => {
  const event = view.fromStoredEvent({ state: "HUMAN_REVIEW", transitions: [] });
  assert.equal(view.eventCamera(event, "after"), null);
  assert.equal(view.customerTerm("large_object"), "大件物品");
  assert.equal(view.customerTerm("unrecognized_internal_enum"), "未归类 / 待复核");
});
test("timestamps do not append a second timezone to ISO values", () => {
  assert.equal(view.timestampMs("2026-08-30 01:00:00"), view.timestampMs("2026-08-30T01:00:00Z"));
});
test("structured demo history retains its source/camera without inventing real AI or pictures", () => {
  const event = view.fromStoredEvent({ event_id: "p1e-history-example", mode: "DEMO_HISTORY", source: "DEMO_HISTORY", camera_id: "CAM-A1-02", state: "CLOSED", transitions: [{state:"HUMAN_STARTED",detail:{source:"DEMO_HISTORY"}}] });
  assert.equal(event.liveResult.mode, "DEMO_HISTORY");
  assert.equal(event.scenario.cameraId, "CAM-A1-02");
  assert.equal(event.liveResult.qwen_review, undefined);
  assert.equal(view.eventCamera(event), null);
  assert.equal(view.timelineFor(event, "history")[0].label, "人工开始处置");
});
test("Workbench detection boxes use the same persisted controlled edge facts as Advanced", () => {
  const record = stored("CAM-A2-11", ["DETECTED", "EDGE_DETECTED"]);
  record.demo_v1.asset_manifest.assets[0].detection_overlays = [{ label: "大型纸箱", confidence: 0.94, bbox: { x1: .349, y1: .525, x2: .433, y2: .65 } }];
  record.demo_v1.controlled_yolo = [
    { camera_id: "CAM-A2-11", class_name: "大型纸箱", confidence: .82, bbox: { x1: .349, y1: .525, x2: .433, y2: .65 }, source: "CONTROLLED_EDGE_DEMO" },
    { camera_id: "CAM-A2-11", class_name: "大型纸箱", confidence: .82, bbox: { x1: .417, y1: .562, x2: .499, y2: .671 }, source: "CONTROLLED_EDGE_DEMO" },
  ];
  const camera = view.eventCamera(view.fromStoredEvent(record), "before", "CAM-A2-11");
  assert.deepEqual(camera.overlay.map((overlay) => overlay.confidence), [.82, .82]);
  assert.deepEqual(camera.overlay.map((overlay) => overlay.bbox), [[.349, .525, .433, .65], [.417, .562, .499, .671]]);
});
