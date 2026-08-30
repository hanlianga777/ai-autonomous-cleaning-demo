# AI 自主清洁 Demo｜真实任务清单

> **状态：LOCKED · 2026-08-30**
> `[x]` 仅代表满足对应验收条件；`[ ]` 包含尚未实现或尚未验收的 LOCKED TARGET。Unified Implementation 已授权，P1-A 工程验收通过；独立提交推送后进入 P1-B，后续阶段仍逐阶段验收提交。

## 已实现基线（IMPLEMENTED，禁止回退）

- 阶段 REST Runtime、SQLite transition audit、Cloud/assign/verify 边界、旧 `/runs/*` 410。
- 受控 bbox、真实 Qwen transport、独立二审/Fusion、Phase 2 空间基础、Phase 3 Capability/Scheduler、Dijkstra global topology planner / `plan_route()`。
- 基础 Multi-view LangGraph、基础 Event Center、Analytics 聚合、确定性 Optimization recommendation 与 Advanced shell 已存在；它们均不等于本文件其余 LOCKED 产品目标。
- Demo01、Demo02、Demo04 的既有真实运行记录；Demo03 当前为 `HUMAN_REVIEW`，不能视为闭环成功。

## P1-A｜真实清洁 Runtime 与产品名称（先完成）

**Closure 状态：IMPLEMENTED · Reviewer A/E PASS。** 真实 Demo01/Demo04 LIVE→persist→Replay 均闭环；此前 Demo04 业务语义阻塞已由用户确认的 scoped metadata 解除，未更改模型结果或能力/调度规则。

- [x] Demo04 业务事实确认、metadata→Scenario/Camera/Zone context→一/二审透传与持久化、模型 veto 不覆盖、旧 context Replay 拒绝、真实 LIVE→Replay 人工闭环。
- [x] Reviewer A/E 最终 PASS，完整测试/构建和六文档一致性核查通过；按独立 P1-A commit/push 交付。
- [ ] P2 后续强化：Fleet/event/transition 跨表原子事务与多请求并发保护；route error 的 assigned reservation 释放；旧 Phase 3 fixtures 静态 map 兼容兜底；API/browser E2E；主工作台外静态旧机器人名称清理；秒级 timestamp 精度与根目录测试相对路径可移植性；P1-H 统一错误层级。不能把多用户/进程崩溃中途原子恢复宣称已经验收。旧合成 replay 已删除，不再作为遗留项。

- [x] **共享 Fleet / 活跃 Runtime 命名投影**：内部 ID 不变；共享 Fleet 与当前事件候选使用四个正式客户名称，Product Capability 与 Demo Configuration 分开。非活跃旧 UI 文案清理留 P2；未来 Analytics/Task/Action Card 的全产品投影随对应阶段完成。
- [x] **Camera→SLAM Runtime 接入**：`locate` 从主 bbox 计算接地点，调用 `map_pixel_to_slam()`，持久化 map/x/y/building/floor/zone；marker 只在定位后出现，客户/Advanced 按锁定层级显示。
- [x] **Dijkstra global topology planner / `plan_route()` Runtime 接入**：`start-navigation` 读取共享 Fleet 当前 map 与已定位 target map，调用 `plan_route()`，将 connector graph 转为可视 anchor path；删除 demo_id 固定路径。
- [x] **Demo04 正确能力边界**：移除 cloud 阶段大件直接人工特判；完整运行 Cloud → Locate → Capability Engine → zero candidate → `HUMAN_FALLBACK` → 人工完成 → verify。
- [x] **共享 Fleet 状态与真实时间**：机器人位置、电量、状态使用同一读模型；任务终点保留，new demo/reset 才复位；前端读取 SQLite transition timestamp、真实 duration、真实 cloud latency。
- [x] **Stable Replay 重定义**：只保存/选择既有真实 AI structured evidence 回放，其他 Runtime 阶段仍真实执行；在现有 Advanced shell 加最小 AI Runtime 控制区，提供 LIVE / Stable Replay 主动选择、云端模型可用状态、最近请求状态和 latency；不得重做完整 Advanced 页面。

## P1-B｜Workbench、MapCanvas 与 EventDetailPanel

- [ ] **唯一 MapCanvas**：建立 `object-contain` 内层画布转换；SLAM white model、anchor、route、marker、A/B/C/D 机器人统一投影，修复 letterbox 漂移。
- [ ] **机器人执行体验**：真实 anchor path 连续插值；未走/已走路线、小 marker、少量箭头；蜗小白 SC50 在电梯入口停约 1 秒并显示“乘梯中”；CLOSED / HUMAN_REVIEW 保留终点和路线。
- [ ] **布局与双监控矩阵**：实现 72/28、31/69、右详情独立滚动、145–155px 资产栏、相机 `object-contain` 规范；四个 Demo before/after 状态矩阵；Demo02 补充图永不替换顶部监控。
- [ ] **统一 EventDetailPanel**：实现 `mode="live"` / `mode="history"`；实时自动跟随一次 smooth scroll，历史只读不滚动、不重跑；统一字段、卡片、颜色、stage hierarchy、历史 snapshot。
- [ ] **客户表达收敛**：全量 enum 中文化；云端 raw confidence、Fusion “N分”、系统决策分层；客户层不展示 raw next_action / 公式 / Chain-of-Thought。

