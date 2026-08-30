# Codex 交接｜从这里开始

> **状态：LOCKED · 2026-08-30**
> 新 Session 必须依次完整阅读：`PROJECT_CONTEXT.md`、`DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、本文件、`AI_INTEGRATION_TEST.md`；随后检查代码、`git status`、`git log`。不要用聊天记忆补全事实。

### 最新交接：P1-E IMPLEMENTED · A/E PASS

P1-A `fcd01d4`、P1-B `b2a1899`、P1-C `c9cf220`、P1-D `a350ad5` 已推送。E代码、12定向/102后端PASS+3skip/32前端/build/浏览器与A/E均PASS，独立提交后继续 **P1-F**，不合并main。F/H/G尚未实施完成。

E注意：启动会幂等插入标明DEMO_HISTORY的演示档案，不能将其当作真实AI。利用率可用时长仅PoC连续可用假设，不是生产uptime；人工缺开始时刻的响应样本排除。旧optimization API仍为待F替换的技术遗留，客户Analytics不展示固定建议或假对话。

### P1-C 已完成交接： IMPLEMENTED · A/E PASS

P1-A `fcd01d4`、P1-B `b2a1899` 已在 `codex/unified-implementation`。本轮 P1-C 完成，独立提交 `c9cf220` 后已进入 P1-D，无需重新向用户询问授权；仍不得提前合并 main。22 项定向、86 后端 PASS + 3 opt-in skipped、前端17/build、真实 Demo02 LIVE→Replay 与浏览器均通过。后续最终五次稳定性等仍 P1-G TODO，不把本轮两次真实成功等同全部终验。

关键实现：`autonomous.py` 真实 tool_choice=auto；`perception_records.py` 只回放 provider response，工具/policy仍真实跑；first single-view不足即使 confidence<0.50 也先合法补证；最终不足不能自动派发。Demo02 原图清晰未触发补证是正确行为，因此新增透明的受控模糊 variant（原图保留），不是 fixed confidence 或假 trace。model configurable，原用户 .env 未改。

请先读测试事实源最新 P1-E 记录、检查 git log/status，再继续 F；不要回到旧 demo02 先固定多图后 Cloud 路径。P2：6 model turns 不是6取证轮次；旧技术AI Lab兼容路径/生产同步/跨标签页幂等未因本轮自动升级。影像版本与完整编辑提示记录在测试事实源。

## 当前基线与授权状态

- 仓库：`ai-autonomous-cleaning-demo`；实施分支：`codex/unified-implementation`；已验收文档基线：`00bd982982c81450e41f1755a3ba95be94c25b23`。
- P0 阶段 Runtime 已实现并做过技术回归：`e6b1eb9 feat: make integrated demo stage-driven`；它不能回退为一次性 `/runs` + 前端播放。
- 当前 Robot Operations Agent、外部配送边界、Advanced Technical Observability 仍为 **LOCKED/TODO**；新 Multi-view 已按 P1-C **IMPLEMENTED**，不得与其它未实现目标混写。
- **Unified Implementation 已明确授权。P1-A `fcd01d4`、P1-B `b2a1899` 已提交推送，P1-C `c9cf220` 与 P1-D 工程验收 PASS，P1-D `a350ad5` 已提交，P1-E工程PASS后独立提交，再进入P1-F。** P1-C 最新测试见页首；P1-F/H/G 仍 LOCKED/TODO，最终产品验收未完成。

### 最新交接：P1-B MapCanvas / 统一详情工程完成

唯一 MapCanvas 与影像 object-contain 内层平面、Dijkstra 路线连续插值/入口停留、正式 Fleet 资产栏、完整 before/after 双监控、同一 EventDetailPanel live/history 已完成。历史只 GET 事件快照，不调用 runtime。工作台刷新仅用保存的 event ID GET 恢复，session request keys 防止同会话重复请求；外来/倒退快照被拒绝，网络不确定不自动重试模型。不要把该浏览器防重等同服务器端幂等。

实际浏览器 Demo04 LIVE 再次经 zero candidate→人工完成→verification CLOSED。Demo03 真实跨楼路线通过但云端 after 验收拒绝，正确保留终点/路线/全时间线并进入 HUMAN_REVIEW；这是待 P1-G 收敛的 ROI 验收限制，不能写为四 Demo 均已最终通过。P1-B 只改变前端和文档，未调整 Scheduler、Capability 或 Cloud gate。

### 本轮交接：P1-A IMPLEMENTED · Reviewer A/E PASS

工作树已接入共享四点映射/Dijkstra/Fleet、结构化 spatial failure、合法 LIVE record replay、共用人工/机器人 verification，并增加真实子进程重启与 opt-in LIVE 测试。用户已明确 Demo04 两箱为废弃待清运，事实通过有来源/范围的 metadata→Scenario→Camera/Zone context 进入云端一/二审；结果与置信度不被硬编码。最新真实 Demo01、Demo04 LIVE与Replay均闭环，Demo04经过零候选人工完成及云端验收。旧失败只属于事实澄清前的历史记录。

先读 `AI_INTEGRATION_TEST.md` 本轮记录，再核对工作树与 Reviewers 的未解决项。测试使用独立临时 SQLite，不把测试 fixture 写入真实业务数据库；不打印密钥或 `.env`。最近请求错误不允许前端 effect 自动反复提交，Replay 标识跟随当前 event.mode 而不是下次选择。

## 先理解的实现事实与文档冲突

1. P1-B 已将 Event Center 详情改为复用 history `EventDetailPanel`；列表/URL/完整分类已在 P1-D 实现。Analytics 已按P1-E改为同库事件/transition真实聚合；旧Optimization固定推荐API留待P1-F，客户页不展示。
2. 主 Runtime 已完成 P1-C single-view→evidence gate→真实 model auto-tool 自主补证；旧受控 LangGraph 仅遗留技术路径，不再从主 Demo 路径进入，不可混淆两者。
3. 旧基线的模板 locate / 演示锚点路线已由 P1-A 改为 bbox→共享 `map_pixel_to_slam()` + Fleet current map→`plan_route()`；P1-B 唯一 MapCanvas 已接入这些事实并通过浏览器验收；不再使用旧外层独立路线投影。
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
7. Event Center 是 read-only archive：正常 `HUMAN_FALLBACK` 绝不是异常。P1-B 已复用 `EventDetailPanel(mode="history")`；正确五类过滤、URL selected event、新记录不抢用户焦点已在 P1-D 实现；不能宣称最终产品验收已完成。
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
