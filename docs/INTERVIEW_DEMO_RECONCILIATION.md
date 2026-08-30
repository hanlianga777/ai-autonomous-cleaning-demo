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
