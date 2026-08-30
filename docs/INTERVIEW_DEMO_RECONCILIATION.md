# Interview Demo Reconciliation

> 本文件记录最新用户确认需求与历史事实源、当前 active implementation 的对齐关系。
> 优先级：最新用户明确确认需求 > 本文件的 `LOCKED TARGET` > `DECISIONS.md` / `ARCHITECTURE.md` > 旧 `IMPLEMENTED` 描述 > 当前代码实际行为。

## GLOBAL IMPLEMENTATION CONTRACT｜统一 Interview Demo Recovery

- 本文件中全部 `LOCKED TARGET`（包括既有 AI-UI-01、WB-DETAIL-01、WB-MAP-01、WB-CAMERA-01 和今后新增的每个 Requirement）共同组成一个强制的产品版本，都是未来 `UNIFIED INTERVIEW DEMO RECOVERY` 的 mandatory implementation scope；不得只实现最后一条、遗漏子项、用当前代码反向覆盖目标，或实现新需求时破坏已锁定需求。
- 当前阶段仅同步需求，不实施。只有用户明确说“讨论结束，可以统一实施”后，才可开始代码工作；开始前必须完整读取本文件、`PROJECT_CONTEXT.md`、`DECISIONS.md`、`ARCHITECTURE.md`、`TODO.md`、`CODEX_HANDOFF.md`、`AI_INTEGRATION_TEST.md` 和 active code，并先建立覆盖每个子项的 `REQUIREMENT IMPLEMENTATION MATRIX`（Requirement → affected code → implementation status）。
- 每次实施一个模块前都必须复核其相关所有 LOCKED Requirement；修改共享组件时必须检查 AI UI、Workbench Detail、Workbench Map 和后续要求的回归影响。技术实现由 Codex 决定；只有业务含义或最终产品/UI效果不明确时才可询问用户。

## AI-UI-01｜AI 运营入口与聊天交互

| Field | Value |
| --- | --- |
| ID | AI-UI-01 |
| Module | Robot Operations Agent UI |
| Status | **LOCKED TARGET** |
| Scope | Docs-only delta sync；本轮不修改 frontend、backend、脚本、数据库、测试或 Runtime。 |

### User Intent

用户确认的是同一个 **Robot Operations Agent** 在三处页面的两种 UI 投影：Workbench 与 Event Center 使用可拖动的圆形 AI 入口和完整弹出式对话；Analytics 使用固定的统一右侧 AI 区域。目标是重新设计前端交互 Shell，不新增第二个 Agent，也不改变既有 Robot Operations Agent 后端能力、Session、Task、Audit 或 Backend State。

### GitHub Previous Coverage

- 已覆盖：唯一 Robot Operations Agent；Workbench、Event Center 与 Analytics 共享 Agent Session、消息、Task/Action Audit、页面上下文与后端状态；Analytics 的 Advice 是同一 Agent 的只读能力，不能自动改运营配置；Analytics 不得新建独立 Analytics / Optimization / Conversation Agent。
- 已覆盖：Workbench / Event Center 的 UI 位置可保存在 localStorage，默认左下、跨页与刷新保持，且位置不能离开 viewport；Analytics 使用固定右侧 Panel。
- 以前缺失：收起入口必须为小型**圆形/球形** AI 悬浮球；点击后必须是完整 AI Assistant Chat Window，而非横向 Tool/Task Panel；Analytics Advice 和 Chat 必须是同一个无割裂右侧 AI Area；右侧 Chat 的输入入口必须在进入 Analytics 后的当前可视高度内可发现，并拥有独立布局/滚动逻辑。
- 以前的“共享长条浮窗”“仅 Header / Drag Handle 拖动”“现有展开式 Tool Panel”是 P1-F 的历史实现/覆盖描述，**SUPERSEDED BY AI-UI-01**；它们不再是当前 UI Shell 的 LOCKED TARGET。

### Current Implementation

- `PrototypeWorkbench.tsx` 在 Workbench / Event Center 渲染 `FloatingRobotOperationsAgent`，在 Analytics 渲染 `AnalyticsView`；三页均处在同一个 `RobotOperationsProvider` 下，故现有 Agent Session / Task / Audit / Backend State 仍为共享事实。
- `FloatingRobotOperationsAgent` 当前默认展开；其收起状态仍是宽 `352px`、高 `40px` 的横向标题条，而非圆形 AI 悬浮球。默认位置及 clamp 以 `352×454` 面板尺寸计算，位置会写入 localStorage。
- 当前浮窗以 Header 承载拖动；展开后是约 `352×454` 的 Panel，混合消息、任务操作卡、工具审计和紧凑输入框。它可收起/展开，但视觉与信息架构更接近 Tool/Task Panel，而非明确、完整的 AI Chat 产品窗口。
- Analytics 已把 Advice 放在右侧上半、同一 Agent Chat 放在下半；但 `AnalyticsView` 的右侧 aside 跟随左侧长 Analytics 内容形成页面流布局。左侧内容变长时，Chat 及其输入区不能保证留在当前浏览器可视高度内，用户可能要滚动整个 Analytics 页面才能输入。

### Root Cause

- `SOURCE_MISSING`：旧 P1-F 文档锁定了共享 Agent、会话和位置持久化，却没有锁定 AI-UI-01 所要求的完整入口、完整 Chat 和 Analytics 可发现性规格。
- `IMPLEMENTATION_DIVERGENCE`：当前 active frontend 仍实现历史长条浮窗 / Header 拖动 / Tool Panel 形态，Analytics 右侧区域也未满足独立可视布局要求。

### Locked Target

#### AI-UI-01.1｜Workbench / Event Center 入口

- Workbench 和 Event Center 使用**同一个** Robot Operations Agent。
- 默认仅显示小型、圆形/球形的 AI Assistant 悬浮球，位于页面左下区域；不能使用横向矩形长条作为收起状态，不能把整个 `352px` Header 当作悬浮入口。
- 悬浮球必须可拖动，用户可以移动到整个浏览器可视区域内的任意合法位置，不得只限于一小块拖动区域；位置可以持久化。
- 默认位置不得遮挡核心页面内容。
- 收起状态只保留小型圆形 AI 悬浮球。

#### AI-UI-01.2｜Workbench / Event Center 完整对话窗口

- 点击圆形悬浮球后，必须弹出明显、完整的 AI Assistant 对话窗口；不得只在原长条工具面板原地展开。
- 对话窗口必须包含：AI Assistant 欢迎/身份区域、对话历史、用户消息、AI 回复、明显的文本输入区域、发送按钮、必要状态提示，以及关闭/收起后重新变回圆形悬浮球的入口。
- 整体体验必须让用户一眼认知为完整 AI 聊天助手，不得呈现为工程调试面板、Task Debug Panel、长条工具卡或小型系统日志窗口。
- Robot Operations Agent 的后端能力保持不变；本目标仅重新设计前端交互 Shell，不新增第二个 Agent。

#### AI-UI-01.3｜Analytics 固定 AI Area

- Analytics 不使用 Workbench / Event Center 的悬浮球。
- Analytics 页面右侧必须形成一个固定的统一 AI 区域：上半为“AI 运营分析 / 运营建议”，下半为完整 Robot Operations Agent 对话窗口；上下两部分属于同一个右侧 AI Area。
- 下半部分必须是明显、完整的 AI Chat，具有清晰消息区、输入框与发送入口；Advice 与 Chat 不得有强烈割裂感。
- 左侧 Analytics 页面内容很长时，不得把聊天输入框推到整页底部。用户进入 Analytics 后，必须能在当前浏览器可视高度内找到 Chat 入口；右侧区域必须有自己的布局/滚动逻辑。

#### AI-UI-01.4｜共享状态与禁止新增 Agent

- Analytics、Workbench 与 Event Center 继续共享同一个 Robot Operations Agent、Agent Session、Task / Audit / Backend State：**一个 Agent，两种 UI 投影**。
- 严禁因此新建 Analytics Agent、Optimization Agent 或第二个 Conversation Agent。

### Must Not Do

- 不得简化、合并、改变本条交互含义，或以“更合理的 UX”、现有代码或实现难度替代本 LOCKED TARGET。
- 不得把旧共享横向长条浮窗、仅 Header / Drag Handle 拖动、现有展开式 Tool/Task Panel 重新当作当前目标。
- 不得把 Analytics 改用浮动球，也不得让 Advice 与 Chat 变成两个割裂的右侧系统。
- 不得因 UI 改造新增第二 Agent、第二 Session、第二 Conversation State、Analytics Agent 或 Optimization Agent。
- 未来实施不得只证明“共享 Agent”而跳过任一 UI 细节。

### Acceptance Criteria

