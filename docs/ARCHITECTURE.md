# AI 自主清洁 Demo｜当前架构与锁定目标

> **状态：IMPLEMENTED 基线 + LOCKED/TODO · 2026-08-30**
> 本文同时表达代码事实与下一实现目标；没有明确标为 IMPLEMENTED 的内容均不可据此宣称已完成。

## 1. 当前运行形态（IMPLEMENTED）

```text
React / Vite customer shell (/ and /prototype)
  ├── Workbench：CameraMonitorGrid + SpatialDispatchView + EventDetailPanel
  ├── Event Center：基础列表 + 独立简版详情
  ├── Analytics：Demo history 聚合 + 基础热点 / KPI / 建议
  └── Advanced：状态与 trace shell
  ▼
FastAPI /api
  ├── demo_v1.service（阶段 Runtime）
  ├── perception/qwen（唯一云端 transport）
  ├── perception/multiview（灰区、受控顺序的 LangGraph）
  ├── spatial（地图、标定、Dijkstra global topology planner / plan_route()）
  ├── scheduling（Capability Engine + Scheduler）
  ├── analytics / optimization（演示聚合与确定性 mock recommendation）
  └── SQLite（CleaningEvent / transitions / decisions / human work orders）
```

**实现边界**：当前 Event Center、Analytics、Optimization 与 Multi-view 的代码存在，但只代表上述现状；它们不代表 D06–D10 的 LOCKED 目标已经完成。

## 2. 已实现的阶段边界（IMPLEMENTED / LOCKED）

