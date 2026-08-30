# AI 自主清洁 Demo｜当前架构与锁定目标

> **状态：IMPLEMENTED · Post-merge Interview Freeze · 2026-08-30**
> Unified Implementation merge baseline: `8341eb079fe5a700b4931e0112fdbe5552297785`
> Current main HEAD: 以 GitHub main / `git rev-parse HEAD` 为准
> 历史实施分支 `codex/unified-implementation` / `bdd08e02e0e4fc96d9ad6229949f2c8bf3812136` 仅作历史记录。
> 本文同时表达代码事实与下一实现目标；没有明确标为 IMPLEMENTED 的内容均不可据此宣称已完成。

## Post-merge 当前验收状态（IMPLEMENTED；用户主观展示验收仍待）

`perception/verification_evidence.py` 从与定位同源的主相机 controlled-edge detections 提取 normalized bbox union，生成 before/after target ROI（仅用于验单，不改 Camera→SLAM），并只把 crop hash、ROI 与事实 context 进入 Replay key；crop 本身仅用于当次模型调用。`qwen.py` 的 primary verifier 接收 full-before/full-after/ROI-before/ROI-after 四项证据；primary 未闭环时，最多调用一次完全独立的 paired-ROI verifier，不能携带第一次答案。service 在保存/Replay 时严格校验 schema、JSON bool 与有限 raw float，异常一律 `VERIFICATION_ERROR` / fail closed；Analytics 读取保存的 `first_review`，不把独立 ROI 补救结果冒充首判。

P1-G acceptance runner 以独立 SQLite append-only `acceptance_runs` 保存真实阶段执行、运行时 trace、source batch 和安全摘要。正式 batch 满足 Live 5/5、5/5、5/5、3/3；post-review 四个 Replay 各3/3，Replay transport 被断言阻断且无新 Cloud request。该 runner 在每个 Demo03 跨楼试验前以持久化、显式的 relocation task 返回 B1F，绝不直接写坐标或 reset Fleet。Task-owned human completion 通过 session+lease 唯一 owner；task-owned event 的旧 manual HTTP 返回409，Agent没有人工确认工具，Workbench不暴露该旧入口；非 task-owned event 保留原人工完成流程。backend164/frontend46/build/bash-n/diff与 A/B/C/D/E 已通过，P1-G 已合并至 main；用户主观展示验收仍独立。

## P1-H 当前观测架构（IMPLEMENTED · A/E PASS · 2026-08-30）

`observability/context.py`传递独立Trace；`requests.py`只在实际调用时记录模型metadata和stage spans；`service.py`是只读SQLite投影，`redaction.py/errors.py`在API边界执行白名单及taxonomy安全映射，`routes.py`仅GET。`AdvancedView/advancedTraceModel`负责63/37布局和节点选择，不拥有Runtime。

Event trace在创建时持久化；模型记录外层新增trace列，canonical payload不改。Operations session/request/nativeTask有独立关联；每消息request trace写audit，CleaningTask绑定event trace并保留origin_request_trace_id。GET按event/task/明确request关联，不按整个session关联。legacy只显示缺失，禁止startup/GET回填。新stage/model/tool均真实计时，历史缺失不补造。

## P1-F 当前执行架构（IMPLEMENTED · A/E PASS · 2026-08-30）

`robot_operations/` 按职责分离：`repository`（SQLite session/task/audit/cache）、`catalog`（Approved POI/原生配送部署策略/未授权平台 registry）、`tools`（严格参数与白名单）、`agent`（唯一 Ops model-tool loop/Advice）、`tasks`（Task state machines）、`coordination`（跨原工作台与 Agent 的 durable lease）、`routes`（薄 HTTP）。

`runtime_transaction()` 让嵌套仓储调用共享 BEGIN IMMEDIATE；仅短确定性状态变更持锁。模型调用在事务外；单 backend worker 启动将未完成请求标 INTERRUPTED，不自动重发模型/硬件命令。并发派发只允许一个占用；Task action session header 与工具路径都验证归属。不是生产分布式执行引擎。