| ID | 可视觉验收标准 |
| --- | --- |
| AI-UI-01.1 | Workbench 和 Event Center 初始仅显示左下小型圆形 AI 悬浮球；没有横向收起条或 `352px` Header 入口。 |
| AI-UI-01.2 | 悬浮球可拖至整个浏览器可视区域内的合法位置，刷新及在 Workbench / Event Center 之间切换后位置仍保留，且默认位置不遮挡核心内容。 |
| AI-UI-01.3 | 点击悬浮球显示明显的完整 Chat Window，能看见 Assistant 身份/欢迎、历史消息、用户/AI 消息、输入框、发送按钮、状态提示和关闭/收起控制；关闭后恢复圆球。 |
| AI-UI-01.4 | 展开窗口的视觉语义是 AI Chat，不是 Tool/Task Debug Panel、长条工具卡或系统日志；任务/Audit 投影不得取代聊天核心结构。 |
| AI-UI-01.5 | Analytics 右侧同时包含上半 Advice 与下半完整 Chat，二者属于一个统一 AI Area；下半有清晰消息区、输入框和发送入口。 |
| AI-UI-01.6 | 在左侧 Analytics 内容足够长的页面中，进入 Analytics 时右侧 Chat 入口仍在当前可视高度内；右侧自身滚动不依赖把整页滚到最底部。 |
| AI-UI-01.7 | 三页使用同一个 Robot Operations Agent、Session、消息、Task、Audit 和后端状态；没有 Analytics / Optimization / 第二 Conversation Agent。 |

### Future Implementation Evidence Rule

未来 Unified Interview Demo Recovery 的最终 Implementation Report 必须逐项列出 `AI-UI-01.1` 至 `AI-UI-01.7`，每一项都要对应代码文件、实现、测试与用户验收结果。任何子项未实现，AI-UI-01 不得标记为 `IMPLEMENTED`。

### Affected Active Code (future work only; unchanged this round)

- `frontend/src/components/prototype/PrototypeWorkbench.tsx`
- `frontend/src/components/prototype/AnalyticsView.tsx`
- `frontend/src/components/robot-operations/RobotOperationsPanel.tsx`
- `frontend/src/components/robot-operations/robotOperationsModel.ts`
- `frontend/src/components/robot-operations/RobotOperationsProvider.tsx`

## WB-DETAIL-01｜面客事件处置详情与实时业务进度

| Field | Value |
| --- | --- |
| ID | WB-DETAIL-01 |
| Module | Workbench Event Detail / demo_v1 customer projection |
| Status | **LOCKED TARGET** |
| Scope | Docs-only delta sync；本轮不修改 frontend、backend、runtime、test、database 或 launcher。 |

> 所有技术真实性、审计、算法参数、schema、raw evidence、latency、error taxonomy 与 PoC 边界统一进入 Advanced / Technical Detail。Workbench 只投影真实 Runtime 事实的面客业务叙事；不得为展示编造模型耗时、路线、ETA、设施、状态或验收结果。

### WB-DETAIL-01.1｜面客定位与信息层级

- **User Intent**：Workbench 右侧“最近事件处置详情”必须面向客户/面试官，实时说明一次 AI 自主清洁事件如何发生、研判、调度、执行、验收和闭环。首屏只回答发生什么、AI 判断什么、系统下一步、机器人到哪里、是否验收闭环；它不是工程日志、Debug 面板、技术免责面板、数据库 Trace 或算法参数面板。
- **Current Implementation**：`EventDetailPanel` 副标题仍为“真实阶段记录 · 完整处置过程”；各阶段混杂事实、审计、技术边界与执行说明，整体仍具有技术流程面板语义。
- **Previous Source Coverage**：D02 已要求客户层使用业务中文，D13 已指定 Advanced 为技术观测页；但没有把 Workbench 首屏问答、信息层级和面客/Advanced 边界锁定为可验收规格。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：右侧以业务优先、结果优先、过程清楚、字段少而精、层级明显为原则；允许一个低干扰全局 `POC / DEMO` 身份提示，不得每阶段重复免责。工程师追问才进入 Advanced。
- **Acceptance Criteria**：不打开 Advanced 即可在首屏识别事件、AI 结论、下一业务动作、执行进度与最终验收；主流程不出现工程日志/Debug 风格、重复免责声明或成段技术说明。
- **Affected Active Code**：`frontend/src/components/prototype/EventDetailPanel.tsx`、`EventStageEvidence.tsx`、`eventViewModel.ts`。

### WB-DETAIL-01.2｜渐进式真实业务节奏

- **User Intent**：Demo 必须像正在发生的真实业务事件逐步出现。普通确定性步骤（事件发现、边缘识别、空间定位、能力筛选、机器人派单）应各有约 1.5–3 秒可感知展示节奏；Cloud 仅以真实 API 调用时间推进并显示“AI研判中…”，Multi-view 按真实工具调用/模型响应推进，Navigation 按真实 backend Dijkstra route 的 PoC playback 连续移动，Cleaning 也要有可感知 PoC 执行过程，Verification 必须等当前 Cloud 返回。不得伪造 Cloud latency。
- **Current Implementation**：`PrototypeWorkbench` 对已完成的确定性阶段以 `queueMicrotask()` 连续提交下一 stage；多个业务步骤可在同一秒完成。`SpatialDispatchView` 已有后端路线驱动的连续 playback，但 Cleaning 到 Verification 没有独立可感知执行节奏；Cloud 与 verification 的等待由真实请求结果决定。
- **Previous Source Coverage**：P1-B 已锁定路线连续插值、P1-A/B 已锁定真实 transition timestamp 和模型真实 latency、P1-C 已锁定真实 Multi-view tool loop；没有锁定 Workbench 其余确定性阶段的面客可感知节奏与 Cleaning 展示节奏。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：展示节奏只能延迟客户层对已持久化确定性阶段的展示/推进，不得预计算整条流程、伪造模型耗时、改变 Cloud/Multi-view/Verification 调用边界，或把 PoC route playback 伪称真实遥测。
- **Acceptance Criteria**：演示录屏可清楚看见各普通业务步骤按约 1.5–3 秒逐步出现；Cloud/Verification 仅在真实返回后进入下一步；触发 Multi-view 时工具与响应按真实顺序可见；导航连续移动且 Cleaning 不从 ARRIVED 瞬跳 VERIFYING。
- **Affected Active Code**：`PrototypeWorkbench.tsx`、`SpatialDispatchView.tsx`、`runtimeSession.ts`、`frontend/src/components/prototype/useRoutePlayback.ts`、`backend/demo_v1/service.py`。

### WB-DETAIL-01.3｜发现现场与边缘目标识别

- **User Intent**：发现卡以地点、事件、发现时间表达真实业务，例如“园区东侧道路发现疑似小型垃圾”；边缘识别卡突出识别对象、核心置信度、现场图像和检测框。不得在客户主卡展示“事件已持久化”“受控边缘检测”“不代表本地 YOLO”“bbox 坐标”等技术/存储说明。
- **Current Implementation**：DETECTED 显示“现场证据已接收，事件已持久化”；EDGE_DETECTED 显示受控边缘检测、同坐标系和“不代表本地 YOLO 实跑”，虽已有图像/检测框，但未突出对象与核心置信度的面客表达。
- **Previous Source Coverage**：P1-B 已有客户 enum 中文化及图像/overlay 投影，P1-C/D13 已锁定受控证据真实性应可审计；没有锁定这些内容必须移出 Workbench 客户主卡。
- **Root Cause**：`IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：客户层只使用业务语言呈现真实地点、事件、发现时间、对象、核心置信度、现场图像和检测框；存储、controlled-edge、YOLO、bbox/坐标技术说明转入 Advanced。
- **Acceptance Criteria**：右侧 DETECTED / EDGE_DETECTED 卡片不含持久化/controlled-edge/本地 YOLO 免责声明或 bbox 技术解释；可一眼看见地点、对象、时间、图片、框和核心置信度。
- **Affected Active Code**：`EventStageEvidence.tsx`、`EventDetailPanel.tsx`、`eventViewModel.ts`、`backend/demo_v1/service.py`。

### WB-DETAIL-01.4｜云端 AI 综合研判卡

- **User Intent**：客户层只突出一个“最终有效 AI研判置信度”，不得同时堆叠首轮、最终语义和独立复核置信度。若展示 Fusion，必须称“系统处置评分 XX分”且不用百分比。Cloud Card 固定独立左对齐字段行：研判结果、事件类型、AI研判置信度、污染程度、地面材质、系统处置评分、研判摘要；Label 加粗，置信度与评分视觉强调且彼此区分，摘要只 1–2 句。Evidence Sufficiency、干扰因素、API latency、schema 等进 Advanced。
- **Current Implementation**：`CloudSummary` 同时显示首轮/最终/独立复核置信度、证据充分性、干扰因素和 API 耗时；多个核心字段同一行，视觉权重基本一致，Fusion 仍写作“系统 Fusion 处置评分”。
- **Previous Source Coverage**：D04 已锁定 Fusion 用“综合处置评分：N分”且不与 raw 模型百分比混淆，P1-C 已锁定 evidence/second review 真实性；但未锁定单一主置信度、字段排版与技术明细从面客卡移除。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`；旧“客户时间线可显示模型真实 latency”的面客展示部分 **SUPERSEDED BY WB-DETAIL-01**，真实 latency 仍保留在 Advanced。
- **Locked Target**：使用真实最终有效 AI 结论，不改写模型/二审/Fusion 事实；面客只呈现上述字段和 1–2 句研判摘要，技术证据与真实 latency 留 Advanced。
- **Acceptance Criteria**：Cloud Card 仅有一个视觉强调的 AI研判置信度；评分显示为“系统处置评分 N分”；每个主要字段独立一行、Label 加粗左对齐，且不出现 sufficiency/干扰/API/schema/多份置信度。
- **Affected Active Code**：`EventStageEvidence.tsx`、`eventViewModel.ts`、`backend/demo_v1/service.py`、`frontend/src/components/prototype/AdvancedView.tsx`。

