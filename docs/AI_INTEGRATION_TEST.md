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

### 当前已知限制

1. 当前无真实 YOLO 权重通过验收；不要把 controlled bbox 写成 REAL YOLO。
2. Demo03 本轮真实云端验收返回 `retry`，因此正确停在 `HUMAN_REVIEW`；不能声称四个场景均已自动闭环。
3. P0 已完成技术与浏览器回归，但仍等待用户最终验收，不能自行进入 P1。

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

- [x] 修改首轮 Demo02 Prompt 后，重跑 Demo02 三次，保存首轮、独立复核、融合分、延迟、选中摄像头与最终状态。
- [x] 阶段化执行已重跑 Demo01–04；阶段单元测试证明前一阶段完成前不会调用后一阶段。
- [x] assignment_decision 已驱动地图；Robot C `navigation_plan.anchor_sequence` 已验证为完整 B1→电梯→B2→连廊→A2 路径。
- [x] Demo04：人工工单 → after 图 → 真实云端验收 → CLOSED 已重新验证。
- [ ] 云端超时、无 Key、无效 JSON、模型 veto、验收失败的可见错误与不派单回归。
- [ ] 五个只读 AI Assistant 问答及禁止创建任务/改阈值测试（当前未实现后端）。

## 6. 禁止性结论

- 不得声称本地 Custom YOLO、完整 REAL MODE、真实多机位帧同步、真实机器人遥测或生产阈值已验收。
- 不得把稳定回放、固定前端建议或旧 Mock Verification 写成真实云端结果。
- 任何新测试必须注明日期、代码版本、模式、调用次数与是否真实云端；失败/未测不可省略。

## 7. P0 阶段化真实回归（2026-08-29，待提交 commit）

**环境**：本地 FastAPI + SQLite，`DASHSCOPE_API_KEY` 已配置；受控边缘证据仍为 `CONTROLLED_EDGE_DEMO`。每个场景经 `/events → edge-review → [multi-view] → cloud-review → locate → assign → navigation → cleaning → verify` 顺序执行；Demo04 经人工完成接口。调用次数和模型输出均会自然波动。

| Case | 首轮云端 / 延迟 | 独立复核 / 延迟 | Fusion | 多视角 | 派单 | 验收 / 延迟 | 最终状态 |
|---|---|---|---:|---|---|---|---|
| Demo01 | `.81` / `5517ms` | `.95` / `3973ms` | `.89` | — | Robot A (`robot-a`) | PASS `.95` / `3452ms` | `CLOSED` |
| Demo02 #1 | `.85` / `4854ms` | 未触发 | `.91` | CAM-A1-02、CAM-A1-04 | Robot B (`robot-b`) | PASS `.95` / `3307ms` | `CLOSED` |
| Demo02 #2 | `.75` / `6545ms` | `.95` / `7547ms` | `.97` | CAM-A1-02、CAM-A1-04 | Robot B (`robot-b`) | PASS `.95` / `3150ms` | `CLOSED` |
| Demo02 #3 | `.85` / `4521ms` | 未触发 | `.91` | CAM-A1-02、CAM-A1-04 | Robot B (`robot-b`) | PASS `.95` / `3392ms` | `CLOSED` |
| Demo03 | `.84` / `3559ms` | `.95` / `4671ms` | `.89` | — | Robot C (`robot-c`) | `retry` `.95` / `3296ms` | `HUMAN_REVIEW` |
| Demo04 | large_object / `.92` / `4722ms` | 未触发 | 不派发 | — | 人工工单 | 人工完成后 PASS `.98` / `3684ms` | `CLOSED` |

**Demo03 topology audit**：`B_1F_ROBOT_C_STANDBY → B_1F_ELEVATOR_ENTRY → B_2F_ELEVATOR_EXIT → B_2F_SKYBRIDGE_ENTRY → A_2F_SKYBRIDGE_EXIT → A_2F_CAN_EVENT`。Scheduler 的真实选择为 Robot C；验收失败不会被前端改写为 CLOSED。

**云端不可用异常**：Demo01 执行至 `EDGE_DETECTED` 后以 `cloud-review?simulate_unavailable=true` 模拟不可用，状态为 `HUMAN_REVIEW`，`assignment_decision=null`、`verification=null`；SQLite audit 仅有 `DETECTED → EDGE_DETECTED → HUMAN_REVIEW`。

**浏览器真实性观察**：在 Demo02 点击开始后，首先只看到发现阶段和全部机器人空闲；边缘、多视角完成后，云端阶段显示“正在分析 3 路现场图像”，此时尚无派单/路线/验收结论。云端响应后才进入派单和导航。浏览器 Console error 为 0。前端构建通过；后端单元测试 35/35 通过。