CleaningTask 只关联现有集成事件，阶段完全委托 demo_v1；完整 trace 读取同一 CleaningEvent transitions。Delivery/Relocation 有持久化 task transitions、同一 Fleet active_task_id、合法 POI 与现有 Dijkstra。配送 CREATED→ASSIGNED→TO_PICKUP→ARRIVED_PICKUP→PICKED_UP→条件电梯→TO_DESTINATION→DELIVERED→CLOSED；无电梯路段不伪造 ELEVATOR_TRANSIT。物理推进来源为显式操作员 PoC driver。

前端 `RobotOperationsProvider` 提供跨页 Session/错误/忙碌/串行只读同步；聊天和任务卡不生成本地替代结果。任务/对话真相在 SQLite，UI 位置只存 localStorage。Analytics 上半缓存建议、下半同一对话，无第二 Agent。Advice GET 不调用模型，POST 才真实执行只读 tool loop 并保留审计；provider/parser失败保留旧缓存。麦克风明确未配置。旧 P1-F 横向浮窗、仅 Header / Drag Handle 拖动及展开式 Tool/Task Panel 是现有实现的历史 UI Shell，**SUPERSEDED BY AI-UI-01**；AI-UI-01 是未实施的 LOCKED TARGET，详见 `INTERVIEW_DEMO_RECONCILIATION.md`。

## P1-E 当前数据层（IMPLEMENTED · A/E PASS · 2026-08-30）

`analytics/history_seed.py` 在 FastAPI lifespan 的 schema 初始化之后幂等插入过去30个完整日的结构化事件/transition，日期+版本ID、显式时间/来源；不调用真实模型、Runtime、Fleet。六事实源中的“演示历史”是合成业务数据，不是客户生产数据。

`analytics/read_model.py` 从一次 `read_archived_events()` SQLite快照计算5KPI、样本分母、数据来源组成、时段/类型/热点、事件时活跃区间利用率。默认滚动30天；自定义窗口同步返回真实 `period.days`。利用率 provider 当前显式假定连续可用，未来可替换观测区间。无 GET 写入、无当前 Fleet 覆盖。

`AnalyticsView` 与纯 `analyticsViewModel` 消费真实 API；ECharts 与已有 MapCanvas/projectMapCoordinate 共用内层坐标。热点选择为聚合区域交互，事件点坐标不被挪动；明细保留精确 map/x/y/type/time 与平均闭环并跳档案。Event Archive 能恢复 UTC 时间筛选且 input 显示本地时间。Analytics右侧已按P1-F接入共享Agent/真实只读Advice；旧固定推荐入口退役410。

## P1-D 当前实现补充（2026-08-30）

`backend/event_archive/service.py` 在同一 SQLite read transaction 批量读取 events/transitions，投影发现时间、类别、处理方式、事件时执行对象与位置、duration。`/api/event-archive` 支持 category/q/event_type/handling_mode/since/until/map_id/offset/limit；非法筛选 422，不静默回退全部。无 write/model/workflow/Fleet 依赖。

`EventArchiveView` + `eventArchiveModel` 负责只读分页/1.5 秒串行轮询、URL selected event、请求取消与 ID 防错配；复用 `EventDetailPanel(mode="history")`，不另建详情 renderer。`PrototypeWorkbench` 路径与 popstate 恢复导航，阶段 POST 与当前任务 polling 仅在 Workbench 执行。历史布局 56/44、紧凑 archive header/row 和 history technical card 是当前实现事实；其面客页面标题、工单表格和 Workbench/Event Center 详情同构展示已被 **EVENT-01 SUPERSEDED / LOCKED TARGET**，当前属 `IMPLEMENTATION_DIVERGENCE`，不可据此宣称已满足 EVENT-01。

## P1-C 当前实现补充（IMPLEMENTED · A/E PASS）