### WB-DETAIL-01.5｜真实空间定位的客户投影

- **User Intent**：客户层必须真实投影已有 spatial 结果：定位位置、Building、Floor、Zone、SLAM X/Y、Map ID 对应的客户层地图名称。技术定义准确为“固定摄像头图像目标位置 → 四点 Camera/SLAM 标定 → 2D SLAM Map Coordinate”，不得描述为 3D Reconstruction、三维重建或真实深度估计。
- **Current Implementation**：LOCATED 卡显示“Camera→SLAM 标定映射已完成”、building/floor/zone 和“空间落点已写入事件与地图”，没有显式 X/Y、map ID 的客户名称；未知枚举还可能被投影为“未归类 / 待复核”。
- **Previous Source Coverage**：P1-A/B 已锁定 `map_pixel_to_slam()`、building/floor/zone/map/x/y 的真实持久化，D05 已规定 Camera→SLAM 和路线事实；客户层完整定位字段/地图名称及准确二维表述缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：只从真实 `spatial_location`/transition 投影位置和坐标，Map ID 必须映射为客户地图名称；四点标定和二维语义可在准确、低噪音方式表达，详细 u/v/homography 仅 Advanced。
- **Acceptance Criteria**：定位卡明确显示如“A栋2F · 东侧走廊”、Building/Floor/Zone、`SLAM坐标：X … / Y …` 与“所属地图：…”；不出现“未归类 / 待复核”替代已有有效后端空间结果，也不含 3D/深度表述。
- **Affected Active Code**：`EventStageEvidence.tsx`、`eventViewModel.ts`、`frontend/src/components/prototype/spatialProjection.ts`、`backend/demo_v1/service.py`、`backend/spatial/calibration.py`、`backend/spatial/spatial_data.py`。

### WB-DETAIL-01.6｜能力匹配与机器人派单

- **User Intent**：客户层只用正式名称赛特净界 S5、高仙 Omnie、蜗小白 SC50；FlashBot Max 不得成为 Cleaning Scheduler 候选。能力匹配应以简单业务语言表现 Hard Constraint Filter → Eligible Candidates → Soft Score → Assignment：不满足硬约束者灰化/×、显示 1–2 个关键原因和“未进入评分”；只有合格候选显示真实调度评分；最终选择明显高亮。不得从历史 snapshot 泄漏 Robot A/B/C，也不得伪造未进入评分者的 Soft Score。
- **Current Implementation**：`CapabilitySummary` 直接渲染 `assignment_decision.candidates` 和其 `robot_name`/原因，未强制正式命名投影、未明确“未进入评分”、未做候选灰化/最终高亮；当前 scheduler 已只对 eligible 候选计算真实 `final_score`，且未配置 profile 的 FlashBot 不进入候选。
- **Previous Source Coverage**：D03、P1-A/P1-F 已锁定正式名称、Capability + Scheduler 唯一选择器、FlashBot 不参与清洁调度；客户层 Hard Filter/Score/Assignment 的视觉语义和旧名称泄漏防线未锁定。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：前端只投影真实 decision 的候选、hard reject、评分和 selected robot；正式名称要覆盖 active 与历史展示，不能更改 Capability/Scheduler 或伪造 score。
- **Acceptance Criteria**：每次派单中，淘汰机器人以灰化 ×、1–2 个关键原因和“未进入评分”显示；合格机器人显示真实评分，最终派发显著高亮；不显示 Robot A/B/C 或 FlashBot Max 清洁候选。
- **Affected Active Code**：`EventStageEvidence.tsx`、`eventViewModel.ts`、`backend/scheduling/capability_engine.py`、`backend/scheduling/scheduler.py`、`backend/scheduling/profiles.py`。

### WB-DETAIL-01.7｜机器人前往现场与路线事实