## P1-C｜新 Multi-view Perception Agent

- [ ] **Single-view Cloud schema 与 Gate 顺序**：第一次仅输入主视角、YOLO bbox/detection、必要 Camera Context；输出 `event_type`、`need_action`、`confidence`、`evidence_sufficient`、`ambiguity_type`。Evidence Sufficiency Gate 优先于最终 confidence disposition：可恢复不足先补证，最终充分 evidence 才进入 `>=0.85` / `0.50 <= confidence < 0.85` / `<0.50` 处置。
- [ ] **Evidence acquisition Agent**：以 `tool_choice=auto` 实现 `find_supporting_cameras()`、`fetch_camera_evidence()`、`finish_visual_judgment()` 等价工具；当证据不足、歧义可由额外视角缓解且存在合法 camera 时，模型自主选择补证摄像头，最多 2 路、最多 2 rounds；无合法 camera、fetch 失败或最终仍不充分则 `HUMAN_REVIEW`，不允许 demo_id 或固定 confidence branch。
- [ ] **PoC Evidence Adapter、二审与审计**：明确 controlled evidence assets，不伪称真实 RTSP 同步；持久化 Agent Start、single-view result、sufficiency、ambiguity、tool call、candidates、selected cameras、fetch、multi-view result、final decision、latency。最终 `0.50 <= confidence < 0.85` 的 independent second review 可读取合法 evidence set，但不读取上一轮模型答案或 reasoning。
- [ ] **Demo02 真实演示**：CAM-A1-01 单视角的液体/反光歧义必须由模型自己发起 Tool Call；补充图来自 tool audit，客户只显示 Tool Calls、Evidence、Selected Cameras、Final Confidence、Decision，不显示 Chain-of-Thought。

## P1-D｜Event Center（AI 事件处置档案中心）

- [ ] **统一事件索引与状态映射**：同一 CleaningEvent / SQLite；全部、处理中、已自主闭环、待人工处理、异常五类状态；正常 `HUMAN_FALLBACK` 不得归为异常。
- [ ] **搜索、筛选与两级 List**：支持 Event Type、Camera ID、Building/Floor、Robot Name、Event ID、时间范围、事件类型、处置方式；默认倒序、新事件不抢占当前历史详情。
- [ ] **History Detail Drawer 与 URL State**：右侧 42–46% `EventDetailPanel(mode="history")`；`/events?event=...` 可恢复选择；首次进入不自动选中；切换内容不闪烁。
- [ ] **read-only trace 边界**：不做删除、批量状态修改、批量派发、CSV/Excel 导出或其他批量运营动作。

## P1-E｜Analytics（AI 自主清洁运营分析中心）

- [ ] **可追溯 Analytics data model**：结构化 30 天 Seed History + 当前 Runtime CleaningEvent Increment；明确“近30天 · 演示历史数据”；真实计算 event/transition-derived 指标，移除固定 response/closure/utilization 与虚构趋势。
- [ ] **5 KPI**：实现并记录有效事件 denominator：自主闭环率、人工介入率、首次处置成功率、平均响应时间、平均闭环时间；处理中/系统异常处理规则可审计。
- [ ] **Campus Spatial Event Heatmap**：用 map_id/x/y/event_type/timestamp 聚合，复用 SLAM white model；实现 type/time filters、热点 drill-down、跳转 Event Center 的 location/type/time URL filter。
- [ ] **辅助分析**：事件结构、区域/时段规律、清洁机器人运营效率；FlashBot Max 不进清洁利用率排名；利用率必须由任务状态时间 ÷ 可用时间计算。

## P1-F｜Robot Operations Agent 与配送扩展基础

- [ ] **Agent runtime / Policy Guard / Audit**：实现白名单 Read Tools、低风险 Action Tools、代码级禁止 Write Tools、Observe/Replan/Close 与 Action Audit；不得产生 Scheduler / Dijkstra / Heatmap / RAG 等额外 Agent。
- [ ] **Task 与 Action Card**：实现 Cleaning / Delivery / Relocation Standby Task；POI 白名单；真实 backend Task ID 与 Fleet/Workbench/Agent 共享同一状态；Agent 不直接操作底盘坐标。
- [ ] **一个 Agent、两种 UI 与真实语音边界**：Workbench/Event Center 共享可拖动浮窗；无已保存位置默认左下角，localStorage 位置优先，Header/Drag Handle 拖动、viewport 限制、展开/收起/跨页/刷新保持。Analytics 固定右侧 Panel；共享 session / messages / audit / Page Context。语音链路为 Microphone → real ASR → transcript；只有已配置 ASR provider 才能启用麦克风，未配置时 disabled 或显示“语音服务未配置”，禁止预设文本、timer、mock transcript 或 fake animation。
- [ ] **Analytics Advice**：成为 Robot Operations Agent 的只读能力，最多 3–4 Read Tool calls、3–4 条含数据依据的建议；默认 snapshot，用户点击才重新生成；不自动改变运营配置。
- [ ] **Delivery Adapter boundary**：FlashBot Max Demo Fleet / DeliveryTask state machine 可未来实现；外部平台仅在合法授权后接入，未授权显示 `ADAPTER READY` / `AUTH REQUIRED`，不得伪造 webhook / callback。

