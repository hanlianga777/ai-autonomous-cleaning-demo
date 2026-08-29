# AI 自主清洁 Demo｜真实任务清单

> **状态：LOCKED · 2026-08-30**
> `[x]` 仅代表代码与技术验证已存在；`[ ]` 是已确认但尚未实现的 LOCKED TARGET。本轮是 docs-only：本文件的所有 `[ ]` 均未获 implementation 授权。

## 已实现基线（IMPLEMENTED，禁止回退）

- 阶段 REST Runtime、SQLite transition audit、Cloud/assign/verify 边界、旧 `/runs/*` 410。
- 受控 bbox、真实 Qwen transport、独立二审/Fusion、Phase 2 空间基础、Phase 3 Capability/Scheduler、Dijkstra global topology planner / `plan_route()`。
- 基础 Multi-view LangGraph、基础 Event Center、Analytics 聚合、确定性 Optimization recommendation 与 Advanced shell 已存在；它们均不等于本文件其余 LOCKED 产品目标。
- Demo01、Demo02、Demo04 的既有真实运行记录；Demo03 当前为 `HUMAN_REVIEW`，不能视为闭环成功。

## P1-A｜真实清洁 Runtime 与产品名称（先完成）

- [ ] **客户机器人命名投影**：保持 `robot-a` / `robot-b` / `robot-c` / `robot-d` 内部 ID；全客户 UI、Event、Analytics、Task、Action Card 改为赛特净界 S5、高仙 Omnie、蜗小白 SC50、普渡 FlashBot Max。能力呈现必须分开 Product Capability 与 Demo Configuration。
- [ ] **Camera→SLAM Runtime 接入**：`locate` 从主 bbox 计算接地点，调用 `map_pixel_to_slam()`，持久化 map/x/y/building/floor/zone；marker 只在定位后出现，客户/Advanced 按锁定层级显示。
- [ ] **Dijkstra global topology planner / `plan_route()` Runtime 接入**：`start-navigation` 读取共享 Fleet 当前 map 与已定位 target map，调用 `plan_route()`，将 connector graph 转为可视 anchor path；删除 demo_id 固定路径。
- [ ] **Demo04 正确能力边界**：移除 cloud 阶段大件直接人工特判；完整运行 Cloud → Locate → Capability Engine → zero candidate → `HUMAN_FALLBACK` → 人工完成 → verify。
- [ ] **共享 Fleet 状态与真实时间**：机器人位置、电量、状态使用同一读模型；任务终点保留，new demo/reset 才复位；前端读取 SQLite transition timestamp、真实 duration、真实 cloud latency。
- [ ] **Stable Replay 重定义**：只保存/选择既有真实 AI structured evidence 回放，其他 Runtime 阶段仍真实执行；在现有 Advanced shell 加最小 AI Runtime 控制区，提供 LIVE / Stable Replay 主动选择、云端模型可用状态、最近请求状态和 latency；不得重做完整 Advanced 页面。

## P1-B｜Workbench、MapCanvas 与 EventDetailPanel

- [ ] **唯一 MapCanvas**：建立 `object-contain` 内层画布转换；SLAM white model、anchor、route、marker、A/B/C/D 机器人统一投影，修复 letterbox 漂移。
- [ ] **机器人执行体验**：真实 anchor path 连续插值；未走/已走路线、小 marker、少量箭头；蜗小白 SC50 在电梯入口停约 1 秒并显示“乘梯中”；CLOSED / HUMAN_REVIEW 保留终点和路线。
- [ ] **布局与双监控矩阵**：实现 72/28、31/69、右详情独立滚动、145–155px 资产栏、相机 `object-contain` 规范；四个 Demo before/after 状态矩阵；Demo02 补充图永不替换顶部监控。
- [ ] **统一 EventDetailPanel**：实现 `mode="live"` / `mode="history"`；实时自动跟随一次 smooth scroll，历史只读不滚动、不重跑；统一字段、卡片、颜色、stage hierarchy、历史 snapshot。
- [ ] **客户表达收敛**：全量 enum 中文化；云端 raw confidence、Fusion “N分”、系统决策分层；客户层不展示 raw next_action / 公式 / Chain-of-Thought。

