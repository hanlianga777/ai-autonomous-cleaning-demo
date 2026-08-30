# Interview Demo Reconciliation

> 本文件记录最新用户确认需求与历史事实源、当前 active implementation 的对齐关系。
> 优先级：最新用户明确确认需求 > 本文件的 `LOCKED TARGET` > `DECISIONS.md` / `ARCHITECTURE.md` > 旧 `IMPLEMENTED` 描述 > 当前代码实际行为。

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
