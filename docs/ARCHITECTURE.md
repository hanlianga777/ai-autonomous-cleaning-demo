# AI 自主清洁 Demo｜当前架构

> **状态：IMPLEMENTED + PARTIAL · 2026-08-29**
> 本文描述当前代码实际存在的模块，不把目标架构当作完成事实。

## 1. 运行形态

```text
React / Vite customer shell (/ and /prototype)
  ├── 自主清洁工作台
  │   ├── CameraMonitorGrid（两路监控、受控 bbox）
  │   ├── SpatialDispatchView（白模 + SVG/DOM 路线 + 机器人图层）
  │   └── EventDetailPanel（右侧时间线、证据、验收）
  ├── 事件中心（SQLite 列表 + 独立简化 Drawer）
  ├── 运营分析（30 天基线 + SQLite 增量）
  └── 高级模式（运行状态与技术审计）
             │
             ▼
FastAPI /api
  ├── demo_v1.service（客户演示组合层）
  ├── perception / qwen（唯一云端传输）
  ├── spatial（地图、标定、路由）
  ├── scheduling（Capability Engine + Scheduler）
  ├── workflow（Phase 3 审计状态机）
  ├── analytics（演示历史聚合）
  └── SQLite（CleaningEvent / transitions / decisions）
```

## 2. 感知、门控与调度

```text
受控边缘证据（bbox + 固定置信度，非真实 YOLO）
  → 首次云端大模型语义研判
  → [0.50–0.85] 独立二次云端复核
  → Evidence Fusion Composite Disposal Score
  → 绝对 veto 检查（need_clean=false / unknown / ignore）
  → TaskProfile
  → Capability Engine
  → Scheduler / assignment_decision
  → 云端清洁后验收
```

**IMPLEMENTED**：`backend/perception/qwen.py::_request_qwen` 是唯一 DashScope OpenAI-compatible HTTP transport。`run_event_qwen_vl` 和 `run_targeted_event_qwen_vl` 共享 schema/transport；后者不接收首轮答案。`backend/demo_v1/service.py` 计算融合分数并复用既有 Capability Engine/Scheduler。

**PARTIAL**：首次多图 Prompt 未写清“三图同地点/同时间/同地面区域”；前端时间线在 API 返回完整结果后以 `setTimeout` 推进，不能视为后端逐阶段真实执行。

## 3. 数据与持久化

- **IMPLEMENTED**：`database/connection.py` 存储 `cleaning_events`、`event_transitions`、assignment decisions 与 human fallback work orders。
- **IMPLEMENTED**：`demo_v1.service._persist_demo_result` 每次运行写入 CleaningEvent 和审计 transition；`analytics.service.task_history()` 将 `integrated-*` 事件叠加到 30 天/300 条演示历史。
- **PARTIAL**：客户 Event Center 没有复用工作台详情组件；Analytics 的部分客户分析/助手为前端占位，不是云端 Assistant。

## 4. 空间与路线

**IMPLEMENTED 基础**：6 map（OUTDOOR、A_B1、A_1F、A_2F、B_1F、B_2F）、Global Spatial Graph、Dijkstra/A*、Coverage、CAM-A1-01 四点映射在 `backend/spatial/`。

**PARTIAL 客户投影**：`SpatialDispatchView.tsx` 用归一化 display coordinates 和本地 SVG 路线。视觉上包含 Robot C 的电梯/连廊阶段，但不直接消费完整 Phase 2 路径拓扑，也主要读取 `scenario.robot` 而非 `assignment_decision`。因此地图并非真实导航投影。

## 5. 素材与证据

- 摄像头素材：`sample_data/camera_events/<camera>/<event>/`，FastAPI 通过 `/demo-assets` 静态提供。
- Demo04 after 图：`CAM-A2-11/event-oversized-box-004/after.png`，只用于人工完成后的云端验收。
- 园区白模与机器人图片：`frontend/public/visual-assets/`；Robot A 为用户 2×2 原图左上象限裁切，B/C/D 保持原素材。
- bbox 保持与 1448×1086 原图相同的归一化坐标，在 `CameraViewport` 的 object-contain 内层渲染。

## 6. API 边界

| API | 当前状态 | 说明 |
|---|---|---|
| `GET /api/health`、`GET /api/dashboard` | IMPLEMENTED | Phase 1 健康与基础数据 |
| `POST /api/demo-v1/runs/{demoId}` | IMPLEMENTED / PARTIAL | 真实云端组合与 SQLite 写入；非逐阶段执行 API |
| `POST /api/demo-v1/manual-work-orders/{event_id}/complete` | IMPLEMENTED | Demo04 人工完成后调用真实云端验收 |
| `GET /api/events` | IMPLEMENTED / PARTIAL | 可查 SQLite，但客户字段/详情复用不足 |
| `GET /api/analytics/overview` | IMPLEMENTED | 程序聚合演示基线 + 增量 |
| `/api/optimization/recommend` | IMPLEMENTED（旧 Optimization Agent） | 不等于当前客户页“重新分析”已接真实云端模型 |

## 7. 安全与运行

- `DASHSCOPE_API_KEY` 只从本地环境读取，绝不写入响应、日志、Git 或客户页面。
- Key/权重不在 Git；Custom YOLO 当前只作为离线实验，禁止接入客户主链路。
- 真实机器人、电梯、Skybridge 与遥测均是模拟/演示边界，不能宣传为生产接入。
