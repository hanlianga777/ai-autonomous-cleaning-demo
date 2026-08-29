# Integrated Demo｜AI 集成测试事实记录

> **状态：PARTIAL · 2026-08-29**
> 本文件严格区分历史结果、当前实现与待重测项；不将旧测试结果扩写为当前逻辑验收。

## 1. 当前实现（Current Implementation）

- 云端调用通过 `perception.qwen._request_qwen`，本地环境变量提供 Key；Key 不记录在本文件。
- 边缘框是 `CONTROLLED_EDGE_DEMO`，固定值而非真实 YOLO 权重输出。
- 首次云端语义调用：`run_event_qwen_vl`。
- `.50–.85` 首轮置信度：调用 `run_targeted_event_qwen_vl` 进行**独立**二次复核；其 Prompt 不传入首轮模型回答。
- `Evidence Fusion Composite Disposal Score` 按 `0.60 raw cloud + 0.20 category + 0.12 camera/location/time mapping + 0.08 multi-view` 计算。veto（`need_clean=false`、`unknown`、`ignore`）仍转人工。
- 仅 TaskProfile 进入既有 Capability Engine + Scheduler；云端模型不选择 Robot A/B/C。
- Demo04 人工完成 endpoint 以清洁前/后同机位图调用 `run_verification_qwen_vl`。

### 当前已知实现缺口

1. 首轮多图 Prompt 没有明确说明 Demo02 三图为同地点、同时间段、同一地面区域、三台固定摄像头；二次 Prompt 已明确，但不能替代首轮。
2. API 在请求中完成整次组合计算，前端随后以定时器展示阶段；这不是逐阶段 E2E 执行。
3. 当前无真实 YOLO 权重通过验收；不要把 controlled bbox 写成 REAL YOLO。

## 2. 历史结果（Historical Result / Previous Test）

**日期：2026-08-28。** 下列结果来自旧“单次云端置信度 + `next_action=dispatch_robot`”门控，早于当前独立复核/融合逻辑，不能作为当前验收：

| Case | 图数 | 云端结论 | 原始置信度 | 当时状态 |
|---|---:|---|---:|---|
| Demo01 | 1 | small_litter / need_clean=true | .81 | HUMAN_REVIEW |
| Demo02（三次） | 3 | liquid / need_clean=true | .61 | HUMAN_REVIEW |
| Demo03 | 1 | can / need_clean=true | .84 | HUMAN_REVIEW |
| Demo04 | 1 | large_object / need_clean=false | .95 | HUMAN_REVIEW |

当时单元测试为 4/4，覆盖三图限制、Robot B 的可调度分支、Demo04 人工边界和云端不可用。它们仍可作为历史回归参考，但不能证明当前门控或完整 LIVE E2E。

## 3. 当前代码后的真实运行记录（Not a full regression）

**日期：2026-08-29，本地开发机。** 这些是实现后运行的单次观察，模型输出可能波动；未构成四场景统一正式验收。

| Case | 观察结果 | 状态解释 |
|---|---|---|
| Demo01 | 云端 `need_clean=true`、原始 .92、融合 .872；Robot A | CLOSED |
| Demo02 | 首轮 .61；独立复核 .95；融合 .97；Robot B | CLOSED；独立复核调用 1 次 |
| Demo03 | Robot C 被选择；该次验收未满足门控 | HUMAN_REVIEW |
| Demo04 | 首轮 `need_clean=false` / large_object / .92 | 正确进入人工；随后人工完成后云端验收 .98、CLOSED |
| 云端不可用模拟 | 写入 HUMAN_REVIEW、无机器人任务 | 通过 API 观察 |

这些记录证明部分真实调用和人工闭环路径曾运行；**不能**证明真实逐阶段状态、真实 YOLO、真实拓扑投影、浏览器四场景 E2E 或生产稳定性。

## 4. 本轮已执行的非模型检查

- `npm run build`：通过。
- `GET /api/health`：通过。
- `GET /api/dashboard`：通过。
- 浏览器：四个一级页面和演示菜单可打开；本次基础检查未发现 Console error。
- SQLite：模拟不可用和真实 demo run 均可在 `/api/events` 查询，Analytics 总事件数随运行增加。

## 5. 当前待重测（Pending Real Re-test）

- [ ] 修改首轮 Demo02 Prompt 后，重跑 Demo02，保存首轮、独立复核、融合分、延迟、选中摄像头与最终状态。
- [ ] 真实逐阶段执行实现后，重跑 Demo01–04，验证前一阶段完成前后一阶段不可执行。
- [ ] assignment_decision 驱动地图后，验证 A/B/C 真实选择与运动投影；重点验证 Robot C 拓扑路径。
- [ ] Demo04：人工工单 → after 图 → 真实云端验收 → CLOSED 的浏览器端端到端回归。
- [ ] 云端超时、无 Key、无效 JSON、模型 veto、验收失败的可见错误与不派单回归。
- [ ] 五个只读 AI Assistant 问答及禁止创建任务/改阈值测试（当前未实现后端）。

## 6. 禁止性结论

- 不得声称本地 Custom YOLO、完整 REAL MODE、真实多机位帧同步、真实机器人遥测或生产阈值已验收。
- 不得把稳定回放、固定前端建议或旧 Mock Verification 写成真实云端结果。
- 任何新测试必须注明日期、代码版本、模式、调用次数与是否真实云端；失败/未测不可省略。