`perception/qwen.py`：唯一 provider transport + 严格 canonical visual schema；`perception/multiview/autonomous.py`：只读 evidence policy / model tool loop；`demo_v1/perception_records.py`：LIVE structured response + model turns 持久化/校验；`demo_v1/service.py`：阶段组合，不拥有第二套 Scheduler/Spatial。

`cloud-review` 开始只传 primary image、primary edge、camera-scoped context；持久化 SINGLE_VIEW_REVIEW。可恢复不足时，先用同一 Camera→SLAM helper 计算 **Coverage 查询 hint**，不写正式定位/派单目标；Agent 用 Phase 2 coverage polygon 与 manifest evidence 白名单交集。成功工具输出与图片随后追加到 model conversation；从不预装补图。正式 LOCATED/dispatch target 仍由后续 locate stage 写入。最终充分证据再作 confidence gate，灰区二审只读本次合法图片/事实 context，不读之前模型答案。

Audit 保存 UTC 时间、agent start、候选、model tool calls、selected camera/fetch、语义结果、实际 provider latency；不保存 prompt/image data URL/CoT。额外摄像头≤2、fetch rounds≤2、model turns≤6（含 query/final，不等同取证轮数）。原有 legacy LangGraph / AI Lab 技术接口仍保留，但不在主工作台新闭环上，也不声称已经全面迁移。

Semantic records 使用 `p1c.visual-pipeline.v1`，绑定图像字节、camera context/coverage、模型标识、semantic/Agent system prompt、工具 schema/description、budget 与 schema；Replay 解码安全 OpenAI assistant message，再运行同一个 Agent 的 Coverage/Fetch/白名单与门控。verification records 仍按 P1-A 合约；旧不兼容记录缺失时安全失败。新 schema 不改变共享 TaskProfile、Capability、Scheduler、Dijkstra、Fleet。

## 1. 当前运行形态（IMPLEMENTED）

```text
React / Vite customer shell (/ and /prototype)
  ├── Workbench：CameraMonitorGrid + SpatialDispatchView + EventDetailPanel
  ├── Event Center：P1-D 只读档案列表/筛选/URL + 共用 history EventDetailPanel
  ├── Analytics：同库Seed/Runtime聚合 + 5KPI/热点/区间利用率；P1-F共享Agent建议
  └── Advanced：只读Trace → Node → Inspect / Tool / Error / Reality Matrix
  ▼
FastAPI /api
  ├── demo_v1.service（阶段 Runtime）
  ├── perception/qwen（唯一云端 transport）
  ├── perception/multiview/autonomous（证据不足时真实 model auto-tool）
  ├── spatial（地图、标定、Dijkstra global topology planner / plan_route()）
  ├── scheduling（Capability Engine + Scheduler）
  ├── analytics + robot_operations Advice（真实演示聚合与共享 Agent 只读建议；旧 Optimization endpoint 410）
  └── SQLite（CleaningEvent / transitions / decisions / human work orders）
```

**实现边界**：D06 Event Center 已按 P1-D 完成；D07 Analytics已在P1-E接入真实聚合；D08–D09 Operations/Advice已在P1-F完成；D10 新 Multi-view 已按 P1-C 完成。

## 2. 已实现的阶段边界（IMPLEMENTED / LOCKED）

```text
POST create event
  → edge-review
  → cloud-review（single-view → evidence gate → optional autonomous multi-view → final confidence / independent second / Fusion）
  → locate
  → assign（Capability Engine + Scheduler）
  → start-navigation → complete-navigation → complete-cleaning
  → verify
  → CLOSED / HUMAN_REVIEW / HUMAN_FALLBACK
```

