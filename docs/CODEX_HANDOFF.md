# Codex 交接｜从这里开始

> **状态：LOCKED · 2026-08-30**
> 新 Session 必须依次完整阅读：`PROJECT_CONTEXT.md`、`DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、本文件、`AI_INTEGRATION_TEST.md`；随后检查代码、`git status`、`git log`。不要用聊天记忆补全事实。

## 当前基线与授权状态

- 仓库：`ai-autonomous-cleaning-demo`；分支：`main`。
- P0 阶段 Runtime 已实现并做过技术回归：`e6b1eb9 feat: make integrated demo stage-driven`；它不能回退为一次性 `/runs` + 前端播放。
- 当前最新文档提交锁定了 Event Center、Analytics、Robot Operations Agent、外部配送边界与新的 Multi-view 架构；这些是 **LOCKED/TODO，不是 IMPLEMENTED**。
- **当前没有 implementation 授权。** 等待用户单独提供统一 implementation prompt；在此之前不得修改 frontend、backend、数据库、API、Runtime、模型、素材或测试，也不得擅自进入 Batch C / Part 3。

## 先理解的实现事实与文档冲突

1. 当前代码有基础 Event Center、Analytics、Optimization、Advanced 和 Multi-view，但它们不符合本轮 LOCKED 目标：基础 Event Center 不是复用的 history `EventDetailPanel`；Analytics 含演示 baseline / 固定聚合；Optimization 是确定性 mock recommendation；均不可称为最终产品。
2. 当前 Multi-view 是“灰区阈值 + 固定 coverage/frame/VLM 顺序”的受控 LangGraph 流程，且当前 Demo Runtime 可按 Demo 场景进入。它不符合新目标的 Single-view Cloud `evidence_sufficient` + `tool_choice=auto` 自主补证，不能写作完成。
3. 当前 `locate` 仍是模板 location，`navigation_plan` 仍是演示锚点，不是 bbox→`map_pixel_to_slam()` + Fleet current map→`plan_route()` Runtime。
4. 当前客户名称/产品资料仍是旧 mock 名称。实施时只能改显示投影与资料契约，保持内部 ID `robot-a` / `robot-b` / `robot-c` / `robot-d`。
5. 当前 Demo04 有 cloud 阶段直接人工分支；目标必须改为 Cloud → Locate → Capability zero candidate → `HUMAN_FALLBACK`。

## 不可违反规则

1. 机器人客户名称固定：赛特净界 S5、高仙 Omnie、蜗小白 SC50、普渡 FlashBot Max；Product Capability 与 Deployment Policy / Demo Configuration 必须分开。蜗小白 SC50 的地毯轻量垃圾是 Demo 配置，不是厂商原生公开宣称。
2. LLM 不能选机器人；Capability Engine + Scheduler 是唯一 `robot-a` / `robot-b` / `robot-c` 选择器，人工不是候选。FlashBot Max `cleaning capability = none`，不进 Cleaning Scheduler。
3. 首次 Cloud：`confidence >= 0.85` 不独立二审；`0.50 <= confidence < 0.85` 独立 targeted second review；`confidence < 0.50` 必须 `HUMAN_REVIEW`。LIVE 无云端可用时绝不 silent fallback；Replay 透明且不替代非 AI Runtime。
4. 新 Multi-view：主视角 Single-view VLM 先判断 `evidence_sufficient` / `ambiguity_type`；真实模型 `tool_choice=auto` 自主选择是否调用 evidence tools、哪 1–2 路、最多 2 rounds。禁止 `demo_id`、固定 threshold、强制 tool choice、初轮三图和前端假 Trace。
5. 新路线必须来自 Camera→SLAM + Dijkstra global topology planner / `plan_route()`，不得以 demo_id 固定；Demo03 固定 B1F→elevator→B2F→Skybridge→A2F carpet can；Demo04 必经 zero-candidate Human Fallback。
6. MapCanvas 是 white model、anchor、route、marker、robot 的唯一坐标系；终态机器人不自动回出生点；历史详情以 event-time snapshot 为准，不能由当前 Fleet 覆盖。
7. Event Center 是 read-only archive：正常 `HUMAN_FALLBACK` 绝不是异常；只复用 `EventDetailPanel(mode="history")`，保留 URL selected event 且不抢用户焦点。
8. 系统仅有 Multi-view Perception Agent 与 Robot Operations Agent 两个 Agent。后者可以在低风险白名单内做 task-level action / observe / replan，但绝不拥有地图、能力、Coverage、标定、Scheduler、阈值、速度、门禁、电梯等基础设施 Write Tool。
9. 一个 Robot Operations Agent：Workbench/Event Center 浮窗，Analytics 固定 Panel，Session/Audit/Task context 共享；语音只是 real ASR 输入。Analytics Advice 不是第三个 Agent，也不能自动改运营配置。
10. 不引入第二 UI System、Three.js、ROS/RMF、Docker/K8s、真实设备 runtime 或大型本地模型。

## 获得统一 implementation prompt 后的建议顺序

1. P1-A：机器人名称投影、bbox→Camera→SLAM、共享 Fleet、`plan_route()` Runtime、Demo04 zero candidate、真实 transition time、Stable Replay 最小控制区。
2. P1-B：MapCanvas、连续路线与终态、Workbench 布局/相机矩阵、统一 `EventDetailPanel`。
3. P1-C：新的 Single-view / evidence-sufficiency / tool-calling Multi-view Agent 与 Demo02 Trace/Audit。
4. P1-D：Event Center archive list、filters、history Drawer、URL state。
5. P1-E：Analytics data model、KPI、Heatmap、drill-down、真实利用率。
6. P1-F：Robot Operations Agent、Policy Guard、Task/Action Card、共享 UI、Analytics Advice、Delivery Adapter boundary。
7. P1-G：按测试事实源跑 LIVE / Replay / Event / Analytics / Agent 回归，并用代码、测试、浏览器证据更新六份文档。

## 代码定位（仅供核对现状）

- 阶段 Runtime：`backend/demo_v1/service.py`；API：`backend/api/routes.py`；SQLite：`backend/database/connection.py`。
- 云端：`backend/perception/qwen.py`；现有 Multi-view：`backend/perception/multiview/`。
- 空间：`backend/spatial/calibration.py`、`backend/spatial/route_planner.py`；调度：`backend/scheduling/`。
- 当前 Event Center/Analytics/Advanced：`frontend/src/components/prototype/PrototypeWorkbench.tsx`；当前 Event Detail：`frontend/src/components/prototype/EventDetailPanel.tsx`。
- 当前 Analytics / Optimization：`backend/analytics/`、`backend/optimization/`；当前操作展示：`backend/operations/`、`frontend/src/components/operations/`。

## 验收与文档纪律

实施前先将本文所列当前/目标差距映射为实际计划；未经用户授予 implementation 权限不得行动。实施后只在代码、测试、浏览器证据和用户验收都存在时，才把 TODO 变 IMPLEMENTED。每次代码改动更新六份事实源并 commit/push；如发现代码与 LOCKED 方案冲突，先记录并按用户授权处理，不要静默改变硬规则。
