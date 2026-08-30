import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { resolve } from "node:path";
import test from "node:test";
import { build } from "esbuild";

const entryPoint = resolve(import.meta.dirname, "../src/components/prototype/advancedTraceModel.ts");
const bundled = await build({ entryPoints: [entryPoint], bundle: true, format: "esm", platform: "node", target: "node20", write: false, logLevel: "silent" });
const source = Buffer.from(bundled.outputFiles[0].text).toString("base64");
const model = await import(`data:text/javascript;base64,${source}`);

const nodes = [
  { id: "edge", group: "AI", label: "Edge Detection", status: "COMPLETED", source: "CONTROLLED EVIDENCE" },
  { id: "slam", group: "SPATIAL", label: "Camera→SLAM", status: "COMPLETED", source: "DETERMINISTIC RUNTIME" },
];

test("Advanced trace URL only reads selected event and stale response identity is rejected", () => {
  assert.equal(model.advancedTraceUrl("event/a?"), "/api/advanced/trace?event_id=event%2Fa%3F");
  assert.equal(model.advancedTraceUrl(null), "/api/advanced/trace");
  assert.equal(model.acceptsTraceResponse(3, 3), true);
  assert.equal(model.acceptsTraceResponse(2, 3), false);
});

test("node detail follows selected identity and never falls back to a different trace node", () => {
  assert.equal(model.nextSelectedNode(nodes, null), "edge");
  assert.equal(model.nextSelectedNode(nodes, "slam"), "slam");
  assert.equal(model.nextSelectedNode(nodes, "stale"), "edge");
  assert.equal(model.selectedTraceNode(nodes, "slam").label, "Camera→SLAM");
  assert.equal(model.selectedTraceNode(nodes, "missing"), null);
});

test("source badges and structured summaries preserve reality while excluding secrets and reasoning", () => {
  assert.equal(model.sourceBadgeLabel("LIVE MODEL"), "LIVE MODEL");
  assert.equal(model.sourceBadgeLabel(null), "SOURCE NOT RECORDED");
  assert.match(model.sourceBadgeClass("CONTROLLED EDGE DEMO"), /orange/);
  assert.equal(model.traceStatusLabel("NOT_TRIGGERED"), "未触发");
  assert.equal(model.traceIdentityLabel(null, "LEGACY_MISSING"), "历史记录未记录 Trace ID");
  assert.equal(model.traceIdentityLabel(null, "NO_EVENT"), "暂无事件");
  assert.equal(model.traceIdentityLabel("trace-new", "RECORDED"), "trace-new");
  const entries = model.safeSummaryEntries({ confidence: 0.87, api_key: "never-show", reasoning: "never-show", nested: { token: "never-show", camera_id: "CAM-A1-01" } });
  assert.deepEqual(entries, [["confidence", "0.87"], ["nested", "camera_id: CAM-A1-01"]]);
  assert.equal(model.safeTraceText("authorization: Bearer hidden"), "[敏感字段已隐藏]");
  assert.equal(model.safeEvidenceUrl("/asset.png?token=hidden"), null);
  assert.equal(model.safeEvidenceUrl("/asset.png"), "/asset.png");
});