- 每个阶段保存 `CleaningEvent` 并 `record_transition`；Cloud、Scheduler、Verification 不得由未来/早期接口提前调用。
- `perception.qwen._request_qwen` 是唯一 DashScope transport。LLM 输出语义、置信度、能力建议和验收；**LLM 不选机器人**。
- `assignment_decision` 是前端行动机器人的唯一事实源。旧 `/api/demo-v1/runs/*` 已 RETIRED (410)。
- 受控 bbox 是 `CONTROLLED_EDGE_DEMO`，不是本地权重推理；现有 operation playback 也不得称为真实机器人遥测。

## 3. 锁定的清洁 Runtime（P1-A/B/C IMPLEMENTED；target-aware Verification 与 P1-G 工程总收口已完成）

```text
Fixed Camera
  → Edge YOLO / controlled edge evidence
  → Single-view Cloud VLM
  → Evidence Sufficiency Judgment
  → conditional Multi-view Perception Agent
  → Multi-view Cloud VLM
  → Business Decision + System Fusion / veto
  → Camera→SLAM
  → Capability Engine
  → Scheduler
  → Dijkstra global topology planner / plan_route()
  → Robot Execution
  → Fixed Camera After
  → Cloud target-aware Verification
  → CLOSED / HUMAN_REVIEW / HUMAN_FALLBACK
```

`confidence` 与 `evidence_sufficient` 必须是不同输出，且 **Evidence Sufficiency Gate 优先于最终 confidence disposition**。Single-view `evidence_sufficient=false`、ambiguity 属于 reflection / occlusion / perspective / lens_contamination / insufficient_view 等可由额外视角缓解的问题、并存在合法 supporting cameras 时，先进入自主 Multi-view evidence acquisition；不能仅因 Single-view `confidence < 0.50` 提前 `HUMAN_REVIEW`。取得最终充分 evidence 后，才执行 `confidence >= 0.85` 不独立二审、`0.50 <= confidence < 0.85` 独立 targeted second review、`confidence < 0.50` 为 `HUMAN_REVIEW`。没有合法 supporting camera、Evidence Fetch 失败、或最多 2 rounds 后仍不充分时必须 `HUMAN_REVIEW`；最终 evidence 不充分即使 raw confidence 高也不得自动机器人处置。

**CURRENT vs TARGET（P1-A IMPLEMENTED，工程验收通过）**：活跃 stage API 已用 bbox 地面代表点调用共享 `map_pixel_to_slam()`；navigation 从 SQLite Fleet 当前 map 调 Dijkstra `plan_route()`。Camera→SLAM 失败持久化 `error.error_type=SPATIAL_ERROR` 与 HUMAN_REVIEW transition，阻止后续 Scheduler/assignment/route；P1-H 的八类 taxonomy 已实施。P1-C 已替换活跃 Multi-view 为先单图、证据不足时真实自主取证；旧初轮多图/场景强制已删除。

### P1-A Closure 的持久化与 Replay（IMPLEMENTED · Reviewer A/E PASS）

