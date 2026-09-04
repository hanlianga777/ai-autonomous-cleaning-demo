import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const source = await readFile(resolve(import.meta.dirname, "../src/components/prototype/AnalyticsView.tsx"), "utf8");

test("Analytics reserves a customer-readable fixed chat column", () => {
  assert.match(source, /xl:grid-cols-\[minmax\(0,1fr\)_360px\]/);
  assert.match(source, /<AnalyticsAgentChat pageContext=\{analyticsAgentContext\}/);
  assert.doesNotMatch(source, /286px/);
});

test("Analytics keeps advice in the left story and caps it at three cards", async () => {
  const panel = await readFile(resolve(import.meta.dirname, "../src/components/robot-operations/RobotOperationsPanel.tsx"), "utf8");
  assert.match(source, /<AnalyticsAdviceCards \/>.*<section className="mt-4 border/s);
  assert.match(panel, /const items = advice\?\.items\.slice\(0, 3\)/);
  assert.match(panel, /const \{ advice, adviceError, adviceLoading, loadAdvice \} = useRobotOperations\(\)/);
});

test("Analytics presents fixed predictive prepositioning before the AI advice cards", () => {
  assert.match(source, /AI 预测与预部署/);
  assert.match(source, /固定演示预案/);
  assert.match(source, /输入信号/);
  assert.match(source, /风险预判/);
  assert.match(source, /建议待命/);
  assert.match(source, /<PredictiveDeployment[\s\S]*?<AnalyticsAdviceCards/);
});