- **User Intent**：导航卡以业务执行摘要显示执行机器人、真实 backend navigation_plan / Dijkstra route 的预计路径距离、预计到达时间、主要路径节点、是否需要电梯/空中连廊和当前状态。不得显示“依据后端 Dijkstra…”或“PoC 视觉插值/非真实遥测”的免责声明，也不得由前端/LLM 编造距离、ETA、设施或路径。若当前 route 没有可计算 distance/ETA，必须记录实施 Gap，并在未来以确定性 route 数据计算。
- **Current Implementation**：导航卡仅显示 Dijkstra 技术文案、`display_path` 和 PoC 插值免责声明；route planner 返回 topology `total_cost`/segments/node path，但没有面客 distance/ETA 字段或确定性换算，故距离与 ETA 当前不能真实显示。
- **Previous Source Coverage**：P1-A/B/D05 已锁定 Dijkstra route、真实 node/segment path、PoC playback 与不伪造路线；没有锁定客户业务字段、设施摘要或可计算 distance/ETA 的数据契约。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE` + `IMPLEMENTATION_GAP`（现有 navigation plan 缺少可展示的真实 distance/ETA）。
- **Locked Target**：路线事实必须只来自 backend navigation_plan/Dijkstra；当数据契约补齐前，不能填充或写死距离/ETA。PoC 属性可保留为一次低干扰全局身份提示，不得阶段重复。
- **Acceptance Criteria**：导航卡用客户语言显示机器人、主要节点、当前状态、电梯/连廊；所有已显示值可追溯至 navigation plan。若 distance/ETA 尚无确定性数据，验收不得用占位/虚构值通过，并明确列为未完成 Gap。
- **Affected Active Code**：`EventStageEvidence.tsx`、`SpatialDispatchView.tsx`、`frontend/src/components/prototype/spatialProjection.ts`、`backend/demo_v1/service.py`、`backend/spatial/route_planner.py`、`backend/spatial/spatial_data.py`。

### WB-DETAIL-01.8｜完整闭环、ownership 与失败释放

- **User Intent**：四个正式 Demo 必须自动完成真实业务流程，不得永久停在 NAVIGATING/ARRIVED/CLEANING/VERIFYING；Demo01–03 完整至 CLOSED，Demo04 以 zero candidate → HUMAN_FALLBACK → 用户确认人工搬运 → after evidence → AI Verification → CLOSED/HUMAN_REVIEW。Workbench 直接触发的正式 Demo 不得因共享 Robot Operations Agent 失去 Runtime 推进权；Agent 接管与 Workbench demo 要有清晰 ownership。任何 Cloud/API/Spatial/Route/Verification 异常必须得到明确错误或 HUMAN_REVIEW，保留记录并释放 Workbench 下次启动条件，不能锁死四个 Demo。
- **Current Implementation**：`runtimeSession.canAutoAdvance()` 只允许非 task-owned、非 paused、非 terminal 的 Workbench event 自动推进；task-owned event 被共享 Operations controls 接管。`canStartDemo()` 仅在无事件或 terminal 后可启动；前端错误分支会停止重复提交，但当前 Source of Truth 没有面客演示级别的“每个故障必终态并释放启动条件”验收契约。确定性 stages 现有自动推进过快而非逐步展示。
- **Previous Source Coverage**：P1-A/P1-G/D12 已锁定 stage boundary、Demo04 Human Fallback、durable lease/ownership、错误 taxonomy、LIVE failure 不 silent replay 与正式回归记录；没有把 Workbench 正式 Demo 的自动闭环、ownership 和所有失败释放作为 P0 面客验收项。
- **Root Cause**：`SOURCE_MISSING`；自动推进节奏是 `IMPLEMENTATION_DIVERGENCE`，task/workbench ownership 与 failure release 需要针对本目标的实施/验收收口。
- **Locked Target**：保留一个 Runtime、SQLite transition、真实 Cloud/Verification 与既有 Robot-first/Human Fallback。未来实现自行选择技术机制，但必须清楚区分 Workbench-origin demo 和 Agent-origin task 的 mutation owner，并保证每条失败路径终态化/可恢复而不永久占用 Demo 启动条件。
- **Acceptance Criteria**：四个 Workbench 正式 Demo 可重复运行并按其指定流程到 CLOSED/HUMAN_REVIEW；故障注入的 Cloud/API/Spatial/Route/Verification 路径保留事件、给出明确终态并允许后续 Demo 启动；共享 Agent 不阻断其未接管的 Workbench Runtime。
- **Affected Active Code**：`PrototypeWorkbench.tsx`、`runtimeSession.ts`、`SpatialDispatchView.tsx`、`backend/demo_v1/service.py`、`backend/robot_operations/coordination.py`、`backend/robot_operations/tasks.py`、`backend/observability/errors.py`。

### WB-DETAIL-01.9｜面客 AI 验收与结果闭环

- **User Intent**：右侧流程必须显式展示“固定摄像头处置后取证 → AI验收 → 验收结果”，至少有处置后图片、通过/未通过、验收置信度和最终结论。通过进入完整闭环；未通过按既有 Runtime 重新处置或人工复核。Verification 不能只存在 backend/Advanced。
- **Current Implementation**：VERIFYING 已显示处置后图片与 AI 验收置信度；CLOSED 卡写“验收门控通过 · 完整闭环已持久化”，HUMAN_REVIEW 则以技术原因表达。最终结果的面客业务结论与复处置/人工复核去向没有作为统一、清晰的验收闭环展示。
- **Previous Source Coverage**：P1-A/P1-G/D12 已锁定 after evidence、真实 Cloud verification、fail closed 与 CLOSED/HUMAN_REVIEW；P1-B 已有 Verification timeline stage，但面客右侧的完整可视闭环字段和结果表达缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：客户流程始终保留真实 Verification stage 与 after image；验收结果只取真实 verification/runtime result，失败后严格遵循既有重新处置或人工复核状态，不创造第二套验收逻辑。
- **Acceptance Criteria**：每个完成/失败 demo 的右侧可找到 after 图、AI验收通过/未通过、验收置信度和最终业务结论；通过显示完整闭环，未通过显示真实的下一状态（重新处置或人工复核）。
- **Affected Active Code**：`EventStageEvidence.tsx`、`EventDetailPanel.tsx`、`eventViewModel.ts`、`backend/demo_v1/service.py`、`backend/perception/qwen.py`、`backend/perception/verification_evidence.py`。

### WB-DETAIL-01.10｜全局视觉与技术信息迁移

- **User Intent**：面客 Event Detail 禁止单卡堆大量技术字段、英文工程术语、同义重复字段、重复免责声明、Debug Log 风格、同权重文字和说明书式长文；技术真实性信息要保留但只在 Advanced / Technical Detail 可追溯。
- **Current Implementation**：`EventStageEvidence` 在客户时间线直接显示 controlled evidence、API timing、source/replay、tool audit、schema 历史提示、Dijkstra/PoC 非遥测等多类技术文本；Advanced 已具备 Trace → Node → Inspect、Source Badge、error taxonomy、spatial/capability/route/verification 技术投影。
- **Previous Source Coverage**：D13/P1-H 已实现 Advanced 的技术透明与不泄露 CoT；D02 仅概括要求客户层业务中文，未定义具体字段迁移清单和右侧视觉禁令。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：将完整处置过程、真实阶段记录、持久化、controlled edge、非本地 YOLO、历史 schema、PoC 插值/非遥测、API latency、内部 error/schema/evidence/technical reason 等从 Workbench 默认客户卡迁至 Advanced/Technical Detail；不得删除底层事实或真实性审计。
- **Acceptance Criteria**：客户右侧卡片不包含上述技术清单或英文工程堆栈；Advanced 仍可读取相应真实 trace/metadata，且没有前端伪造/删除事实。
- **Affected Active Code**：`EventDetailPanel.tsx`、`EventStageEvidence.tsx`、`eventViewModel.ts`、`frontend/src/components/prototype/AdvancedView.tsx`、`backend/observability/service.py`。

### WB-DETAIL-01.11｜实现报告与全项门槛

- **User Intent**：未来 Unified Interview Demo Recovery 必须逐项完成本 Requirement；任何一项未完成，WB-DETAIL-01 不得标记 IMPLEMENTED。
- **Current Implementation**：当前工程/自动化历史验收为 P1-A/B/C/D/E/F/G/H 的 IMPLEMENTED 事实，不等同 WB-DETAIL-01 的新面客体验验收。
- **Previous Source Coverage**：`TODO.md` 和 `PROJECT_CONTEXT.md` 将用户主观展示验收保留为未完成，但未建立 WB-DETAIL-01 的逐项 Requirement→Code→Test→Screenshot/User Acceptance 追踪。
- **Root Cause**：`SOURCE_MISSING`。
- **Locked Target**：最终 Implementation Report 必须逐项列出 `WB-DETAIL-01.1`–`WB-DETAIL-01.11`，各自对应 Requirement、代码、测试、截图/用户验收；任何子项缺失，状态保持 `LOCKED TARGET`，不得写为 IMPLEMENTED。
- **Acceptance Criteria**：实施报告含完整 11 项映射与可复核证据；没有以“已有 Runtime/共享 Agent/历史测试通过”替代新面客 UI/节奏/闭环验收。
- **Affected Active Code**：本条是跨模块证据门槛，覆盖上述所有 affected active files；本轮不修改任何代码。

## WB-MAP-01｜机器人资产与园区空间调度地图

| Field | Value |
| --- | --- |
| ID | WB-MAP-01 |
| Module | Workbench Robot Assets / Campus Spatial Dispatch Map |
| Status | **LOCKED TARGET** |
| Scope | Docs-only delta sync；本轮不修改 frontend、backend、runtime、test、database 或 launcher。 |

> 中央区域是客户/面试官可一眼理解“机器人在哪里、事件在哪里、系统选择谁、准备怎么过去、已经走到哪里”的园区机器人空间调度总览；它不是 SLAM/Fleet/Topology/Backend/Anchor/Interpolation 调试器。所有路线、位置、设施、距离和 ETA 必须来自确定性 backend spatial/runtime facts，禁止前端按 demo ID 写死、LLM 生成或为动画随意连线。

### WB-MAP-01.1｜统一机器人资产卡

- **User Intent**：左侧四台机器人必须以统一网格卡展示正式名称赛特净界 S5、高仙 Omnie、蜗小白 SC50、普渡 FlashBot Max；卡高、图片框、文本起线、状态、电量、位置区域一致。每张默认显示名称、图片、当前状态、电量和客户语言当前位置，不得显示 Robot A/B/C/D、map/zone/internal code。
- **Current Implementation**：`FleetAssetCard` 以纵向列表展示四台资产，卡高和图片框受内容影响；名称/状态/电量存在，但位置只在 hover，默认区域并未提供统一位置行，`FLEET ASSETS` 等英文仍可见。
- **Previous Source Coverage**：D03/P1-A 已锁定正式命名和共享 Fleet；P1-B 已有资产栏，但没有锁定四卡网格与默认五项客户信息。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：默认卡片只以客户语言显示五项信息并统一视觉节奏，内部标识只进入轻量 hover。
- **Acceptance Criteria**：四张卡在同一视图中对齐一致，均显示正式名称、图片、状态、电量、位置；不存在 Robot A/B/C/D 或内部位置码。
- **Affected Active Code**：`frontend/src/components/prototype/SpatialDispatchView.tsx`、`eventViewModel.ts`、`backend/demo_v1/service.py`、`backend/spatial/spatial_data.py`。

### WB-MAP-01.2｜卡片密度与 Hover 边界

- **User Intent**：默认卡增加到恰当业务密度但不成为工程字段堆积；只显示名称、图片、状态、电量、位置。完整能力、SLAM 坐标、Task ID、内部状态等详细信息只在 Hover 中查看。
- **Current Implementation**：默认卡缺少位置，hover 已混合地图 ID、坐标、Task ID、服务范围与能力；卡片整体偏空而详细信息的客户/技术边界未锁定。
- **Previous Source Coverage**：P1-B 有资产栏，P1-F 有共享 Fleet/Task 事实；默认/hover 信息分层缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：默认业务摘要和 hover 详情必须分层，既不稀疏也不默认泄漏工程信息。
- **Acceptance Criteria**：不 hover 即可获得五项业务信息；hover 才出现 SLAM、能力与当前任务，且不出现 JSON/大量内部 ID。
- **Affected Active Code**：`SpatialDispatchView.tsx`、`eventViewModel.ts`。

### WB-MAP-01.3｜被调度机器人的克制突出

- **User Intent**：实际被选择机器人必须以边框/轻量背景/执行状态点/“执行中”等克制企业 SaaS 视觉显著突出，其他保持普通状态；禁止霓虹、强发光、赛博风。
- **Current Implementation**：当前 active card 有轻量 `active` 边框/背景，地图 marker 略缩放；没有把选中、执行状态和最终调度形成完整明确的面客高亮。
- **Previous Source Coverage**：Capability/Scheduler 已锁定唯一 `assignment_decision`；P1-B 未锁定客户层选中状态的视觉优先级。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：只以真实 selected robot/state 驱动克制高亮，不新增选择逻辑或视觉夸张。
- **Acceptance Criteria**：派单后客户无需阅读技术文本即可辨认被选机器人；未选机器人不与其竞争视觉焦点。
- **Affected Active Code**：`SpatialDispatchView.tsx`、`backend/scheduling/scheduler.py`。

### WB-MAP-01.4｜园区调度总览的命名与语言

- **User Intent**：中央区域命名为“园区空间调度”或同义业务中文；3D 园区白模表示跨楼栋/跨楼层调度总览，不得整体称“SLAM地图”（真实 SLAM 是每层 2D 地图）。清理客户层 `FLEET ASSETS`、Fleet、Backend Route、Topology、`PoC模拟状态 · 共享Fleet`、“定位完成后显示后端空间路线”等英文/工程术语；空闲地图保持干净。
- **Current Implementation**：组件仍使用“园区空间调度视图”、`FLEET ASSETS`、共享 Fleet、后端 Dijkstra/拓扑路线、PoC 视觉插值、后端空间路线等技术措辞。
- **Previous Source Coverage**：D05 已锁定 3D 白模与每层 Camera→SLAM 2D map 的实际事实，D02 要求客户中文；客户地图命名和清理清单缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：客户层仅使用业务中文；技术定义仍保留 Advanced，不能通过改名误称 3D 物理/SLAM 事实。
- **Acceptance Criteria**：地图区域无上述英文/工程文案；空闲时仅显示业务必要的机器人与环境，不出现技术路线提示。
- **Affected Active Code**：`SpatialDispatchView.tsx`、`MapCanvas.tsx`、`AdvancedView.tsx`。

### WB-MAP-01.5｜已确认的空间与能力边界

- **User Intent**：未来视觉必须尊重现有六张空间 Map、Camera→SLAM、Global Spatial Graph、Dijkstra `plan_route()`、持久化 Fleet position、电梯和空中连廊节点。蜗小白 SC50 可室内/电梯/连廊并真实支持 Demo03 的 B栋1F→B栋电梯→B栋2F→空中连廊→A栋2F→事件位置；高仙 Omnie 仅 A栋室内、可电梯、不可跨连廊；赛特净界 S5 仅室外，不能进入楼栋/电梯/连廊。
- **Current Implementation**：backend 已有六张 map、四点标定、connector graph、Dijkstra segments、Fleet position 和 capability hard constraints；现有 profiles 已限制 Omnie skybridge=false、S5 outdoor-only、SC50 elevator/skybridge=true。
- **Previous Source Coverage**：P1-A/B、D03/D05 已锁定这些 runtime/能力事实；此前缺少将其提升为客户地图视觉的强制边界。
- **Root Cause**：`SOURCE_MISSING`。
- **Locked Target**：不得为视觉效果越过既有 capability/deployment policy；任何路线展示须反映这些真实约束。
- **Acceptance Criteria**：Demo03 走完整跨楼路径；Demo02 Omnie 仅在 A栋合理区域活动；Demo01 S5 只沿室外道路，三者均无违规穿越。
- **Affected Active Code**：`backend/spatial/spatial_data.py`、`route_planner.py`、`backend/scheduling/capability_engine.py`、`profiles.py`、`frontend/src/components/prototype/SpatialDispatchView.tsx`。

### WB-MAP-01.6｜当前拓扑路线的实现缺口

- **User Intent**：不得因 backend 已有 Dijkstra 就声称真实面客可行走路线已实现。
- **Current Implementation**：`spatialProjection.ts` 的 `CAMPUS_TOPOLOGY_ANCHORS` 把 backend map/node 投影到 3D 白模，再对相邻点线性插值；它能证明跨楼、电梯、连廊的拓扑顺序，但不能充分证明运动沿真实道路中心线、室内走廊、电梯厅或连廊通道。
- **Previous Source Coverage**：P1-B 已实现 Dijkstra connector order + anchor playback，并明确它不是导航遥测；缺少“业务可行走几何”的路线交付标准。
- **Root Cause**：`IMPLEMENTATION_GAP`，并且旧“anchor path 已足够代表面客路线”的视觉结论 **SUPERSEDED BY WB-MAP-01**。
- **Locked Target**：现有 backend topology 继续作为 route order 来源，但不得把 anchor-to-anchor 直线宣传为真实可行走道路。
- **Acceptance Criteria**：在 Waypoint Geometry 落地并经 Demo01/02/03 可视验证前，WB-MAP-01 不得标为 IMPLEMENTED/USER_ACCEPTED。
- **Affected Active Code**：`spatialProjection.ts`、`useRoutePlayback.ts`、`SpatialDispatchView.tsx`、`backend/spatial/route_planner.py`。

### WB-MAP-01.7｜Demo Navigation Waypoint Geometry

- **User Intent**：不要求 ROS Nav2、真实激光 SLAM、动态避障或 production costmap，但未来必须让视觉路线位于业务合理可行走区域。建立统一维护的面客 Demo 级 Navigation Waypoint Geometry，覆盖室外道路、A/B栋1F/2F走廊、电梯入口/出口和空中连廊中心路径；Dijkstra business route 必须投影为合法 waypoint sequence，机器人沿 waypoints 移动，绝不穿墙/穿楼/漂移/直线跨楼。
- **Current Implementation**：当前没有独立的 waypoint geometry data contract；几何锚点散布在 frontend `CAMPUS_TOPOLOGY_ANCHORS`，并以直线段动画。
- **Previous Source Coverage**：D05 明确 Dijkstra 不是 Nav2/local avoidance，P1-B 有 anchor playback；统一 demo route geometry 缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_GAP`。
- **Locked Target**：waypoints 必须作为 Spatial Data / Route Geometry 统一维护，并由确定性 backend route/runtime facts 选择；不是 React 场景特判。
- **Acceptance Criteria**：所有正式 demo 路线由 backend route + 统一 geometry 解析为可审计 waypoint sequence；视觉检查无穿墙、穿楼、道路外漂移或跨楼直线。
- **Affected Active Code**：`backend/spatial/spatial_data.py`、`route_planner.py`、`backend/demo_v1/service.py`、`frontend/src/components/prototype/spatialProjection.ts`、`useRoutePlayback.ts`、`SpatialDispatchView.tsx`。

