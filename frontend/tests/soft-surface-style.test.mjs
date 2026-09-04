import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../src");
const [styles, monitor, viewport, detail, analytics, archive, operations] = await Promise.all([
  readFile(resolve(root, "index.css"), "utf8"),
  readFile(resolve(root, "components/prototype/CameraMonitorGrid.tsx"), "utf8"),
  readFile(resolve(root, "components/prototype/CameraViewport.tsx"), "utf8"),
  readFile(resolve(root, "components/prototype/EventDetailPanel.tsx"), "utf8"),
  readFile(resolve(root, "components/prototype/AnalyticsView.tsx"), "utf8"),
  readFile(resolve(root, "components/prototype/EventArchiveView.tsx"), "utf8"),
  readFile(resolve(root, "components/robot-operations/RobotOperationsPanel.tsx"), "utf8"),
]);

test("customer surfaces use shared soft radii while camera planes remain rectangular", () => {
  assert.match(styles, /\.surface-card\s*\{\s*@apply rounded-2xl;/);
  assert.match(styles, /\.surface-inset\s*\{\s*@apply rounded-xl;/);
  assert.match(styles, /\.surface-control\s*\{\s*@apply rounded-xl;/);
  assert.match(monitor, /surface-card/);
  assert.match(detail, /surface-card/);
  assert.match(analytics, /surface-card/);
  assert.match(archive, /surface-card/);
  assert.match(operations, /surface-card/);
  assert.match(viewport, /camera-rectangle/);
  assert.match(styles, /\.camera-rectangle\s*\{\s*@apply rounded-none;/);
});
