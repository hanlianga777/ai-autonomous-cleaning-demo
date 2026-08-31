import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { resolve } from "node:path";
import test from "node:test";
import { build } from "esbuild";

const entryPoint = resolve(import.meta.dirname, "../src/components/robot-operations/robotOperationsModel.ts");
const bundled = await build({ entryPoints: [entryPoint], bundle: true, format: "esm", platform: "node", target: "node20", write: false, logLevel: "silent" });
const source = Buffer.from(bundled.outputFiles[0].text).toString("base64");
const model = await import(`data:text/javascript;base64,${source}`);

test("floating Agent defaults to bottom-left and persisted positions stay in viewport", () => {
  const viewport = { width: 1000, height: 700 };
  const start = model.defaultFloatingPosition(viewport);
  assert.equal(start.x, 16);
  assert.ok(start.y >= 16 && start.y <= 628);
  assert.deepEqual(model.clampFloatingPosition({ x: 9999, y: -50 }, viewport), { x: 928, y: 16 });
  assert.deepEqual(model.parseStoredPosition(JSON.stringify({ x: 900, y: 650 }), viewport), { x: 900, y: 628 });
  assert.deepEqual(model.clampFloatingPosition({ x: Number.NaN, y: Number.POSITIVE_INFINITY }, { width: 100, height: 120 }), { x: 16, y: 16 });
  assert.equal(model.parseStoredPosition('{"x":1e999,"y":3}', viewport), null);
  assert.equal(model.parseStoredPosition("not-json", viewport), null);
  assert.equal(model.FLOATING_EXPANDED_KEY, "cleanops.robot-operations.expanded.v2");
});

test("customer task action cards expose only pause, resume, cancel and explicit human completion", () => {
  const created = { task_id: "task-1", kind: "cleaning", status: "CREATED", source: "POC_SIMULATION" };
  assert.deepEqual(model.taskActions(created), ["cancel"]);
  assert.deepEqual(model.taskActions({ ...created, status: "PAUSED" }), ["resume", "cancel"]);
  assert.deepEqual(model.taskActions({ ...created, status: "ASSIGNED" }), ["pause", "cancel"]);
  assert.deepEqual(model.taskActions({ ...created, status: "CLOUD_REVIEW" }), ["pause", "cancel"]);
  assert.deepEqual(model.taskActions({ ...created, kind: "delivery", status: "PICKED_UP" }), ["pause", "cancel"]);
  assert.deepEqual(model.taskActions({ ...created, kind: "relocation", status: "NAVIGATING" }), ["pause", "cancel"]);
  assert.deepEqual(model.taskActions({ ...created, status: "HUMAN_FALLBACK" }), ["manual_complete"]);
  assert.deepEqual(model.taskActions({ ...created, kind: "delivery", status: "HUMAN_FALLBACK" }), []);
  assert.deepEqual(model.taskActions({ ...created, status: "CLOSED" }), []);
  assert.equal(model.taskActions({ ...created, status: "ASSIGNED" }).includes("advance"), false);
  assert.equal(model.actionLabel("manual_complete"), "确认人工处置完成");
});

test("newest-first task records keep the newest three visible", () => {
  const tasks = ["task-4", "task-3", "task-2", "task-1"].map((task_id) => ({ task_id, kind: "cleaning", status: "CREATED", source: "POC_SIMULATION" }));
  assert.deepEqual(model.recentTasks(tasks).map((task) => task.task_id), ["task-4", "task-3", "task-2"]);
});

test("customer task labels do not fabricate external or telemetry state", () => {
  assert.equal(model.taskKindLabel("relocation"), "待命调度");
  assert.equal(model.taskStatusLabel("ASSIGNED"), "已分配");
  assert.equal(model.taskStatusLabel("UNSEEN_BACKEND_STATE"), "状态待确认");
  assert.equal(model.taskExecutorLabel({ task_id: "human-1", kind: "cleaning", status: "HUMAN_FALLBACK", source: "POC_SIMULATION", robot_id: null }), "处置方式：人工搬运");
  assert.equal(model.taskExecutorLabel({ task_id: "pending-1", kind: "cleaning", status: "CREATED", source: "POC_SIMULATION", robot_id: null }), "执行对象：待调度");
  assert.equal(model.taskExecutorLabel({ task_id: "robot-1", kind: "cleaning", status: "ASSIGNED", source: "POC_SIMULATION", robot_id: "robot-b" }), "机器人：高仙 Omnie");
  assert.equal(model.taskLocationLabel("East Corridor"), "东侧走廊");
});

test("customer chat redacts internal identifiers and runtime enums", () => {
  const copy = model.customerAgentMessage("robot-b 正在处理 integrated-demo02-a1b2；POI 为 a2-corridor，状态 HUMAN_FALLBACK，zone_id=a2-corridor");
  assert.match(copy, /高仙 Omnie/);
  assert.doesNotMatch(copy, /integrated-demo|a2-corridor|HUMAN_FALLBACK|zone_id/i);
});

test("customer chat projects task jargon into business language", () => {
  const copy = model.customerAgentMessage("Task ID: task-3\n类型: delivery (POC SIMULATION)\n状态: CREATED\nPOI: outdoor-standby");
  assert.match(copy, /本次任务/);
  assert.match(copy, /配送任务/);
  assert.match(copy, /已创建/);
  assert.match(copy, /园区室外道路待命点/);
  assert.doesNotMatch(copy, /Task ID|delivery|POC|CREATED|outdoor-standby|POI/i);
});

test("customer presentation consistently uses formal robot, state and location labels", () => {
  assert.equal(model.taskRobotLabel("robot-c"), "蜗小白 SC50");
  assert.equal(model.taskRobotLabel("unknown-robot"), "未分配机器人");
  assert.equal(model.taskStatusLabel("NAVIGATING"), "机器人前往现场");
  assert.equal(model.taskStatusLabel("unrecognized"), "状态待确认");
  assert.equal(model.taskLocationLabel("Main Lobby"), "主大堂");
  assert.match(model.customerAgentMessage("Robot B 正在处理"), /高仙 Omnie/);
});

test("advice data window is rendered as a factual label, not an object", () => {
  assert.equal(model.adviceWindowLabel({ start: "2026-08-01", end: "2026-08-30", days: 30 }), "2026-08-01 至 2026-08-30 · 30 天");
});

test("task mutations are scoped to the shared Operations session", () => {
  assert.deepEqual(model.operationSessionHeaders("ops-session-7"), { "X-Operations-Session": "ops-session-7" });
});

test("archive Agent context cannot inherit an unrelated Workbench event", () => {
  const workbench = { selected_event_id: "workbench-event", event_state: "NAVIGATING", runtime_mode: "live" };
  const archive = model.archivePageContext("archive-event", { event_id: "archive-event", state: "CLOSED", model_records: "x".repeat(20000) }, { category: "all", map_id: "A_1F" });
  assert.equal(archive.page, "events");
  assert.equal(archive.selected_event_id, "archive-event");
  assert.deepEqual(archive.selected_history_snapshot, { event_id: "archive-event", state: "CLOSED" });
  assert.deepEqual(archive.archive_filters, { category: "all", map_id: "A_1F" });
  assert.equal("event_state" in archive, false);
  assert.equal("runtime_mode" in archive, false);
  assert.notEqual(archive.selected_event_id, workbench.selected_event_id);
});