### WB-MAP-01.8｜路线视觉层级

- **User Intent**：路线必须在白模上明显可见：完整规划路线约 3px 级，已走更深更实，待走较浅/虚线；事件点 > 当前机器人 > 已走路线 > 待走路线，不能被背景吞没。具体像素可按实际比例微调。
- **Current Implementation**：`RouteLayer` 使用约 1.15px 未走虚线和 1.75px 已走实线，路线对比度与层级不足。
- **Previous Source Coverage**：P1-B 已有未走/已走路线和少量箭头；视觉显著性与事件/机器人/路线优先级缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：在不损害 MapCanvas 内层坐标一致性的前提下，建立明显且克制的路线层级。
- **Acceptance Criteria**：在常见桌面视口，客户可不放大地图就看清完整路线、已走段、待走段、事件点和当前 robot 的视觉优先级。
- **Affected Active Code**：`SpatialDispatchView.tsx`、`MapCanvas.tsx`、`spatialProjection.ts`。

### WB-MAP-01.9｜事件点与状态演进

- **User Intent**：事件点需以红色实心中心 + 柔和脉冲外圈和简短业务标签（如“小型垃圾 · 待处理”）强突出；待处理红、处理中橙、验收通过绿/✓，不能只有小“事件位置”文本。
- **Current Implementation**：当前事件 marker 是小红圈和“事件位置”文字，状态不随处理/验收阶段切换，也没有脉冲和业务标签。
- **Previous Source Coverage**：P1-B 已锁定定位后才显示 marker 和最终路线/终点保留；动态业务状态标记缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：颜色/文案仅从真实 event state、event type、verification result 投影，不创造第二状态机。
- **Acceptance Criteria**：在发现、处理中、CLOSED 三个阶段，事件点的颜色/标签清楚反映真实状态；验收通过后可见绿色完成状态。
- **Affected Active Code**：`SpatialDispatchView.tsx`、`eventViewModel.ts`、`backend/demo_v1/service.py`。

### WB-MAP-01.10｜地图机器人 Hover