```text
POST create event
  → edge-review
  → multi-view（当前：仅 Demo02 / 灰区受控流程）
  → cloud-review（一次 Cloud / 必要时独立二审 / Fusion）
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

## 3. 锁定的清洁 Runtime（TODO）

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

**CURRENT vs TARGET（P1-A IMPLEMENTED，工程验收通过）**：活跃 stage API 已用 bbox 地面代表点调用共享 `map_pixel_to_slam()`；navigation 从 SQLite Fleet 当前 map 调 Dijkstra `plan_route()`。Camera→SLAM 失败持久化 `error.error_type=SPATIAL_ERROR` 与 HUMAN_REVIEW transition，阻止后续 Scheduler/assignment/route；完整 taxonomy 仍属 P1-H。当前 Multi-view 仍是固定灰区工具序列，初轮可使用多图上下文；自主视觉取证仍属 P1-C，不宣称已经实现。

### P1-A Closure 的持久化与 Replay（IMPLEMENTED · Reviewer A/E PASS）

- `system_snapshots.fleet_state` 是活跃阶段 Runtime 的共享 Fleet；初始化不覆盖已有位置/电量/状态/active_event_id，事件保存独立 fleet_snapshot。底层数据库 session 每步关闭；真正重启测试另起 Python interpreter 后重读 SQLite。
- `model_records` 保存 LIVE provider structured response bundle，而非预计算路由或整场演示。`demo_v1/replay.py` 校验 schema、image hash、model、Prompt 合约、事实 context 及关联 LIVE event；一审/二审分开保留。灰区一审缺二审的 bundle 不合法。
- 显式 Stable Replay 仅替换 cloud/verification response source；Camera→SLAM、Capability、Scheduler、Dijkstra、Fleet、SQLite、任务阶段和验收门控均重新运行。Replay 缺 semantic record 时安全停止；缺 after verification record 时先保存 VERIFYING，再 HUMAN_REVIEW / VERIFICATION_ERROR。
- 用户确认的废弃待清运事实存于主摄像头事件 metadata，以 `scene_context` 纳入 Scenario manifest；按 camera_id 匹配的 `operational_context` 进入一/二审相同事实 context，并以 `cloud_context` 持久化。模型不可读取 expected_robot/verification_mode 等预期结论；Replay key 包含该 context。事实限定本事件的两箱，不扩展到该摄像头所有未来物体。
- Demo04 人工完成不依赖 demo_id，而要求已持久化的 `HUMAN_FALLBACK` + `candidate_count=0`；机器人/人工完成调用同一 verification workflow。真实模型 veto 仍可阻止此前路径，不得为闭环展示绕过。
- 此处 Task Runtime 指当前 CleaningEvent/assignment/active_event_id 阶段执行；P1-F Agent Task/Action Card 尚未实现。`run_demo` 兼容入口仅委托同一 stage runtime；旧合成 `_stable_replay` 及旧持久化捷径已删除，旧 `/runs/*` 仍 410。P1-A Event/targeted 的 need_clean 与 verification 的 verification_pass 及其 confidence 必须在规范化前严格校验 JSON boolean / 非 boolean 的有限数值，禁止字符串 `"false"` 或布尔置信度转换成成功结果。 AI Lab 旧 run_qwen_vl 与非关单字段 issue_remaining 的宽松规范化尚待后续统一硬化，不属于本轮已验证范围。

## 4. Multi-view Perception Agent（LOCKED / TODO）

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
- 客户 UI 只投影 Agent Trace / Tool Audit / Cloud Response / transition 中的 Tool Calls、Evidence、Selected Cameras、Final Confidence、Decision；禁止 Chain-of-Thought。

## 5. 空间、路线与 Fleet（IMPLEMENTED 基础 + TODO）

**IMPLEMENTED 基础**：6 map（OUTDOOR、A_B1、A_1F、A_2F、B_1F、B_2F）、Global Spatial Graph、Camera Coverage、`map_pixel_to_slam()`、Dijkstra global topology planner / `plan_route()`、`campusTopology` 与蜗小白 SC50 演示锚点存在。A2F 与 B2F 通过 Skybridge 连接。

**LOCKED / TODO**：MapCanvas 的 object-contain 内层画布是 SLAM white model、anchor、marker、route、robot 的唯一坐标系；定位后才出现 marker。Scheduler 应以共享 Fleet 当前 map 与 target SLAM map 调 `plan_route()`，前端只投影其结果。蜗小白 SC50 的正式路线为 B1F → elevator → B2F → Skybridge → A2F carpet can event；终态保留到 new demo/reset。

## 6. Event Model、Event Center 与历史快照（LOCKED / TODO）

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

Event Center 是 read-only archive：事件创建即进入列表，默认倒序；全部、处理中、已自主闭环、待人工处理、异常五类状态分离。`HUMAN_FALLBACK` 是业务兜底，不是异常。历史详情必须读事件发生当时 Fleet / robot / route / AI / verification snapshot，不能用当前状态覆盖；URL `?event=` 恢复选择但首次不自动打开。

## 7. Analytics Engine（LOCKED / TODO）

```text
30-day structured Demo Historical Baseline (explicitly labelled)
  + current Runtime CleaningEvent Increment
  → deterministic Analytics Engine
       ├── KPI definitions / denominator rules
       ├── Campus Spatial Event Heatmap
       ├── event structure + time / hotspot analysis
       └── cleaning-robot utilization from task-state time
  → Analytics UI + Robot Operations Agent read tools
```

Analytics Engine 不是 Agent，不得由 LLM 编造 KPI、utilization 或效果数字。热力图用 map_id/x/y/event_type/timestamp 聚合，点击热点可带 filter 跳到 Event Center。FlashBot Max 不进入清洁机器人利用率排名。运营建议只读取此确定性数据；默认显示带 Data Window / Generated At 的 snapshot，用户主动点击才重新生成。

## 8. Robot Operations Agent、Policy Guard 与页面上下文（LOCKED / TODO）

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
  ├── Workbench: draggable Floating Window + live context
  ├── Event Center: same floating window + selected event context
  └── Analytics: fixed right panel + KPI/hotspot/chart context
```

没有已保存 UI position 时，Workbench / Event Center 的共享浮窗默认位于左下角；有 localStorage position 时以其为准。浮窗只能从 Header/Drag Handle 拖动，不能超 viewport，展开/收起、跨 Workbench/Event Center 与刷新均保持位置；Analytics 仅显示固定 Panel，不与 Floating Window 重复。语音只是同一 Agent 的 Microphone → real ASR → transcript 输入适配，不是独立 Agent，也不是当前清洁 Demo 主秀；麦克风只有在真实 ASR provider 已配置时可用，否则 disabled 或明确显示“语音服务未配置”，不得 fake voice interaction。

## 9. External Delivery Adapter（LOCKED / TODO）

清洁仍是主业务。未获得平台授权、资质与 API 权限时，Delivery Adapter 只能显示 `ADAPTER READY` / `AUTH REQUIRED`；不得声称 `CONNECTED` 或伪造 platform callback。授权后，结构化订单走确定性 Adapter / POI normalization / Policy / Delivery Workflow / FlashBot Max / status callback；不确定例外才升级给 Robot Operations Agent。

## 10. Advanced Technical Observability（LOCKED / TODO）

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

Advanced 是 read-mostly **Technical Observability & Execution Trace Inspector**，不是新 Runtime：不得独立重跑模型、Scheduler 或 Route Planner。当前代码仅有基础技术状态卡片与当前事件 JSON；目标实现改为顶部 Runtime Strip、左 62–65% Execution Trace、右 35–38% Selected Node Detail 的 Trace → Node → Inspect，不默认展平 JSON。

AI Trace 固定投影 Edge Detection、Single-view Cloud VLM、Conditional Multi-view Perception Agent、Multi-view Cloud Judgment、Business Decision/Fusion、Verification 六段。Multi-view 未发生时必须明确 `NOT_TRIGGERED / EVIDENCE_ALREADY_SUFFICIENT`；发生时 Tool Trace 必须来自真实 Agent audit，并记录 `MODEL_TOOL_CALL`。每个 Node 只显示结构化 input/output summary、evidence, confidence、sufficiency、ambiguity、latency、second-review、ROI/verdict，不显示 Chain-of-Thought。

空间 Trace 固定投影 Camera→SLAM、Capability、Scheduler、Dijkstra：在现有 Runtime 具备记录后显示 calibration / u-v / map-x-y、TaskProfile / constraints、Scheduler explanation / `AssignmentDecision`、Dijkstra map/node/segment/cost；Dijkstra 是 campus global topology，不是 Nav2 / local obstacle avoidance。Runtime / Tool / Error Trace 使用统一 trigger source（`MODEL_TOOL_CALL`、`SYSTEM_WORKFLOW`、`USER_ACTION`）与错误 taxonomy（`MODEL_ERROR`、`TOOL_ERROR`、`POLICY_REJECTED`、`SPATIAL_ERROR`、`SCHEDULER_ERROR`、`ROUTE_ERROR`、`VERIFICATION_ERROR`、`EXTERNAL_ADAPTER_ERROR`）。

Reality Source Metadata 是独立可审计数据：`LIVE MODEL`、`DETERMINISTIC RUNTIME`、`CONTROLLED EVIDENCE`、`POC SIMULATION`、`REPLAY`、`AUTH REQUIRED / NOT CONNECTED`。System Reality Matrix 由该 metadata、provider/configuration 与 authorization status 自动投影，覆盖模型、evidence、空间、调度、路线、机器人、电梯/Skybridge、验证、Replay、Delivery、ASR；不能由前端手改或伪造。Advanced 还应显示 Current PoC Boundaries、future adapter replacement points 与独立 Trace ID（不等于 Event ID），且绝不泄露密钥、token、authorization header 或环境变量值。

## 11. 不进入本轮与不允许的实现

Unified Implementation 已授权前后端、测试与文档变更，但仍禁止第二 UI System、Three.js、ROS/RMF、Docker/K8s、大型本地模型，以及让 Agent 或 Advanced 改基础设施配置。Batch C / Part 3 由后续 P1-H 承载，不提前混入 P1-A/P1-B。
