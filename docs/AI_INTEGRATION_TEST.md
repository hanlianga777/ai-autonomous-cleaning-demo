# Integrated Demo｜AI 集成与回归事实记录

> **状态：IMPLEMENTED 基线 + LOCKED/TODO 验收计划 · 2026-08-30**
> 本文区分已发生的真实调用、当前代码边界和未来必须达到的验收标准。固定 bbox 仍是 `CONTROLLED_EDGE_DEMO`，不是本地 REAL YOLO。

## 1. 当前 AI / Runtime 事实（IMPLEMENTED）

- 云端 transport 唯一入口为 `perception.qwen._request_qwen`；密钥只在本地环境变量。
- 当前实现的首轮 `run_event_qwen_vl` 使用 `confidence >= 0.85` 不触发独立二审、`0.50 <= confidence < 0.85` 调用 `run_targeted_event_qwen_vl`、`confidence < 0.50` 进入 `HUMAN_REVIEW`。未来新 Multi-view Runtime 必须按第 4 节先完成 Evidence Sufficiency Gate，再执行最终 confidence disposition。
- Fusion 为 `0.60 raw cloud + 0.20 category + 0.12 camera/location/time + 0.08 multiview`；veto 不被融合覆盖；raw next_action 不负责系统派单。
- Cloud 只在 cloud-review，Scheduler 只在 assign，Verification 只在 verify / Demo04 人工完成后。LIVE 不可用时停止在 Human Review，无 silent replay。
- 当前 Multi-view 是有 2 路摄像头 / 2 iteration 上限的受控 LangGraph；其触发条件是当前灰区阈值，coverage/frame/VLM 工具顺序固定，使用 controlled evidence assets。这是 IMPLEMENTED 基线，不是下一节锁定的主动视觉取证验收。

## 2. 真实历史记录（不可当作未来成功保证）

| 日期 / 代码 | Case | 结论 |
|---|---|---|
| 2026-08-28，旧单次门控 | Demo01–04 | 历史结果，不适用于独立二审/Fusion/阶段 Runtime 验收 |
| 2026-08-29，`e6b1eb9` | Demo01 / 赛特净界 S5 | 首轮 `.81`、二审 `.95`、Fusion `.89`、`robot-a`、验收 `.95`，CLOSED；这是历史真实结果，不是未来 UI/Runtime 固定值 |
| 同上 | Demo02 / 高仙 Omnie | 真实执行 Multi-view Agent workflow（使用受控多视角证据资产）；均 `robot-b` + CLOSED；首轮 `.85/.75/.85`，仅 #2 二审 `.95`，Fusion `.91/.97/.91` |
| 同上 | Demo03 / 蜗小白 SC50 | `robot-c` 被选、完整演示锚点路径；验收 `retry`，`HUMAN_REVIEW` |
| 同上 | Demo04 | cloud large_object 后人工完成、验收 `.98`，CLOSED；但 cloud 直接人工分支已被新的 LOCKED 目标替代 |
| 同上 | cloud unavailable | `HUMAN_REVIEW`，无 assignment/verification |

这些结果证明 transport、阶段边界和部分真实调用存在；不证明本地 YOLO、生产多机位同步、真实机器人遥测、MapCanvas、Camera→SLAM Runtime、Dijkstra Runtime、Demo03 ROI 验收、Stable Replay、Event Center/Analytics 目标产品或 Robot Operations Agent 已完成。

## 3. LOCKED 模式与安全测试语义

- **LIVE**：真实云端模型请求；失败必须可见并停在 `HUMAN_REVIEW`，不得自动切换 Replay。
- **Stable Replay（TODO）**：只允许使用过去真实成功调用保存的 structured AI evidence；Camera→SLAM、Scheduler、Dijkstra global topology planner / `plan_route()`、Fleet、SQLite transitions、Verification 仍需现场运行。UI 明示“稳定回放”。
- **Product capability / deployment policy**：测试客户显示为赛特净界 S5、高仙 Omnie、蜗小白 SC50、普渡 FlashBot Max，同时验证内部 ID 未变；SC50 地毯轻量垃圾仅作为 Demo Configuration；FlashBot Max 不能成为 Cleaning Scheduler 候选。
- **Demo03 verification（TODO）**：目标 ROI，不是整图找不同；输入原类别、bbox/ROI、before/after 全图和 ROI；机器人、人员、阴影、光照、无关变化不能单独导致失败。非目标干扰失败时独立 ROI 二审，不读取第一次答案。
- **Demo04（TODO）**：必须验证 Cloud → Locate → Capability Engine zero candidate → `HUMAN_FALLBACK` → 人工完成 → after → 云端验收，不允许 Demo ID 或 Cloud 直接跳人工。

## 4. 新 Multi-view Agent 验收（LOCKED / TODO）

### 通用不变量