- `system_snapshots.fleet_state` 是活跃阶段 Runtime 的共享 Fleet；初始化不覆盖已有位置/电量/状态/active_event_id，事件保存独立 fleet_snapshot。底层数据库 session 每步关闭；真正重启测试另起 Python interpreter 后重读 SQLite。
- `model_records` 保存 LIVE provider structured response bundle，而非预计算路由或整场演示。P1-A `demo_v1/replay.py`（verification 继续使用，semantic 已由 P1-C `perception_records.py` 替代）校验 schema、image hash、model、Prompt 合约、事实 context 及关联 LIVE event；一审/二审分开保留。灰区一审缺二审的 bundle 不合法。
- 显式 Stable Replay 仅替换 cloud/verification response source；Camera→SLAM、Capability、Scheduler、Dijkstra、Fleet、SQLite、任务阶段和验收门控均重新运行。Replay 缺 semantic record 时安全停止；缺 after verification record 时先保存 VERIFYING，再 HUMAN_REVIEW / VERIFICATION_ERROR。
- 用户确认的废弃待清运事实存于主摄像头事件 metadata，以 `scene_context` 纳入 Scenario manifest；按 camera_id 匹配的 `operational_context` 进入一/二审相同事实 context，并以 `cloud_context` 持久化。模型不可读取 expected_robot/verification_mode 等预期结论；Replay key 包含该 context。事实限定本事件的两箱，不扩展到该摄像头所有未来物体。
- Demo04 人工完成不依赖 demo_id，而要求已持久化的 `HUMAN_FALLBACK` + `candidate_count=0`；机器人/人工完成调用同一 verification workflow。真实模型 veto 仍可阻止此前路径，不得为闭环展示绕过。
- 此处 Task Runtime 指当前 CleaningEvent/assignment/active_event_id 阶段执行；P1-F已在此基础上增加Agent Task/Action Card，清洁阶段仍委托同一CleaningEvent。`run_demo` 兼容入口仅委托同一 stage runtime；旧合成 `_stable_replay` 及旧持久化捷径已删除，旧 `/runs/*` 仍 410。P1-A Event/targeted 的 need_clean 与 verification 的 verification_pass 及其 confidence 必须在规范化前严格校验 JSON boolean / 非 boolean 的有限数值，禁止字符串 `"false"` 或布尔置信度转换成成功结果。 AI Lab 旧 run_qwen_vl 与非关单字段 issue_remaining 的宽松规范化尚待后续统一硬化，不属于本轮已验证范围。

## 4. Multi-view Perception Agent（IMPLEMENTED / LOCKED · P1-C）

```text
Single-view VLM
  ├── event_type / need_action / confidence
  ├── evidence_sufficient / ambiguity_type
  └── tool_choice=auto
       ├── finish_visual_judgment()
       └── find_supporting_cameras()
            → fetch_camera_evidence() × 1–2
            → Multi-view Cloud VLM
            → finish_visual_judgment()
```

- 执行顺序固定为 Single-view evidence → Evidence Sufficiency Gate → recoverable insufficiency 时自主 acquisition → final semantic judgment → final confidence disposition。若最终落在 `0.50 <= confidence < 0.85`，独立 second review 可读取本次合法取得的 evidence set，但不得读取上一轮模型答案或 reasoning。
- Agent 只拥有视觉证据获取自主权：找 Camera Coverage candidate、读取合法 evidence、结束视觉判断；最多 2 路补充摄像头、最多 2 个 acquisition rounds。
- PoC Evidence Adapter 可以返回 controlled evidence assets，必须显式标示；未来可替换 RTSP/VMS/NVR/Camera Platform。它不是生产级多摄像头同步。
- Agent 不拥有配置权：不能修改 Camera Coverage、邻接关系、calibration、SLAM、地图、机器人、confidence、阈值、Capability 或 Scheduler。
- Demo02 从 CAM-A1-01 单视角开始；只有真实模型以 `tool_choice=auto` 发出 Tool Call 后，后端才进入 acquisition。不得按 `demo_id`、固定 confidence、`tool_choice=required`、一次塞三图或前端动画强制进入。
- 旧“客户 UI 只投影 Agent Trace / Tool Audit / Cloud Response”的表述是 P1-C 历史视觉范围，**SUPERSEDED BY WB-DETAIL-01 / EVENT-01**。客户详情应投影业务过程；Event Detail 的证据区仍可如实显示同图受控 edge YOLO bbox/对象/置信度、并排 supporting evidence 与独立 Multi-view VLM judgement。Tool JSON、arguments、round、raw response、latency 与 Chain-of-Thought 只在 Advanced。

## 5. 空间、路线与 Fleet（IMPLEMENTED 基础 + TODO）

**IMPLEMENTED 基础**：6 map（OUTDOOR、A_B1、A_1F、A_2F、B_1F、B_2F）、Global Spatial Graph、Camera Coverage、`map_pixel_to_slam()`、Dijkstra global topology planner / `plan_route()`、`campusTopology` 与蜗小白 SC50 演示锚点存在。A2F 与 B2F 通过 Skybridge 连接。