## P1-C｜新 Multi-view Perception Agent

- [ ] **Single-view Cloud schema**：第一次仅输入主视角、YOLO bbox/detection、必要 Camera Context；输出 `event_type`、`need_action`、`confidence`、`evidence_sufficient`、`ambiguity_type`，且 confidence 不等于 evidence sufficiency。
- [ ] **Evidence acquisition Agent**：以 `tool_choice=auto` 实现 `find_supporting_cameras()`、`fetch_camera_evidence()`、`finish_visual_judgment()` 等价工具；模型自主选择补证摄像头，最多 2 路、最多 2 rounds；不允许 demo_id 或固定 confidence branch。
- [ ] **PoC Evidence Adapter 与审计**：明确 controlled evidence assets，不伪称真实 RTSP 同步；持久化 Agent Start、single-view result、sufficiency、ambiguity、tool call、candidates、selected cameras、fetch、multi-view result、final decision、latency。
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
- [ ] **一个 Agent、两种 UI**：Workbench/Event Center 可拖动浮窗（viewport 与 localStorage 规则），Analytics 固定右侧 Panel；共享 session / messages / audit / Page Context；语音仅预留 real ASR → transcript 接入，禁止 fake animation。
- [ ] **Analytics Advice**：成为 Robot Operations Agent 的只读能力，最多 3–4 Read Tool calls、3–4 条含数据依据的建议；默认 snapshot，用户点击才重新生成；不自动改变运营配置。
- [ ] **Delivery Adapter boundary**：FlashBot Max Demo Fleet / DeliveryTask state machine 可未来实现；外部平台仅在合法授权后接入，未授权显示 `ADAPTER READY` / `AUTH REQUIRED`，不得伪造 webhook / callback。

## P1-G｜验收、回归与文档纪律

- [ ] **Demo01/03/04 LIVE + Replay 回归**：按 `AI_INTEGRATION_TEST.md` 的次数与字段记录 raw confidence、二审、Fusion、system decision、robot、route、verification、final、latency。
- [ ] **Demo02 LIVE Agent 回归**：连续 5 次中至少 4 次由模型真实触发 Multi-view Tool Calling，经 search → fetch → multi-view Cloud → 高仙 Omnie → verification → CLOSED；严禁 demo_id、固定阈值或前端动画作弊。
- [ ] **Event / Analytics / Agent 回归**：历史 snapshot 不被当前 Fleet 覆盖；状态分类与 URL 恢复正确；Analytics 无硬编码 KPI；Action Card / Policy Guard / Audit 与 Delivery Adapter 授权状态可验证。
- [ ] **实现后文档更新**：仅在代码、测试、浏览器证据和用户验收都存在时，将对应 TODO 转为 IMPLEMENTED，并更新六份事实源。

## 后续 Batch（不在本轮 implementation scope）

- [ ] Advanced 完整产品化与深度技术 trace 体验。
- [ ] 经授权的真实 RTSP/VMS/NVR、生产机器人/电梯/门禁与外部配送平台 Adapter。
- [ ] **Batch C / Part 3 pending discussion**：尚未完整讨论，禁止自行定义范围或实施。

## 不在授权范围

- ROS 2、Nav2/Open-RMF runtime、Docker/K8s、Kafka/Redis/PostgreSQL、真实机器人/电梯/门禁、真实本地 YOLO 主链路。
- 让 LLM 或任一 Agent 修改 SLAM/禁行区/清洁范围/巡检范围/机器人能力/Camera Coverage/标定/Scheduler policy/自动处置阈值/安全速度/门禁或电梯权限。
