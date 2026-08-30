# Codex 交接｜从这里开始

> **状态：LOCKED · 2026-08-30**
> 新 Session 必须依次完整阅读：`PROJECT_CONTEXT.md`、`DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、本文件、`AI_INTEGRATION_TEST.md`；随后检查代码、`git status`、`git log`。不要用聊天记忆补全事实。

## 当前基线与授权状态

- 仓库：`ai-autonomous-cleaning-demo`；实施分支：`codex/unified-implementation`；已验收文档基线：`00bd982982c81450e41f1755a3ba95be94c25b23`。
- P0 阶段 Runtime 已实现并做过技术回归：`e6b1eb9 feat: make integrated demo stage-driven`；它不能回退为一次性 `/runs` + 前端播放。
- 当前最新文档已锁定第一、二、三部分：Event Center、Analytics、Robot Operations Agent、外部配送边界、新 Multi-view 架构与 Advanced Technical Observability；这些是 **LOCKED/TODO，不是 IMPLEMENTED**。
- **Unified Implementation 已明确授权。当前只做 P1-A Closure。** 代码/新增测试/full backend/build/Reviewer A 与 E 必须全部 PASS 后才能将 P1-A 改 IMPLEMENTED，独立 commit/push 当前分支，再自动进入 P1-B。P1-A 代码、测试和 Reviewer A/E 已全部 PASS；独立提交推送后自动进入 P1-B；其余批次仍 LOCKED/TODO。

### 本轮交接：P1-A IMPLEMENTED · Reviewer A/E PASS

工作树已接入共享四点映射/Dijkstra/Fleet、结构化 spatial failure、合法 LIVE record replay、共用人工/机器人 verification，并增加真实子进程重启与 opt-in LIVE 测试。用户已明确 Demo04 两箱为废弃待清运，事实通过有来源/范围的 metadata→Scenario→Camera/Zone context 进入云端一/二审；结果与置信度不被硬编码。最新真实 Demo01、Demo04 LIVE与Replay均闭环，Demo04经过零候选人工完成及云端验收。旧失败只属于事实澄清前的历史记录。

先读 `AI_INTEGRATION_TEST.md` 本轮记录，再核对工作树与 Reviewers 的未解决项。测试使用独立临时 SQLite，不把测试 fixture 写入真实业务数据库；不打印密钥或 `.env`。最近请求错误不允许前端 effect 自动反复提交，Replay 标识跟随当前 event.mode 而不是下次选择。

## 先理解的实现事实与文档冲突

1. 当前代码有基础 Event Center、Analytics、Optimization、Advanced 和 Multi-view，但它们不符合本轮 LOCKED 目标：基础 Event Center 不是复用的 history `EventDetailPanel`；Analytics 含演示 baseline / 固定聚合；Optimization 是确定性 mock recommendation；均不可称为最终产品。
2. 当前 Multi-view 是“灰区阈值 + 固定 coverage/frame/VLM 顺序”的受控 LangGraph 流程，且当前 Demo Runtime 可按 Demo 场景进入。它不符合新目标的 Single-view Cloud `evidence_sufficient` + `tool_choice=auto` 自主补证，不能写作完成。
3. 旧基线的模板 locate / 演示锚点路线已由 P1-A 改为 bbox→共享 `map_pixel_to_slam()` + Fleet current map→`plan_route()`；P1-A 工程验收已通过，唯一 MapCanvas 的视觉改造尚未进入 P1-B。
4. P1-A 的共享 Fleet 已有正式名称及 product_capability / demo_configuration，主工作台外仍有旧静态 mock 文案待清理；保持内部 ID `robot-a` / `robot-b` / `robot-c` / `robot-d`。
5. Demo04 cloud 直接人工分支已删除，当前阶段 Runtime 只允许 Capability zero candidate 产生 HUMAN_FALLBACK；用户确认 context 后，真实完整路径与 Replay 已通过。
6. 当前 Advanced 只是技术状态卡片 + 当前事件 JSON 的基础 shell；没有 Trace Inspector、node detail、structured Tool Audit、Reality Matrix、错误分类或 Trace ID，不能称为 Batch C 已完成。

## 不可违反规则

1. 机器人客户名称固定：赛特净界 S5、高仙 Omnie、蜗小白 SC50、普渡 FlashBot Max；Product Capability 与 Deployment Policy / Demo Configuration 必须分开。蜗小白 SC50 的地毯轻量垃圾是 Demo 配置，不是厂商原生公开宣称。
2. LLM 不能选机器人；Capability Engine + Scheduler 是唯一 `robot-a` / `robot-b` / `robot-c` 选择器，人工不是候选。FlashBot Max `cleaning capability = none`，不进 Cleaning Scheduler。
3. Evidence Sufficiency Gate 高于最终 confidence disposition：Single-view `evidence_sufficient=false` 且 reflection / occlusion / perspective / lens_contamination / insufficient_view 可被合法 supporting camera 缓解时，先以 `tool_choice=auto` 补证，即使 raw confidence `<0.50` 也不得提前 `HUMAN_REVIEW`。最终充分 evidence 后：`confidence >= 0.85` 不独立二审；`0.50 <= confidence < 0.85` 独立 targeted second review；`confidence < 0.50` 为 `HUMAN_REVIEW`。没有合法 camera、fetch 失败、最多 2 rounds 后仍不充分、或最终不充分即使 raw confidence 高，均为 `HUMAN_REVIEW`。二审可读本次合法 evidence set，不得读上一轮答案/reasoning。LIVE 无云端可用时绝不 silent fallback；Replay 透明且不替代非 AI Runtime。
4. 新 Multi-view：主视角 Single-view VLM 先判断 `evidence_sufficient` / `ambiguity_type`；真实模型 `tool_choice=auto` 自主选择是否调用 evidence tools、哪 1–2 路、最多 2 rounds。禁止 `demo_id`、固定 confidence threshold、强制 tool choice、初轮三图和前端假 Trace。
5. 新路线必须来自 Camera→SLAM + Dijkstra global topology planner / `plan_route()`，不得以 demo_id 固定；Demo03 固定 B1F→elevator→B2F→Skybridge→A2F carpet can；Demo04 必经 zero-candidate Human Fallback。
6. MapCanvas 是 white model、anchor、route、marker、robot 的唯一坐标系；终态机器人不自动回出生点；历史详情以 event-time snapshot 为准，不能由当前 Fleet 覆盖。
7. Event Center 是 read-only archive：正常 `HUMAN_FALLBACK` 绝不是异常；只复用 `EventDetailPanel(mode="history")`，保留 URL selected event 且不抢用户焦点。
8. 系统仅有 Multi-view Perception Agent 与 Robot Operations Agent 两个 Agent。后者可以在低风险白名单内做 task-level action / observe / replan，但绝不拥有地图、能力、Coverage、标定、Scheduler、阈值、速度、门禁、电梯等基础设施 Write Tool。
9. 一个 Robot Operations Agent：Workbench/Event Center 共享浮窗，无 localStorage 保存位置时默认左下角，保存位置优先；只可从 Header/Drag Handle 拖动、不能出 viewport，展开/收起/跨页/刷新保持。Analytics 固定 Panel，Session/Audit/Task context 共享。语音只是 Microphone → real ASR → transcript 输入，不是主演示路径；ASR 未配置时麦克风 disabled 或显示“语音服务未配置”，不得伪造 transcript。Analytics Advice 不是第三个 Agent，也不能自动改运营配置。
10. 不引入第二 UI System、Three.js、ROS/RMF、Docker/K8s、真实设备 runtime 或大型本地模型。
11. Advanced 是 read-mostly Technical Observability & Execution Trace Inspector，不是 Admin / Configuration。它只投影真实 Runtime records，不能重跑模型/Scheduler/Route，不能编辑 SLAM、标定、Coverage、范围、Capability、Scheduler/threshold/topology、安全、门禁、电梯或 Agent tool permission。
12. Advanced 四个模块固定：AI Recognition Trace（六段）、Spatial/Capability/Scheduling/Route Trace（四段）、Runtime/Model/Tool/Error Observability、System Reality Matrix。关键来源使用 `LIVE MODEL`、`DETERMINISTIC RUNTIME`、`CONTROLLED EVIDENCE`、`POC SIMULATION`、`REPLAY`、`AUTH REQUIRED / NOT CONNECTED`；不得 fake trace/tool/latency/error/badge/model status/reality status，也不得展示 Chain-of-Thought 或任何 secret。

## 获得统一 implementation prompt 后的建议顺序

1. P1-A：机器人名称投影、bbox→Camera→SLAM、共享 Fleet、`plan_route()` Runtime、Demo04 zero candidate、真实 transition time、Stable Replay 最小控制区。
2. P1-B：MapCanvas、连续路线与终态、Workbench 布局/相机矩阵、统一 `EventDetailPanel`。
3. P1-C：新的 Single-view / evidence-sufficiency / tool-calling Multi-view Agent 与 Demo02 Trace/Audit。
4. P1-D：Event Center archive list、filters、history Drawer、URL state。
5. P1-E：Analytics data model、KPI、Heatmap、drill-down、真实利用率。
6. P1-F：Robot Operations Agent、Policy Guard、Task/Action Card、共享 UI、Analytics Advice、Delivery Adapter boundary。
7. P1-H：在现有 Advanced shell 上实现只读 Trace Inspector、六段 AI Trace、四段空间/调度 Trace、Runtime Strip、统一 Tool/Error Trace、Reality Matrix、Trace ID、PoC boundary / Adapter points 与安全验收。
8. P1-G：在 P1-H 之后，按测试事实源跑最终 LIVE / Replay / Event / Analytics / Agent 回归，并用代码、测试、浏览器证据更新六份文档。

## 代码定位（仅供核对现状）

- 阶段 Runtime：`backend/demo_v1/service.py`；API：`backend/api/routes.py`；SQLite：`backend/database/connection.py`。
- 云端：`backend/perception/qwen.py`；现有 Multi-view：`backend/perception/multiview/`。
- 空间：`backend/spatial/calibration.py`、`backend/spatial/route_planner.py`；调度：`backend/scheduling/`。
- 当前 Event Center/Analytics/Advanced：`frontend/src/components/prototype/PrototypeWorkbench.tsx`；当前 Event Detail：`frontend/src/components/prototype/EventDetailPanel.tsx`。
- 当前 Analytics / Optimization：`backend/analytics/`、`backend/optimization/`；当前操作展示：`backend/operations/`、`frontend/src/components/operations/`。

## 验收与文档纪律

实施前先将本文所列当前/目标差距映射为实际计划。Advanced 所展示的任何步骤必须回溯 backend record / response / audit / transition，绝不前端伪造。本轮按用户 P1-A Closure 明确条件：代码、新增测试、full backend、build、Reviewer A/E 全部 PASS 后才标 IMPLEMENTED、独立 commit/push；未通过时保留 WIP。最终用户产品验收不由工程测试代替。如发现代码与 LOCKED 方案冲突，先记录并按用户授权处理，不要静默改变硬规则。