**IMPLEMENTED / LOCKED（P1-A/B）**：MapCanvas 的 object-contain 内层画布是 white model、anchor、marker、route、robot 的唯一坐标系；定位后才出现 marker。Scheduler 以共享 Fleet 当前 map 与 target SLAM map 调 `plan_route()`，前端只投影其结果。蜗小白 SC50 的基线路线为 B1F → elevator → B2F → Skybridge → A2F carpet can event；终态保留，只有显式 baseline/reset 才复位。

P1-B 前端模块边界：`spatialProjection.ts` 当前提供 MapCanvas 坐标、backend node-path 到 `CAMPUS_TOPOLOGY_ANCHORS` 的 overview 投影和线性插值（缺少或未知 node_path 返回空）；`MapCanvas.tsx` 统一实际图像矩形；`useRoutePlayback.ts` 按 UTC NAVIGATING timestamp 恢复 rAF 插值与入口 1 秒停留；`SpatialDispatchView.tsx` 读取 Fleet 与 ASSIGNED 起点快照。插值不是遥测，也不构成第二个 Route Planner。该 anchor projection 仅证明拓扑顺序，不能证明道路/走廊/连廊可行走几何；它的面客视觉方案 **SUPERSEDED BY WB-MAP-01**，当前属 `IMPLEMENTATION_GAP`。未来必须由 backend deterministic route + 统一维护的 Demo Navigation Waypoint Geometry 驱动面客路线，禁止 React/demo 特判或任意连线。

`eventViewModel.ts` 只投影存档 transitions/asset_manifest；`EventStageEvidence.tsx` 与 `EventDetailPanel.tsx` 当前共用 live/history 卡片，history 不执行 action、不自动滚动。`runtimeSession.ts` 保存 ID/请求防重键、GET-only 恢复、拒绝倒退/外来快照；`PanelBoundary.tsx` 隔离空间显示异常。图像缺失显示不可用，不用预设成功图片替换。当前 Workbench 详情仍将可审计 AI、空间、路线、终态与技术边界混合展示；其历史 UI Shell **SUPERSEDED BY WB-DETAIL-01**，现属 `IMPLEMENTATION_DIVERGENCE`。未来仍从同一 durable transition/asset/decision/route/verification 投影，但 Workbench 只呈现面客业务事实，技术 trace/latency/schema/PoC boundary 转由 Advanced 承担。当前 `CameraMonitorGrid` 仍为双槽、`CameraViewport` 使用 evidence-first `object-contain` 并可绘制 bbox；该 customer monitor wall 视觉方案 **SUPERSEDED BY WB-CAMERA-01**。未来三槽 monitoring mode 必须以真实 before/after/runtime state 投影、允许合理 cover/crop 而不显示 bbox，Evidence/Advanced 则继续使用完整原图和坐标一致性。

## 6. Event Model、Event Center 与历史快照（P1-B 详情与 P1-D 列表/URL 已实现）

```text
CleaningEvent
  ├── detection / edge evidence / Cloud and Multi-view evidence
  ├── spatial location / TaskProfile / assignment decision / navigation route
  ├── robot or human handling / verification
  ├── event_transitions (timestamped audit)
  └── terminal state + immutable history snapshot
       ├── Workbench EventDetailPanel(mode="live")
       └── Event Center EventDetailPanel(mode="history")
```

**P1-D 已实现基础 / EVENT-01 LOCKED TARGET**：Event Center 的同一事件列表、默认倒序、五类状态、URL `?event=` 恢复选择、首次不自动打开和只读历史快照仍有效；`HUMAN_FALLBACK` 是业务兜底，不是异常。旧 archive/trace 页面定位、技术紧凑列表和 history-only detail visual shell **SUPERSEDED BY EVENT-01**。未来必须成为面客工单列表，详情与 Workbench 逐项同构（仅动作权限不同），并统一展示真实条件化 Multi-view 流程与 Demo02 canonical v2 evidence，不能另建第二模型或逻辑。

