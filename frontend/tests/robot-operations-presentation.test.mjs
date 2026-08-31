import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../src/components/robot-operations");
const [provider, panel] = await Promise.all([
  readFile(resolve(root, "RobotOperationsProvider.tsx"), "utf8"),
  readFile(resolve(root, "RobotOperationsPanel.tsx"), "utf8"),
]);

test("chat immediately renders the submitted user message while the server response is pending", () => {
  assert.match(provider, /const optimisticId = `local-/);
  assert.match(provider, /delivery: "sending"/);
  assert.match(provider, /delivery: "failed"/);
  assert.match(panel, /LoaderCircle size=\{14\} className="animate-spin"/);
  assert.match(panel, /正在发送并等待运营助手响应/);
});

test("customer chat removes the user label and hides the task card from the conversation", () => {
  assert.doesNotMatch(panel, /message.role === "user" ? "你"/);
  assert.match(panel, /message.role === "user"/);
  assert.match(panel, /<StructuredAssistantMessage content=\{message\.content\} \/>/);
  assert.doesNotMatch(panel, /当前任务|TaskCard|recentTasks/);
  assert.match(panel, /event.key === "Enter"/);
  assert.match(panel, /aria-label="发送"/);
});

test("the empty chat gives demo-specific recommendations and formats assistant replies", () => {
  assert.match(panel, /当前有哪些事件需要优先处理？/);
  assert.match(panel, /过去 30 天哪些区域问题较多？/);
  assert.match(panel, /三台清洁机器人现在是什么状态？/);
  assert.match(panel, /A栋1F液体污渍如何改善？/);
  assert.match(panel, /aria-label="运营助手推荐问题"/);
  assert.match(panel, /grid-cols-\[74px_minmax\(0,1fr\)\]/);
  assert.match(panel, /function conciseCustomerReply/);
  assert.match(panel, /sentences\.slice\(0, 3\)/);
});

test("advice cards use two concise, complete customer-facing lines", () => {
  assert.match(panel, /A栋1F东入口常见液体污渍。/);
  assert.match(panel, /大件事件常超过24小时未闭环。/);
  assert.match(panel, /园区东侧道路常见识别不清事件。/);
  assert.doesNotMatch(panel, /line-clamp-2/);
});