## P1-G｜验收、回归与文档纪律

- [ ] **Demo01/03/04 LIVE + Replay 回归**：按 `AI_INTEGRATION_TEST.md` 的次数与字段记录 raw confidence、二审、Fusion、system decision、robot、route、verification、final、latency。
- [ ] **Demo02 LIVE Agent 回归**：连续 5 次中至少 4 次由模型真实触发 Multi-view Tool Calling，经 search → fetch → multi-view Cloud → 高仙 Omnie → verification → CLOSED；严禁 demo_id、固定阈值或前端动画作弊。
- [ ] **Event / Analytics / Agent 回归**：历史 snapshot 不被当前 Fleet 覆盖；状态分类与 URL 恢复正确；Analytics 无硬编码 KPI；Action Card / Policy Guard / Audit 与 Delivery Adapter 授权状态可验证。
- [ ] **实现后文档更新**：仅在代码、测试、浏览器证据和用户验收都存在时，将对应 TODO 转为 IMPLEMENTED，并更新六份事实源。

## P1-H｜Advanced Technical Observability（Batch C）

- [ ] **Trace Inspector layout**：在现有 Advanced shell 上实现浅色 read-mostly Technical Observability & Execution Trace Inspector；顶部 Runtime Strip，左 62–65% Execution Trace、右 35–38% Selected Node Detail，交互为 Trace → Node → Inspect；不做配置后台、黑客终端或满屏 JSON。
- [ ] **AI Recognition 6-stage Trace**：投影 Edge、Single-view Cloud、conditional Multi-view Agent、Multi-view Cloud、Business Decision/Fusion、Verification；未触发 Multi-view 如实显示 `NOT_TRIGGERED / EVIDENCE_ALREADY_SUFFICIENT`，不伪造调用或固定 confidence。
- [ ] **Multi-view Agent / unified Tool Trace**：统一展示 tool、`MODEL_TOOL_CALL` / `SYSTEM_WORKFLOW` / `USER_ACTION`、start time、duration、status、input/result summary；Demo02 可审计 single-view insufficiency、candidate、selected camera、fetch、final judgment，不显示 Chain-of-Thought。
- [ ] **Source / Reality badges 与 Reality Matrix**：统一 `LIVE MODEL`、`DETERMINISTIC RUNTIME`、`CONTROLLED EVIDENCE`、`POC SIMULATION`、`REPLAY`、`AUTH REQUIRED / NOT CONNECTED`；Reality Matrix 覆盖 AI、空间、调度、机器人、电梯/Skybridge、验证、Replay、Delivery、ASR，并由 Runtime facts 自动决定，用户不可手改。
- [ ] **空间、能力、调度、路线 Inspector**：展示 Camera→SLAM 4-point homography / u-v / map-x-y、TaskProfile 与 Capability 硬约束、Scheduler factors / AssignmentDecision、Dijkstra global topology route 与 Demo03 Skybridge；不宣称 Nav2 或真实局部避障。
- [ ] **Runtime / Model / Error / Recovery Inspector**：实现 LIVE/Replay strip、真实 provider/model/request/latency、错误 taxonomy、Policy Guard recovery audit、LIVE failure no silent Replay；不泄漏任何 secret。
- [ ] **Trace ID、PoC Boundaries 与 Adapter Points**：以独立 Trace ID 串联 Event / AgentTask / Tool / model / task runtime；展示当前 PoC boundary、future Evidence/Robot/Delivery/ASR/Elevator Adapter replacement point；Advanced 只读真实 Runtime Records，绝不独立重跑模型、Scheduler 或 Route Planner。
- [ ] **Advanced acceptance**：完成 `AI_INTEGRATION_TEST.md` 的 Demo01–04 Trace、Reality Badge、Runtime/Error、sensitive-data 检查；必须证明无 fake trace/tool/latency/error/badge/status。

## 后续 Batch（不在 Unified Implementation Batch 的范围）

- [ ] 在 P1-H 完成并验收后，才另行讨论 Advanced 的非必要增强体验；不得稀释已锁定的四模块 Trace Inspector 范围。
- [ ] 经授权的真实 RTSP/VMS/NVR、生产机器人/电梯/门禁与外部配送平台 Adapter。
- [ ] **Batch C / Part 3 Advanced**：方案已 `LOCKED/TODO`，由 P1-H 承载；Unified Implementation 已授权，但须按阶段依赖在 P1-H 实施。

## 不在授权范围

- ROS 2、Nav2/Open-RMF runtime、Docker/K8s、Kafka/Redis/PostgreSQL、真实机器人/电梯/门禁、真实本地 YOLO 主链路。
- 让 LLM 或任一 Agent 修改 SLAM/禁行区/清洁范围/巡检范围/机器人能力/Camera Coverage/标定/Scheduler policy/自动处置阈值/安全速度/门禁或电梯权限。