## 7. Analytics Engine（P1-E IMPLEMENTED；P1-F Agent Read Tools/Advice IMPLEMENTED）

```text
30-day structured Demo Historical Baseline (explicitly labelled)
  + current Runtime CleaningEvent Increment
  → deterministic Analytics Engine
       ├── KPI definitions / denominator rules
       ├── Campus Spatial Event Heatmap
       ├── event structure + time / hotspot analysis
       └── cleaning-robot utilization from task-state time
  → Analytics UI（P1-E已实现） + Robot Operations Agent read tools（P1-F IMPLEMENTED）
```

Analytics Engine 不是 Agent，不得由 LLM 编造 KPI、utilization 或效果数字。热力图用 map_id/x/y/event_type/timestamp 聚合，点击热点可带 filter 跳到 Event Center。FlashBot Max 不进入清洁机器人利用率排名。运营建议只读取此确定性数据；默认显示带 Data Window / Generated At 的 snapshot，用户主动点击才重新生成。

## 8. Robot Operations Agent、Policy Guard 与页面上下文（P1-F runtime IMPLEMENTED；AI-UI-01 UI Shell LOCKED TARGET）

```text
User text / future ASR transcript
  → Robot Operations Agent
  → Read Tool(s) / intent + plan
  → Policy Guard
  → allowed Action Tool
  → Task Runtime
  → Observe → Replan (within policy) → Close
  → Action Card + Action Audit
```

- Read Tools 可查询事件、Analytics、Fleet、capability、POI、camera evidence、任务与授权配送状态；Action Tools 仅限低风险创建/派发/暂停/恢复/取消清洁、配送、Relocation/Standby task、请求证据和状态通知。
- 不提供任何改变地图、禁行区、范围、能力、Camera Coverage/calibration、Scheduler policy、阈值、安全速度、门禁或电梯权限的 Write Tool。Agent 不直接发底盘坐标，只能目标化到合法 POI。
- 所有 physical-world Action 必须写 Action Audit：原始指令/ASR、intent、tool/args、Policy Guard、Task ID、robot、结果、异常、replan、final state。Action Card 读取真实 backend Task，与 Workbench / Fleet 同一 ID / state。
- 系统只有两个真正 Agent：Multi-view Perception Agent 与 Robot Operations Agent。RAG 是后者可选 Knowledge Tool，不是第三个 Agent。

```text
Shared AgentSession / Message / ActionAudit / Task context
  ├── Workbench: AI-UI-01 圆形拖动入口 → 完整弹出式 Chat + live context
  ├── Event Center: 同一圆形入口 → 完整弹出式 Chat + selected event context
  └── Analytics: 固定统一右侧 Advice + 完整 Chat Area + KPI/hotspot/chart context
```

AI-UI-01 锁定：Workbench / Event Center 的默认收起入口是左下小型圆形/球形 AI 悬浮球，可在整个浏览器可视区域的合法位置拖动并持久化，且默认不遮挡核心内容；点击后弹出完整 Chat Window，并可关闭/收起回圆球。旧“共享横向 Floating Window、仅 Header / Drag Handle 拖动、展开式 Tool/Task Panel”**SUPERSEDED BY AI-UI-01**，当前代码是 `IMPLEMENTATION_DIVERGENCE`。Analytics 仅显示固定且统一的右侧 AI Area：上半 Advice、下半完整 Chat；其独立布局/滚动必须保证左侧长内容不会将 Chat 入口推至整页底部。三页仍为一个 Agent、一个 Agent Session、同一 Task / Audit / Backend State；不得新建 Analytics / Optimization / 第二 Conversation Agent。语音只是同一 Agent 的 Microphone → real ASR → transcript 输入适配，不是独立 Agent，也不是当前清洁 Demo 主秀；麦克风只有在真实 ASR provider 已配置时可用，否则 disabled 或明确显示“语音服务未配置”，不得 fake voice interaction。