1. 第一轮 Cloud 只获得主视角、YOLO bbox/detection 和必要 Camera Context，并输出 `confidence`、`evidence_sufficient`、`ambiguity_type`；二者不能混为一谈。
2. **Evidence Sufficiency Gate 优先**：当 `evidence_sufficient=false`，且 reflection / occlusion / perspective / lens_contamination / insufficient_view 可通过额外视角缓解，并存在合法 supporting cameras 时，先进行自主 Multi-view acquisition；不可仅因 Single-view `confidence < 0.50` 转 `HUMAN_REVIEW`。
3. Multi-view 只能通过真实模型的 `tool_choice=auto` Tool Call 进入；Agent 可选 1–2 路，最多 2 evidence acquisition rounds。没有合法 camera、Evidence Fetch 失败或最多 2 rounds 后仍 `evidence_sufficient=false` 时必须 `HUMAN_REVIEW`；最终 evidence 不充分即使 raw confidence 高也不得自动处置。
4. final semantic judgment 的最终充分 evidence 才进入 confidence disposition：`confidence >= 0.85` 不独立二审；`0.50 <= confidence < 0.85` 做 independent targeted second review；`confidence < 0.50` 为 `HUMAN_REVIEW`。该二审可读本次合法完整 evidence set，不得读上一轮模型答案或 reasoning。
5. `find_supporting_cameras()` 返回 Coverage Graph 的真实候选；`fetch_camera_evidence()` 返回合法 evidence；`finish_visual_judgment()` 结束。PoC 可以使用 controlled evidence assets，测试报告必须显式写明，不能假称生产 RTSP 同步。
6. 严禁 `if demo_id == "demo02"`、固定 confidence threshold、`tool_choice=required`、初轮三图、前端 `setTimeout` 伪 Trace、静态选择 CAM-A1-02/A1-04。

### Demo02 LIVE

| 场景 | 次数与通过条件 | 必须记录 |
|---|---|---|
| A栋 1F 液体污渍 / 高仙 Omnie | 连续真实运行 5 次，至少 4 次由模型在 recoverable evidence insufficiency 下自主发起 Multi-view Tool Calling，并完成 candidate search → 1–2 路 evidence fetch → final semantic judgment → final confidence disposition → Capability / Scheduler → 高仙 Omnie → verification → CLOSED | single-view result、sufficiency、ambiguity、每次 Tool Call、candidate/selected cameras、evidence、final judgment、是否二审及 evidence-set 来源、final decision、latency、run/commit |

模型不稳定时只允许优化主视角、Prompt、Tool Description、Camera Metadata、Evidence Assets；严禁增加 demo_id 分支或强制前端阶段。客户 UI 步骤必须能回溯 Agent Trace / Tool Audit / Cloud Response / backend transition，且不展示 Chain-of-Thought。

## 5. Workbench / Event Center / Analytics 验收（LOCKED / TODO）

| 范畴 | 验收标准 |
|---|---|
| Workbench | MapCanvas 内白模、anchor、robot、route、marker 共用坐标；真实 SQLite transition timestamp；任务终态保留；统一 `EventDetailPanel(mode="live")` |
| Event Center | 新 CleaningEvent 立即出现、默认倒序；全部/处理中/自主闭环/人工/异常正确分类；正常 `HUMAN_FALLBACK` 不为异常；`?event=` 恢复选择；history detail 不重跑 Runtime 且使用 event-time snapshot |
| Analytics | 明确“近30天 · 演示历史数据”；5 KPI 均可追溯到 event/transition；处理中/异常 denominator 有规则；Heatmap / filters / drill-down 跳 Event Center；不使用 hardcoded KPI、利用率或趋势 |
| Robot utilization | 只统计赛特净界 S5、高仙 Omnie、蜗小白 SC50 的任务状态时间 ÷ 可用时间；FlashBot Max 不进清洁利用率排名 |

## 6. Robot Operations Agent / Delivery 验收（LOCKED / TODO）

- **Read 与 Page Context**：Workbench、Event Center、Analytics 是同一 `AgentSession`；分别自动传入当前 event/fleet/map、selected event/filter、time/type/hotspot/robot/KPI/chart context。
- **Action**：低风险 cleaning / delivery / relocation standby 任务必须经 Policy Guard、生成真实 backend Task 与 Action Card，并与 Fleet / Workbench 共享 Task ID / state。
- **Audit**：每个影响物理世界的 Action 记录原始指令/ASR、intent、tool/args、guard、Task ID、robot、结果、异常、replan、final state。
- **禁止工具测试**：Agent 无法获得或调用改 map、禁行区、范围、capability、Coverage/calibration、Scheduler policy、threshold、速度、门禁、电梯权限的 Write Tool。
- **UI / ASR**：Workbench/Event Center 同一可拖动浮窗；无已保存位置默认左下角，localStorage 位置优先，刷新/跨页/展开/收起保持，拖动不出 viewport。Analytics 仅固定 Panel；不出现第二 Agent。Microphone 只有配置的真实 ASR provider 可调用时才可用；未配置时必须 disabled 或显示“语音服务未配置”，不得使用预设文本、timer、mock transcript 或 fake voice animation。
- **Delivery Adapter**：没有真实平台授权必须是 `ADAPTER READY` / `AUTH REQUIRED`；不得显示 `CONNECTED` 或模拟外部 callback。真实授权后才测试 webhook / 双向状态同步。

