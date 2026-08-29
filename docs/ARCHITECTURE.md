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

`confidence` 与 `evidence_sufficient` 必须是不同输出。首次 Cloud 的自动处置门控固定为 `confidence >= 0.85` 不独立二审、`0.50 <= confidence < 0.85` 独立 targeted second review、`confidence < 0.50` 为 `HUMAN_REVIEW`；而是否 Multi-view 由单视角证据是否充分与歧义类型决定，不能仅由 confidence 决定。

**CURRENT vs TARGET**：当前 `locate` 尚未把 bbox 接地点送入 `map_pixel_to_slam()`；当前 navigation plan 仍是演示锚点生成；当前 Multi-view 是固定灰区工具序列，且初轮可使用多图上下文。三者完成前均不能宣称真实空间 Runtime 或真实主动视觉取证。

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

浮窗只能从 Header/Drag Handle 拖动，不能超 viewport，并跨页面与刷新保留位置；Analytics 仅显示固定 Panel，不与 Floating Window 重复。语音只是同一 Agent 的 real ASR 输入适配，不是独立 Agent。

## 9. External Delivery Adapter（LOCKED / TODO）

清洁仍是主业务。未获得平台授权、资质与 API 权限时，Delivery Adapter 只能显示 `ADAPTER READY` / `AUTH REQUIRED`；不得声称 `CONNECTED` 或伪造 platform callback。授权后，结构化订单走确定性 Adapter / POI normalization / Policy / Delivery Workflow / FlashBot Max / status callback；不确定例外才升级给 Robot Operations Agent。

## 10. 不进入本轮与不允许的实现

本轮不实现任何前后端或测试变更。未来统一 implementation batch 也禁止第二 UI System、Three.js、ROS/RMF、Docker/K8s、大型本地模型，以及让 Agent 改基础设施配置。Batch C / Part 3 pending discussion，尚无实施授权。