## 9. External Delivery Adapter（registry IMPLEMENTED；真实授权/回调 TODO）

清洁仍是主业务。未获得平台授权、资质与 API 权限时，Delivery Adapter 只能显示 `ADAPTER READY` / `AUTH REQUIRED`；不得声称 `CONNECTED` 或伪造 platform callback。授权后，结构化订单走确定性 Adapter / POI normalization / Policy / Delivery Workflow / FlashBot Max / status callback；不确定例外才升级给 Robot Operations Agent。

## 10. Advanced Technical Observability（IMPLEMENTED · P1-H）

```text
Existing Runtime
  → CleaningEvent transitions / Cloud request records / Agent Action + Tool Audit
  → spatial mapping / capability evaluation / assignment / route / verification
  → provider status + reality source metadata
  → Technical Projection
  → Advanced Trace Inspector
       ├── AI Recognition Trace
       ├── Spatial / Capability / Scheduling / Route Trace
       ├── Runtime / Model / Tool / Error Observability
       └── System Reality Matrix
```

Advanced 是 read-mostly **Technical Observability & Execution Trace Inspector**，不是新 Runtime：不得独立重跑模型、Scheduler 或 Route Planner。当前为顶部 Runtime Strip、左63% Execution Trace、右37% Selected Node Detail 的 Trace → Node → Inspect，不默认展平 JSON。

AI Trace 固定投影 Edge Detection、Single-view Cloud VLM、Conditional Multi-view Perception Agent、Multi-view Cloud Judgment、Business Decision/Fusion、Verification 六段。Multi-view 未发生时必须明确 `NOT_TRIGGERED / EVIDENCE_ALREADY_SUFFICIENT`；发生时 Tool Trace 必须来自真实 Agent audit，并记录 `MODEL_TOOL_CALL`。每个 Node 只显示结构化 input/output summary、evidence, confidence、sufficiency、ambiguity、latency、second-review、ROI/verdict，不显示 Chain-of-Thought。

空间 Trace 固定投影 Camera→SLAM、Capability、Scheduler、Dijkstra：在现有 Runtime 具备记录后显示 calibration / u-v / map-x-y、TaskProfile / constraints、Scheduler explanation / `AssignmentDecision`、Dijkstra map/node/segment/cost；Dijkstra 是 campus global topology，不是 Nav2 / local obstacle avoidance。Runtime / Tool / Error Trace 使用统一 trigger source（`MODEL_TOOL_CALL`、`SYSTEM_WORKFLOW`、`USER_ACTION`）与错误 taxonomy（`MODEL_ERROR`、`TOOL_ERROR`、`POLICY_REJECTED`、`SPATIAL_ERROR`、`SCHEDULER_ERROR`、`ROUTE_ERROR`、`VERIFICATION_ERROR`、`EXTERNAL_ADAPTER_ERROR`）。

Reality Source Metadata 是独立可审计数据：`LIVE MODEL`、`DETERMINISTIC RUNTIME`、`CONTROLLED EVIDENCE`、`POC SIMULATION`、`REPLAY`、`AUTH REQUIRED / NOT CONNECTED`。System Reality Matrix 由该 metadata、provider/configuration 与 authorization status 自动投影，覆盖模型、evidence、空间、调度、路线、机器人、电梯/Skybridge、验证、Replay、Delivery、ASR；不能由前端手改或伪造。Advanced 还应显示 Current PoC Boundaries、future adapter replacement points 与独立 Trace ID（不等于 Event ID），且绝不泄露密钥、token、authorization header 或环境变量值。

## 11. 不进入本轮与不允许的实现

Unified Implementation 已授权前后端、测试与文档变更，但仍禁止第二 UI System、Three.js、ROS/RMF、Docker/K8s、大型本地模型，以及让 Agent 或 Advanced 改基础设施配置。Batch C / Part 3 由后续 P1-H 承载，不提前混入 P1-A/P1-B。