- **User Intent**：每个地图 robot marker 支持 Hover，轻量透明卡显示正式名称、状态、电量、业务位置、SLAM X/Y、核心清洁能力、当前任务（若有）；不得呈现大量内部 ID、JSON 或调试字段。
- **Current Implementation**：资产栏卡已有 hover，但地图上的 `RobotMarker` 无 hover/信息卡。
- **Previous Source Coverage**：P1-B 有 marker，P1-F 有共享 Fleet/Task 事实；地图 marker hover 的客户信息层缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：hover 值必须读取真实 fleet/task/spatial facts，名称/位置走客户投影。
- **Acceptance Criteria**：所有地图 marker 均可 hover，所见字段与当前 Fleet/Task 一致、无内部 ID/JSON，且卡片不遮蔽核心路线/事件。
- **Affected Active Code**：`SpatialDispatchView.tsx`、`eventViewModel.ts`、`backend/demo_v1/service.py`。

### WB-MAP-01.11｜删除重复右上状态卡

- **User Intent**：地图右上类似“赛特净界 S5 · 行驶中”的独立状态卡默认删除；资产卡、robot marker、事件进度已足够表达，避免重复和视觉悬空。
- **Current Implementation**：地图 navigation 时仍在右上显示 selected robot + 行驶/暂停状态的独立卡。
- **Previous Source Coverage**：P1-B 只要求地图与 Fleet 真实投影，未禁止重复状态卡。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：状态只在指定资产卡/marker/事件进度中表达，除非未来有用户确认的独立业务价值。
- **Acceptance Criteria**：导航时地图右上不再存在重复悬浮状态卡，客户仍能从其它三处明确当前 robot 状态。
- **Affected Active Code**：`SpatialDispatchView.tsx`。

### WB-MAP-01.12｜地图的动态业务过程

- **User Intent**：地图随真实 demo stage 演进：空闲显示四台正常位置且无路线；发现出现事件点；定位锁定事件位置；派单高亮 selected robot 并出现路线；导航沿 waypoints 移动且已走加深；电梯停在真实节点显示“乘梯中”；连廊沿连廊移动；到达停在目标附近；Cleaning 显示清洁中；Verification 保留事件处置状态；CLOSED 变绿完成、路线可逐渐弱化。
- **Current Implementation**：当前有基于 `NAVIGATING` 的 route playback、电梯暂停、target marker 和终态淡化路线，但事件状态、派单高亮、Cleaning/Verification/CLOSED 的完整地图语义未实现。
- **Previous Source Coverage**：P1-B 已覆盖连续插值、电梯提示和终态路线；完整阶段到地图状态编排缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：所有视觉状态只读取已持久化 transition/plan/fleet/verification；不以前端定时器补造业务结果。
- **Acceptance Criteria**：Demo 从空闲至 CLOSED 的每个指定阶段均有可见、真实状态变化，且刷新后可从持久化记录恢复正确视觉状态。
- **Affected Active Code**：`SpatialDispatchView.tsx`、`useRoutePlayback.ts`、`eventViewModel.ts`、`runtimeSession.ts`、`backend/demo_v1/service.py`。

### WB-MAP-01.13｜路径数据真实性与统一维护

- **User Intent**：未来 Route、Waypoint、Distance、Elevator、Skybridge、Start/Target Position 全部来自 backend deterministic spatial/runtime facts。允许 PoC Deterministic Demo Navigation Geometry，但必须统一作为 Spatial Data / Route Geometry 维护，而非散落 React 或 demo-specific branch。
- **Current Implementation**：backend 产生 deterministic `navigation_plan` 的 map/node/segment/cost，前端 projection 没有 demo ID 分支但本地保存 visual anchors、以画布长度决定播放时长；没有受管 waypoint/distance/ETA 数据契约。
- **Previous Source Coverage**：P1-A/B/D05 已禁止 demo ID 固定路线和前端伪造 route；未定义 geometry/distance/ETA 的统一数据所有权。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_GAP`。
- **Locked Target**：保持 backend 为事实源并把 geometry 纳入统一 spatial data；不得让 LLM 或 UI 生成路线事实。
- **Acceptance Criteria**：代码审查可追踪每个显示路线/设施/距离/ETA 到 backend plan/geometry；不存在 demo-specific React 线路、LLM route 或任意动画连线。
- **Affected Active Code**：`backend/spatial/spatial_data.py`、`route_planner.py`、`backend/demo_v1/service.py`、`spatialProjection.ts`、`SpatialDispatchView.tsx`。

### WB-MAP-01.14｜核心用户展示场景

- **User Intent**：用户必须亲眼看到 Demo03 的蜗小白 SC50 从 B栋1F 合理室内路径 → B栋电梯 → B栋2F → 空中连廊 → A栋2F → 事件位置，marker 全程沿路径移动、无瞬移/穿墙/空白直线；Demo02 Omnie 在 A栋合理路线去液体污渍，Demo01 S5 沿园区道路去事件点。
- **Current Implementation**：backend route order 和现有 animation 可以出现 Demo03 连接顺序/电梯停留，但由于 anchor 线性路径，尚不能证明三个场景均沿业务可行走路线运动。
- **Previous Source Coverage**：D05 已锁定 Demo03 connector sequence 和机器人 capability；用户可见的三路线场景验收未建立。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_GAP`。
- **Locked Target**：三条核心路线必须由统一 Waypoint Geometry 和真实 backend plan 驱动。
- **Acceptance Criteria**：Demo01、Demo02、Demo03 的录屏/截图/用户验收逐一展示指定路径；Demo03 五段顺序完整且视觉无非法移动。
- **Affected Active Code**：`backend/spatial/spatial_data.py`、`route_planner.py`、`frontend/src/components/prototype/spatialProjection.ts`、`useRoutePlayback.ts`、`SpatialDispatchView.tsx`。

### WB-MAP-01.15｜验收、用户确认与实施报告

- **User Intent**：未来验收至少覆盖四卡统一布局/五项信息、客户英文技术词清理、robot hover、动态强事件点、明显路线、selected 高亮、backend 来源、Demo01/02/03 合理路线、合法 waypoint 动画、无穿墙/穿楼/漂移与 CLOSED 正确结束。用户未亲眼通过展示前，不得标记 `USER_ACCEPTED`。
- **Current Implementation**：既有 P1-B 测试/浏览器验收覆盖 MapCanvas 内层坐标、拓扑路线、连续插值及电梯停留，不等同本条客户空间总览验收。
- **Previous Source Coverage**：`TODO.md`/测试事实源记录工程验收和用户展示验收待完成，但没有 WB-MAP-01 的逐项证据矩阵。
- **Root Cause**：`SOURCE_MISSING`。
- **Locked Target**：最终 Unified Implementation Report 必须逐项映射 `WB-MAP-01.1`–`.15` 至 Requirement → Code → Test → Screenshot/User Acceptance；任一未完成则 WB-MAP-01 仍为 `LOCKED TARGET`，用户未亲眼通过则不得 `USER_ACCEPTED`。
- **Acceptance Criteria**：报告包含全部 15 项可复核证据，且用户已实际观察 Demo01/02/03 空间展示后才能记录 `USER_ACCEPTED`。
- **Affected Active Code**：本条覆盖上述所有空间、调度、Runtime、frontend projection files；本轮不修改任何代码。

## WB-CAMERA-01｜固定摄像头监控墙与“AI机器人调度大脑”页面表达

| Field | Value |
| --- | --- |
| ID | WB-CAMERA-01 |
| Module | Workbench Camera Monitor Wall / customer-facing page language |
| Status | **LOCKED TARGET** |
| Scope | Docs-only delta sync；本轮不修改 frontend、backend、runtime、test、database 或 launcher。 |

> Workbench 顶部固定摄像头区是客户/面试官理解“园区正在被多个固定摄像头监控、事件画面被突出、清洁后恢复干净”的实时监控墙；不是 CV/YOLO/Evidence Debug 或 Camera 配置页面。受控检测、bbox 和技术证据仍保留给事件详情/Advanced，不能因清理监控墙而破坏真实 evidence 能力。

### WB-CAMERA-01.1｜三路等宽监控墙

- **User Intent**：默认三路等宽 Camera Card 同行展示，视觉尺寸统一、填充均衡；不得继续使用两路超宽 `grid-cols-2` 布局。
- **Current Implementation**：`CameraMonitorGrid` 明确是“两主槽位”，使用 `grid-cols-2`，4:3 图像放入宽槽位产生黑色留白。
- **Previous Source Coverage**：P1-B 已有双监控矩阵和 `object-contain` evidence 规范；三路面客监控墙未被锁定。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：三路卡等宽、等高且同一行；不因事件把第一路放大为主屏。
- **Acceptance Criteria**：常见桌面视口同时显示三路统一卡片，无两路超宽格或大块黑边。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`CameraViewport.tsx`、`eventViewModel.ts`、`data.ts`。