## 7. Advanced Technical Observability 验收（LOCKED / TODO）

| 场景 | 必须可审计的 Advanced Trace |
|---|---|
| Demo01 | Edge → Single-view Cloud → `NOT_TRIGGERED / EVIDENCE_ALREADY_SUFFICIENT` Multi-view → Business Decision / Fusion → Verification |
| Demo02 | Edge → Single-view Cloud → Evidence Insufficient → `MODEL_TOOL_CALL` → supporting camera search → evidence fetch → Multi-view Cloud → Decision / Fusion → Verification；不得显示 `SYSTEM_WORKFLOW` 强制进入 |
| Demo03 | Camera→SLAM → Capability → Scheduler → 真实 `plan_route()` → 蜗小白 SC50 → Verification |
| Demo04 | Cloud → Camera→SLAM → Capability Candidate Count 0 → `HUMAN_FALLBACK` → Manual completion → Verification |

- **Reality Badge**：controlled edge 不得显示 `LIVE MODEL`；controlled camera evidence 不得显示 production live camera；PoC robot 不得显示 real telemetry；未授权 Delivery Adapter 不得显示 `CONNECTED`；Reality Matrix 的状态由 Runtime fact / configuration / provider / evidence / authorization 自动决定，用户不可编辑。
- **Runtime / Error**：验证 LIVE success、LIVE model failure、用户手动启用 Replay、`POLICY_REJECTED`、`SPATIAL_ERROR`、`ROUTE_ERROR`、`VERIFICATION_ERROR`；错误层级准确，LIVE failure 无 silent Replay。Tool Trace 必须有 tool、trigger source、start time、duration、status、input/result summary，不能是前端定时器。
- **Sensitive data / CoT**：任何 Advanced UI/API response 不得泄漏 API Key、Secret、Access Token、Authorization Header 或环境变量具体值；不得显示 Chain-of-Thought、scratchpad 或 reasoning tokens。
- **Trace projection**：Advanced 只投影 CleaningEvent transitions、cloud/model request record、Agent Action/Tool Audit、spatial/capability/scheduler/route/verification/provider/reality metadata；不得重跑模型、Scheduler 或 Route Planner。Trace ID 独立于 Event ID，并可串联 Event / AgentTask / Tool / model / task runtime。

## 8. 清洁主场景总体回归（LOCKED / TODO）

| 模式 | 场景 | 次数与通过条件 |
|---|---|---|
| LIVE | Demo01 | 连续 5 次，至少 4 次赛特净界 S5 → verify → CLOSED |
| LIVE | Demo02 | 见第 4 节；至少 4/5 自主 Tool Calling 后高仙 Omnie → verify → CLOSED |
| LIVE | Demo03 | 连续 5 次，至少 4 次蜗小白 SC50 → Dijkstra global topology planner / `plan_route()` 跨楼/电梯/Skybridge → ROI verify → CLOSED |
| LIVE | Demo04 | 连续 3 次，全部 Cloud → Locate → zero candidate → Human → verify → CLOSED |
| Stable Replay | 四个 Demo | 每个连续 3 次，100% 正确流程；不得跳过非 AI Runtime |

每次必须记录 run id / commit、模式、时间、raw cloud confidence、是否二审及 confidence、Fusion/composite score、系统决策、selected robot、route、verification raw result、最终状态、每个云端请求 latency。主场景合理业务成功率低于约 80% 时，先调查 Prompt、ROI、ontology、输入上下文、parser、模型/系统决策分离，而不是仅称“随机”。

## 9. 当前限制与禁止性结论

- 当前不宣称 REAL YOLO、生产多机位同步、真实机器人遥测、真实电梯、真实外卖平台集成或生产阈值。
- 旧 Stable Replay 不能叫完整稳定回归，直到满足本文件第 3 节定义。
- Demo03 目前的 `retry` 必须如实保留；不能通过 Demo ID 特判或写死 PASS 修复。
- 当前 Advanced 仅是基础 shell；不宣称已完成 Trace Inspector、Reality Matrix、结构化 audit、真实 Tool / Error / source projection 或 Trace ID。
- 本轮是 docs-only；没有运行新的代码、模型、浏览器或 API 测试。
