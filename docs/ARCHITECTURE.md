# AI 自主清洁 Demo｜当前架构与锁定目标

> **状态：IMPLEMENTED + LOCKED/TODO · 2026-08-29**
> 本文同时表达代码事实与下一实现目标；没有明确标为 IMPLEMENTED 的内容均不可据此宣称已完成。

## 1. 当前运行形态（IMPLEMENTED）

```text
React / Vite customer shell (/ and /prototype)
  ├── 自主清洁工作台
  │   ├── CameraMonitorGrid
  │   ├── SpatialDispatchView + campusTopology
  │   └── EventDetailPanel
  ├── Event Center / Analytics / Advanced（已有壳，非本批完整范围）
  ▼
FastAPI /api
  ├── demo_v1.service（阶段 Runtime）
  ├── perception/qwen（唯一云端 transport）
  ├── perception/multiview（受限 Agent）
  ├── spatial（地图、标定、Dijkstra）
  ├── scheduling（Capability Engine + Scheduler）
  └── SQLite（CleaningEvent / transitions / decisions / work orders）
```

## 2. 已实现的阶段边界（IMPLEMENTED / LOCKED）

```text
POST create event
  → edge-review
  → multi-view（仅 Demo02）
  → cloud-review（首次/必要时独立二审/Fusion）
  → locate
  → assign（Capability Engine + Scheduler）
  → start-navigation → complete-navigation → complete-cleaning
  → verify
  → CLOSED / HUMAN_REVIEW / HUMAN_FALLBACK
```

- 每个阶段保存 CleaningEvent 并 `record_transition`；Cloud、Scheduler、Verification 不得由未来/早期接口提前调用。
- `perception.qwen._request_qwen` 是唯一 DashScope transport。LLM 输出语义、置信度、能力建议和验收；**LLM 不选机器人**。
- `assignment_decision` 是前端行动机器人的唯一事实源。旧 `/api/demo-v1/runs/*` 已 RETIRED (410)。
- 受控 bbox 是 `CONTROLLED_EDGE_DEMO`，不是本地权重推理。

## 3. 锁定的最终运行链路（TODO）

```text
Fixed Camera
  → Edge YOLO / controlled edge evidence
  → conditional Multi-view Agent
  → Cloud Semantic Judgment
  → System Fusion + explicit veto
  → Camera→SLAM
  → Capability Engine
  → Scheduler
  → Dijkstra global topology path
  → Robot Execution
  → Fixed Camera After
  → Cloud target-aware Verification
  → CLOSED / HUMAN_REVIEW / HUMAN_FALLBACK
```

**CURRENT vs TARGET**：当前 `locate` 尚未把 bbox 接地点送入 `map_pixel_to_slam()`；当前 navigation plan 仍是演示锚点生成，尚未由共享 Fleet map + target map 调 `plan_route()`。二者必须先完成，才可称为真实空间 Runtime。

## 4. 空间与客户地图

**IMPLEMENTED 基础**：6 map、Global Spatial Graph、`map_pixel_to_slam()`、`plan_route()`、`campusTopology` 与 Robot C 演示锚点存在。

**LOCKED / TODO**：建立唯一 MapCanvas。白模 object-contain 的内层画布应成为所有 anchor、marker、robot、route 的唯一坐标系；动态物件不能使用外层元素百分比。定位完成前不得出现目标 marker。Scheduler 当前机器人位置和目标 SLAM map 进入 Dijkstra；前端仅把结果投影为路线。

Robot C 目标路线语义：B1F 待命 → B1F 电梯入口 → 乘梯暂停 → B2F 电梯出口 → B2F 连廊入口 → A2F 连廊出口 → A2F 易拉罐。任务后位置保留到 reset/new demo。

## 5. 云端、Fusion 与验收

- LIVE 调真实 Qwen；失败转 `HUMAN_REVIEW`，禁止 silent fallback。
- 首轮 `.50–.85` 时二审独立且不携带首轮答案；Fusion 与 raw confidence 分开，veto 优先。
- Stable Replay 是 **LOCKED/TODO**：只回放历史真实 AI 结构化输出，其余 Runtime 仍真实运行；只能由 Advanced 主动选择。
- Demo03 是 **LOCKED/TODO** 目标 ROI 验收：before/after 全图和 ROI、原类别/bbox；忽略机器人等非目标变化，必要时独立 ROI 二审。
- Demo04 是 **LOCKED/TODO** 零候选业务路径，不得 cloud 特判直接人工。

## 6. 数据契约与展示边界

SQLite 是状态、transition、assignment、human work order 的事实源。下一阶段需加入 Camera→SLAM 结果、真实规划路径、共享 Fleet 状态及真实 transition 时间。客户层中文化业务字段；Advanced 才显示 raw enum、pixel、planner、trace/latency 细节。

## 7. 不进入本批的模块

Event Center、Analytics、AI Assistant、Advanced 已有代码/壳不代表符合最新产品目标；它们在当前 Batch 不改造。禁止引入 ROS/RMF、Docker/K8s、第二 UI System、大型本地模型或真实设备接口。