### WB-CAMERA-01.2｜动态三槽位选择

- **User Intent**：无事件显示三路默认重点区域的正常画面；有事件时该主摄像头必须进入第一槽，另两路继续显示其它区域正常画面。选择逻辑可由 Codex 依据 Camera 数据决定，但不得在 React 按 demo ID 堆大量特判。
- **Current Implementation**：`monitorViews()` 只选两路，并根据主 camera 的具体 ID 分支选择；事件主相机虽会进入槽位，但没有动态三槽数据模型。
- **Previous Source Coverage**：P1-B 保证主事件画面与辅助画面隔离，但没有三槽动态调度要求。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：由 Camera/事件事实选择第一主槽及两个正常槽，所有正式事件都可见其事件 camera。
- **Acceptance Criteria**：Demo01–04 中触发 camera 都出现在第一槽，其余两路正常；无事件稳定显示三路默认重点区。
- **Affected Active Code**：`eventViewModel.ts`、`data.ts`、`CameraMonitorGrid.tsx`、`types.ts`。

### WB-CAMERA-01.3｜无事件的正常运营画面

- **User Intent**：没有正在执行的事件时，三路全部显示各自清洁后的正常状态图片，不显示垃圾、检测框、事件前证据或告警。
- **Current Implementation**：当前仅两路；`monitorViews()` 对空闲槽优先使用 `afterImage`，已有“正常画面”的部分能力，但第三槽和完整三路规则不存在。
- **Previous Source Coverage**：P1-B 有 before/after 资产矩阵；无事件三路全正常的业务表达缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：默认园区运营状态必须是三路干净监控图；不得为了展示算法保留异常画面。
- **Acceptance Criteria**：无 event 时三路均为 after/normal 图，且无 overlay、告警标签或事件前对象。
- **Affected Active Code**：`eventViewModel.ts`、`data.ts`、`CameraMonitorGrid.tsx`。

### WB-CAMERA-01.4｜事件前原始画面与无 Overlay

- **User Intent**：事件触发后，事件 camera 显示清洁前真实原始垃圾/污渍/目标画面；监控墙严禁 YOLO 框、识别标签、类别/置信度、bbox 和任何算法 overlay，应像真实监控视频。
- **Current Implementation**：主 camera 在事件中切换为 before asset，但 EDGE_DETECTED 后会把 `detections=true` 传给 `CameraViewport(showDetections=true)`，直接显示 bbox、标签和置信度。
- **Previous Source Coverage**：P1-B/P1-C 已锁定 persisted controlled evidence/overlay 的真实性；从客户监控墙移除 overlay、在详情/Advanced 保留 evidence 的边界缺失。
- **Root Cause**：`IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：Workbench 监控墙永不显示 detection overlay；事件详情/Advanced 可继续基于同一真实 bbox/evidence 审计。
- **Acceptance Criteria**：任何 Demo 的顶部事件前画面可看到原始目标但看不到框、标签、百分比或 bbox；技术视图仍可查证真实检测证据。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`CameraViewport.tsx`、`eventViewModel.ts`、`EventStageEvidence.tsx`、`AdvancedView.tsx`。

### WB-CAMERA-01.5｜事件 Card 状态强调

- **User Intent**：事件待处理为克制红色外框/轻微脉冲，机器人处理中为橙色，AI验收通过短暂绿色，随后恢复普通浅色边框；禁止霓虹、强发光和赛博告警风。
- **Current Implementation**：当前卡主要用右上文字 badge 区分“处置前/后证据”，没有按 event state 的整卡红/橙/绿反馈。
- **Previous Source Coverage**：P1-B 有 stage state 和客户卡颜色，但监控墙状态边框/反馈序列未锁定。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：Card 视觉只读真实 transition/verification state，不创建独立告警状态机。
- **Acceptance Criteria**：Demo 中可依序看见事件红、处理中橙、验收通过短绿、恢复正常；视觉克制且不抢监控图。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`eventViewModel.ts`、`runtimeSession.ts`。

### WB-CAMERA-01.6｜清洁后切换与验收恢复

- **User Intent**：机器人或人工处置完成后，当前 camera 切换对应清洁后图片，随后进入固定摄像头 AI验收；通过后短绿并恢复正常，完整表达“正常→事件→处理中→清洁后→AI验收→正常”。
- **Current Implementation**：`monitorViews()` 在持久化 VERIFYING 后切换事件 camera 为 after asset；但监控卡缺少清晰的清洁后/验收/绿色/恢复完整状态表达。
- **Previous Source Coverage**：P1-A/P1-G 已锁定 before/after 和真实 verification；面客监控墙的切换/反馈生命周期缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：切图和状态必须只依据真实 action/verification Runtime，不伪造验收完成。
- **Acceptance Criteria**：Demo01–04 都可见处置后图先于验收结果；通过后出现短绿并回到正常卡。
- **Affected Active Code**：`eventViewModel.ts`、`CameraMonitorGrid.tsx`、`CameraViewport.tsx`、`backend/demo_v1/service.py`。

### WB-CAMERA-01.7｜Workbench 与技术 Evidence 分层

- **User Intent**：移除 Workbench 监控墙 YOLO Overlay，但不得破坏 Event Detail / Advanced 中真实受控检测 bbox/evidence 能力。
- **Current Implementation**：同一个 `CameraViewport` 的 `showDetections` 用于可视 evidence；顶部墙通过 `detections` 打开，详情通过独立 `CameraEvidence` 使用同一基础组件。
- **Previous Source Coverage**：P1-C/D13 已要求受控 edge 在技术追溯中如实呈现；没有为不同产品场景建立显示策略。
- **Root Cause**：`IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：监控墙与 Evidence/Advanced 必须拥有不同的显示模式，底层 bbox 数据和技术验收不受影响。
- **Acceptance Criteria**：Workbench 无 overlay；Event Detail/Advanced 的真实 bbox/证据验证仍可用且未被删除。
- **Affected Active Code**：`CameraViewport.tsx`、`CameraMonitorGrid.tsx`、`EventStageEvidence.tsx`、`AdvancedView.tsx`、`eventViewModel.ts`。

### WB-CAMERA-01.8｜监控墙与 Evidence 的画面填充策略

- **User Intent**：面客监控墙允许等比例 `cover` 和合理裁切以铺满画面，不拉伸、不留大片黑边；Evidence/Advanced 继续完整原图比例和 bbox 坐标一致性，不能用同一 Viewport 策略强行兼顾两种场景。
- **Current Implementation**：`CameraViewport` 计算 4:3 image plane 并使用 `object-contain`，即使 `fill` 仍维持 letterbox；这满足 evidence 坐标但不满足监控墙。
- **Previous Source Coverage**：P1-B 已锁定 evidence/overlay 坐标一致性；产品场景的 cover 与 evidence contain 分离缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：实现独立 customer monitoring mode 与 evidence/advanced mode，均不得拉伸或伪造 asset。
- **Acceptance Criteria**：三路监控图无明显黑边或形变；Evidence/Advanced 的原图/bbox 对齐保持正确。
- **Affected Active Code**：`CameraViewport.tsx`、`CameraMonitorGrid.tsx`、`EventStageEvidence.tsx`、`AdvancedView.tsx`。

### WB-CAMERA-01.9｜极简监控信息

- **User Intent**：每路默认仅显示左下业务地点、正中半透明播放按钮、右下实时动态时间；不得默认显示 Camera ID、空闲/前后证据、controlled/LIVE evidence 等技术标签。
- **Current Implementation**：当前显示左上 Camera ID、右上“空闲画面/处置前证据/处置后证据”、左下地点；没有中心播放按钮或右下时间。
- **Previous Source Coverage**：P1-B 监控矩阵已经有地点/资产标识；极简三位置信息布局缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：客户只见地点、播放视觉入口和时间；技术身份进入 Advanced/Technical Detail。
- **Acceptance Criteria**：三卡信息位置一致，只有地点/播放按钮/HH:mm:ss；无 Camera ID、Evidence、前后处理技术文字。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`CameraViewport.tsx`、`eventViewModel.ts`。

### WB-CAMERA-01.10｜半透明播放视觉入口

- **User Intent**：恢复画面正中半透明播放按钮，风格像真实监控系统、不过度抢画面；它可以是视觉状态入口，不要求伪造 RTSP 播放控制。
- **Current Implementation**：顶部监控卡没有中心播放按钮。
- **Previous Source Coverage**：P1-B 没有监控播放视觉要求，且当前是静态 PoC asset。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：只实现视觉入口，不声称真实 RTSP 或摄像机控制。
- **Acceptance Criteria**：每卡视觉中心有轻量半透明播放按钮，且不阻碍事件画面/状态边框。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`CameraViewport.tsx`。

### WB-CAMERA-01.11｜动态监控时间

- **User Intent**：每卡右下显示低干扰、每秒刷新 `HH:mm:ss` 的前端展示时间；不需解释或伪造摄像机原始 OSD timestamp。
- **Current Implementation**：`CameraViewport` 与 `CameraMonitorGrid` 没有动态时钟。
- **Previous Source Coverage**：P1-A/B 仅锁定 SQLite business transition timestamp，不包含监控产品氛围时钟。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：展示时间仅作监控产品感，不进入 Runtime/审计事实。
- **Acceptance Criteria**：三路均在右下显示并每秒变化的 `HH:mm:ss`，不影响真实事件时间线。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`CameraViewport.tsx`。

### WB-CAMERA-01.12｜简化监控标题区

- **User Intent**：标题区默认只保留“固定摄像头监控”；可有极短业务状态，不得保留“2路重点区域 · 受控摄像头证据”等解释小字。
- **Current Implementation**：标题下仍显示“2 路重点区域 · 受控摄像头证据”。
- **Previous Source Coverage**：P1-B 已标明证据边界；该技术说明不应再占客户标题区。
- **Root Cause**：`IMPLEMENTATION_DIVERGENCE`；旧标题说明 **SUPERSEDED BY WB-CAMERA-01**。
- **Locked Target**：技术 evidence 说明转入 Advanced/Detail，顶部保持干净。
- **Acceptance Criteria**：标题区无双路、受控证据等灰字，客户默认只看到“固定摄像头监控”。
- **Affected Active Code**：`CameraMonitorGrid.tsx`。

### WB-CAMERA-01.13｜Workbench 顶部去重

- **User Intent**：顶部只保留页面名称“AI机器人调度大脑”，删除客户层的“机器人正在前往”、LIVE、STABLE REPLAY、运行状态和技术模式说明；事件状态由墙、地图、详情共同表达。
- **Current Implementation**：`PrototypeWorkbench` 顶部同时显示旧页面名、stageCopy 状态和 LIVE/STABLE REPLAY badge。
- **Previous Source Coverage**：P1-A/D13 锁定 Runtime/Replay 可观测性，但应由 Advanced 承担；Workbench header 去重缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：Runtime mode/状态并未删除，只从客户 Header 移至 Advanced/其它锁定面客投影。
- **Acceptance Criteria**：Workbench header 仅呈现“AI机器人调度大脑”，不再含运行状态或 LIVE/Replay 标识。
- **Affected Active Code**：`PrototypeWorkbench.tsx`、`data.ts`、`AdvancedView.tsx`。

### WB-CAMERA-01.14｜客户可见名称统一

- **User Intent**：所有客户可见的“自主清洁工作台”统一为“AI机器人调度大脑”，包括左导航、页面 Header、空状态、跳转入口、帮助/面客标签与其它引用；内部 `PrototypeWorkbench` / route 不需无价值重构。
- **Current Implementation**：左侧导航和 Header 仍为“自主清洁工作台”，其它场景/帮助文字也保留旧名称。
- **Previous Source Coverage**：D02 锁定一级导航旧名称；该客户文案被本条新名称 **SUPERSEDED BY WB-CAMERA-01**。
- **Root Cause**：`IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：只替换客户文案，不要求为名称进行内部组件/路由重构。
- **Acceptance Criteria**：全站客户可见 Workbench 名称一致为“AI机器人调度大脑”，搜索/验收无旧客户名称残留。
- **Affected Active Code**：`PrototypeWorkbench.tsx`、`CameraMonitorGrid.tsx`、`EventDetailPanel.tsx`、`data.ts`、客户文案相关组件。

### WB-CAMERA-01.15｜监控墙客户语言

- **User Intent**：监控墙与 Workbench Header 不出现 LIVE、FLEET、CONTROLLED EVIDENCE、Backend、Replay、Camera Evidence 等客户无须理解的英文/技术词；除品牌/不可避免专有名词外优先业务中文，技术信息统一进 Advanced。
- **Current Implementation**：监控墙和 Header 直接显示 Camera ID、Evidence、LIVE/Replay 等；空间卡也有 Fleet/Backend 等技术词。
- **Previous Source Coverage**：D02 概括客户中文、D13 锁定 Advanced 技术透明；具体监控墙/Header 清理清单缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：保持真实技术事实但将其放到正确技术页面，面客主界面使用业务中文。
- **Acceptance Criteria**：客户监控墙/Header 无该类工程词；Advanced 仍可看到真实技术事实。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`CameraViewport.tsx`、`PrototypeWorkbench.tsx`、`SpatialDispatchView.tsx`、`AdvancedView.tsx`。

### WB-CAMERA-01.16｜低干扰演示控制

- **User Intent**：右上“…”中的 Demo Operator Control 可保留，但客户正常观看时不突出；它不是客户业务功能，默认界面保持干净。
- **Current Implementation**：现有“…”已经承载演示控制，默认收起，符合低干扰方向。
- **Previous Source Coverage**：P1-B 有四个 Demo 触发矩阵，但未明确定义客户与操作员入口层级。
- **Root Cause**：`SOURCE_MISSING`（保留现有能力但需锁定边界）。
- **Locked Target**：演示控制保持二级入口；不得扩展为默认业务操作面板。
- **Acceptance Criteria**：正常观看时只见低干扰“…”；打开后才显示 Demo Operator Control，且不影响三路监控布局。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`PrototypeWorkbench.tsx`。

### WB-CAMERA-01.17｜三槽位的统一视觉

- **User Intent**：三路 Camera Card 高度、宽度、裁切、地点、时间、播放按钮位置完全一致；事件主槽仅靠状态边框与画面内容强调，不能把第一路巨大化或其余两路缩小。
- **Current Implementation**：目前只有两路，均缺播放/时间，故三槽统一性尚不存在。
- **Previous Source Coverage**：P1-B 有双监控矩阵，不包含三槽尺寸/信息定位规范。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：一套一致 Camera Card layout，主槽不改变尺寸。
- **Acceptance Criteria**：三槽等宽等高、裁切和三项信息位置一致；事件强调不改变版式比例。
- **Affected Active Code**：`CameraMonitorGrid.tsx`、`CameraViewport.tsx`。

### WB-CAMERA-01.18｜四个 Demo 的完整监控状态循环

- **User Intent**：用户必须能见到无事件三路正常 → Demo01 主 camera 原始垃圾图/无框/红卡 → 处理中橙 → 清洁后图 → AI验收通过短绿 → 正常；Demo02/03/04 完全遵循同一状态逻辑。
- **Current Implementation**：before/after asset 与真实 Verification 已存在，但当前双槽、bbox overlay、技术 badge 和缺失状态卡反馈无法满足统一客户循环。
- **Previous Source Coverage**：P1-A/B/C/G 有全部 Runtime/证据/验证事实；监控墙四 Demo 生命周期验收缺失。
- **Root Cause**：`SOURCE_MISSING` + `IMPLEMENTATION_DIVERGENCE`。
- **Locked Target**：四个 Demo 共享同一 camera-state projection，结果只从真实 Runtime state/verification 产生。
- **Acceptance Criteria**：用户可逐一见证 Demo01–04 的完整循环，任何 Demo 都不显示 bbox 或跳过真实验收状态。
- **Affected Active Code**：`eventViewModel.ts`、`CameraMonitorGrid.tsx`、`CameraViewport.tsx`、`PrototypeWorkbench.tsx`、`backend/demo_v1/service.py`。

### WB-CAMERA-01.19｜验收、用户确认与实施报告

- **User Intent**：未来至少验收三路同排、无黑边、无事件全 after、事件 before 原图无 bbox、红/橙/绿状态、播放按钮、动态时钟、极简地点信息、标题清理、统一“AI机器人调度大脑”、Header 去重、四 Demo 同循环。用户未亲眼通过前不得 `USER_ACCEPTED`。
- **Current Implementation**：既有 P1-B 监控/图片/Evidence 测试与浏览器验收不等同 WB-CAMERA-01 的面客监控墙验收。
- **Previous Source Coverage**：`TODO.md`/测试事实源记录工程验收与用户展示验收待完成，但没有本条逐项 evidence matrix。
- **Root Cause**：`SOURCE_MISSING`。
- **Locked Target**：最终 Unified Implementation Report 必须逐项列出 `WB-CAMERA-01.1`–`.19` 的 Requirement → Code → Test → Screenshot/User Acceptance；任何子项未完成不得 IMPLEMENTED，用户未亲眼验收不得 USER_ACCEPTED。
- **Acceptance Criteria**：Implementation Report 含全部 19 项可复核证据，用户观察四 Demo 监控循环后才可记录 `USER_ACCEPTED`。
- **Affected Active Code**：本条覆盖上述 Workbench/customer/technical evidence files；本轮不修改任何代码。
