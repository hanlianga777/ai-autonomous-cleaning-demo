# AI 自主清洁 Demo｜项目事实源

> **状态：IMPLEMENTED 基线 + LOCKED/TODO · 2026-08-30**
> 本文件与 `DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、`CODEX_HANDOFF.md`、`AI_INTEGRATION_TEST.md` 是后续 Session 的唯一外部事实源。必须先读完六份文件，再读代码、`git status`、`git log`；聊天记录和旧 Prompt 不可替代事实源。

## 最新工程状态：P1-F IMPLEMENTED · A/E PASS（2026-08-30）

P1-A/B/C/D/E 已独立提交推送（最新 E `4c6a8a8`）；P1-F 完成共享 Robot Operations Agent、代码级工具白名单、持久化 Task/Fleet/Audit，以及原生 PoC 配送与待命。实际云端工具调用已创建/派发待命与配送任务，操作员推进后 CLOSED；不是预设自然语言回复。P1-H/G 尚未完成，不提前合并 main。

清洁任务只关联现有合法集成事件，复用 Cloud → Camera→SLAM → Capability/Scheduler → Verification；Agent 不选清洁机器人、不生成坐标。配送仅 robot-d 原生 POC SIMULATION：显式室内/电梯/连廊模拟权限不等于生产授权；四个平台 Adapter 仍 AUTH REQUIRED。ASR 未配置，麦克风 disabled。

Session、Task、Action Audit 与建议缓存位于同一 SQLite。Workbench/Event Center 共享左下角浮窗；Analytics 固定同一聊天与只读建议区。仅显式重新生成才调用建议模型；旧固定 Optimization 入口已 410。模型/工具失败保留错误与已发生任务，不自动 Replay 或伪造成功。生产身份、多 worker 分布式队列/硬件命令、真实机器人/ASR 仍不在当前完成范围。

## P1-E 已完成记录： IMPLEMENTED · A/E PASS（2026-08-30）

P1-A `fcd01d4`、P1-B `b2a1899`、P1-C `c9cf220`、P1-D `a350ad5` 已推送实施分支。P1-E 已接入同一 SQLite 的结构化 DEMO_HISTORY 与 Runtime 增量，5 KPI 明确分母；热图与档案共用坐标/筛选，利用率由任务区间取并集计算。代码/测试/浏览器与 A/E 工程审查通过；提交状态见交接。P1-H/G 仍 TODO，不提前合并 main。

演示历史由应用启动时幂等写入，显式 `DEMO_HISTORY`，不生成模型调用/真实置信度，不改变 Fleet，不可冒充 LIVE。缺失实际人工开始观察时响应时间为空。可用时长目前为“PoC 假定连续24小时可用”的分析归一化假设，不是观测到的生产 uptime；后续实际availability provider可替换，不改 Scheduler。

## P1-C 已完成记录：IMPLEMENTED（2026-08-30）

P1-A `fcd01d4`、P1-B `b2a1899` 已分别推送实施分支；P1-C 本轮完成代码、22 项定向测试、完整后端 86 PASS + 3 opt-in skipped、前端 17/17 与 build、实际浏览器 LIVE/Replay、Reviewer A/E PASS。已独立提交 `c9cf220`；P1-H/G 仍 TODO，最终用户产品验收未完成。

主 Runtime 已移除按 Demo02/固定 confidence 强制 Multi-view：单图云端返回 evidence_sufficient/ambiguity，再由真实 `qwen3-vl-plus`（`DASHSCOPE_AGENT_MODEL` 可配置）以 `tool_choice=auto` 选择合法补图。单图/独立二审仍使用 `DASHSCOPE_VL_MODEL`，未改现有用户 .env。原 Demo02 图过于清晰，真实模型不触发补证；按 Unified §71 允许的 evidence 优化，新增保留原图的 `primary-ambiguous-v2.png`，仅模拟主相机局部成像模糊，明确 CONTROLLED EVIDENCE。不预设模型 confidence、need_action 或工具选择。具体实跑数值仅在测试事实源记录。

## 1. 产品目标与当前授权边界

这是面向 AI 解决方案专家岗位面试的园区自主清洁 PoC：固定摄像头发现地面事件，受控边缘证据提供候选，云端模型做语义理解，确定性空间/能力/调度系统决定处置，固定摄像头 + 云端验收形成可解释闭环。

产品由同一套 `CleaningEvent`、SQLite transition 与 Fleet / route snapshot 支撑四个一级页面：

- **自主清洁工作台（Workbench）**：回答“现在正在发生什么”。
- **AI 事件处置档案中心（Event Center）**：回答“一个事件如何发生、为何这样处置、如何闭环”。
- **AI 自主清洁运营分析中心（Analytics）**：回答“历史事件整体说明什么、下一步应如何优化”。
- **Advanced Technical Observability / 高级模式**：回答“系统如何运行、哪些记录与能力是真实、确定性、受控证据或 PoC 模拟”。

用户已授予 **Unified Implementation** 权限，工作分支为 `codex/unified-implementation`，已验收文档基线为 `00bd982982c81450e41f1755a3ba95be94c25b23`。P1-A 已独立提交并推送 `fcd01d4`；P1-B 代码、17 项前端测试、完整后端回归、构建、浏览器检查与 Reviewer A/E 均 PASS（工程 IMPLEMENTED），随后独立提交。P1-C 已工程完成（见上节）；P1-H/G 仍为后续任务，最终用户产品验收未被工程 PASS 替代。

本轮已补齐版本化 AI response Replay、空间失败保护、共享 Fleet 与重启测试。用户已确认 Demo04 两纸箱是废弃待清运物品；该事实作为 event-scoped Scenario / Camera / Zone Context 传给云端，不写死输出。真实 Demo01 与 Demo04 均完成 LIVE→持久化→Replay 闭环；Demo04 人工兜底只由 Capability zero candidate 产生。旧失败保留为历史，测试证据见 `AI_INTEGRATION_TEST.md`。

真实生产机器人、电梯、近同步多摄像头、RTSP/VMS/NVR、平台授权、动态避障和生产阈值均未部署；A/B 楼、电梯、Skybridge 与机器人执行是 PoC 模拟。受控 bbox 不是本地真实 YOLO 权重推理，禁止对外声称 REAL YOLO 已通过。

## 2. 机器人命名、产品能力与 Demo 配置

内部技术 ID 固定为 `robot-a`、`robot-b`、`robot-c`、`robot-d`，客户名称不得改变内部 ID。

| 内部 ID | 客户名称 | Product Capability（公开资料可合理验证的产品定位） | Deployment Policy / Demo Configuration Capability（本 PoC 人为配置） |
|---|---|---|---|
| `robot-a` | 赛特净界 S5 | 室外道路 / 广场类清扫产品定位。 | 仅处理室外道路、广场、其他小型干垃圾和树叶。 |
| `robot-b` | 高仙 Omnie | 高能力洗扫 / 室内重清洁产品定位。 | 优先处理液体污渍、较重室内清洁；Demo02 液体污渍优先匹配。 |
| `robot-c` | 蜗小白 SC50 | 楼宇室内清洁产品定位。 | 楼栋室内轻量清洁；支持瓷砖，**本 Demo 配置为支持地毯区域轻量垃圾清洁**，处理纸屑、杯子、易拉罐、小瓶等；弱化重液体处理；允许经楼内跨层与 A2F–B2F Skybridge 执行。 |
| `robot-d` | 普渡 FlashBot Max（闪电匣 · 楼宇配送机器人） | 楼宇配送产品定位。 | P1-F原生配送PoC资产，`cleaning capability = none`，不参与 Cleaning Scheduler。 |

“地毯区域轻量垃圾清洁”是 Demo Configuration，不是对蜗小白 SC50 厂商原生能力的公开宣称。Product Capability 与 Deployment Policy 必须始终分开表述。

## 3. 当前已实现事实（IMPLEMENTED）

- React/Vite/Tailwind/shadcn、FastAPI/SQLite、6 张模拟 SLAM map、Global Spatial Graph、Camera Coverage、四点标定、Dijkstra global topology planner / `plan_route()`、Phase 3 Capability Engine + Scheduler 均存在。
- `demo_v1` 是阶段 REST Runtime：create → edge → cloud-review（single-view → evidence gate → optional multi-view → final gate）→ locate → assign → navigation → cleaning → verify；每步写入 SQLite `CleaningEvent` transition。旧 `/runs/*` 一次性入口为 410。
- 云端调用统一经 `perception.qwen._request_qwen`；已有一次 Cloud 与独立 targeted second review/Fusion 的代码边界。`confidence >= 0.85` 不独立二审；`0.50 <= confidence < 0.85` 独立二审；`confidence < 0.50` 转 `HUMAN_REVIEW`。
- P1-C 主 Runtime 已完成 evidence-sufficiency 驱动的真实 model auto-tool 自主补证；旧受控 LangGraph 仅为遗留技术路径，不能当作主工作台当前执行链路。
- P1-B Event Center 已复用同一只读历史 `EventDetailPanel`，列表/过滤/URL 产品化已在 P1-D 实现。Analytics 已按P1-E读取同库结构化演示历史与Runtime真实聚合；P1-F已退役旧固定Optimization入口(410)，客户页使用共享Operations Agent的真实只读建议。
- 当前 Advanced 是技术状态卡片 + 当前事件 JSON 的基础 shell；它不具备最终 Trace → Node → Inspect、结构化 audit、Reality Matrix 或错误分层，不得称为 Advanced Trace Inspector。
- P1-B 的唯一 MapCanvas 使用 object-contain 内层平面，投影已存 SLAM target、Fleet 和 Dijkstra node_path；路线起点读 ASSIGNED 快照，终态位置读 Fleet 快照。连续移动是明确标识的 PoC 视觉插值，不是设备遥测。无后端路线不画假路线。
- Demo01、Demo02 三次、Demo04 人工完成后曾真实 CLOSED；Demo03 曾真实选中 `robot-c`，但验收为 `retry → HUMAN_REVIEW`。完整原始记录见测试事实源。

## 4. 四个 Demo 的锁定故事

| Demo | 锁定业务事实 | 正常目标 |
|---|---|---|
| 01 | 室外、**其他小型垃圾**、赛特净界 S5、before/after | 自动闭环 |
| 02 | A栋 1F 高反光地面疑似液体污渍；主摄像头 `CAM-A1-01` 的受控 YOLO 58%；`CAM-A1-02` / `CAM-A1-04` 是受控补充证据资产（63% / 61%） | Single-view Cloud 先作 Evidence Sufficiency Judgment；若证据不足且可由合法补充视角缓解，先由模型自主请求 Multi-view，再以最终充分证据进入 confidence disposition，最终由高仙 Omnie 自动闭环 |
| 03 | A栋 2F 地毯易拉罐；蜗小白 SC50 从 B1F 经电梯、B2F、Skybridge 至 A2F；after 有约 3m 外机器人 | 目标 ROI 验收后闭环 |
| 04 | A栋 2F 逃生/通道附近两纸箱、**废弃待清运的大件物品（不是合法暂存/补货/待使用物资）**；A/B/C 无搬运能力 | Cloud → Locate → Capability Engine 零候选 → `HUMAN_FALLBACK` → 人工搬运 → after → AI 验收 → CLOSED |

客户业务名称固定：`small_litter → 其他小型垃圾`、`liquid → 液体污渍`、`can → 易拉罐`、`large_object → 大件物品`、`leaf → 树叶`。旧“地面纸巾”“大型纸箱”等过度具体面客类目已废弃。Demo01 的 LIVE confidence 不是锁定业务事实；历史 `.81 → .95 → Fusion .89` 仅能在 `AI_INTEGRATION_TEST.md` 中作为历史记录出现。

## 5. LOCKED 产品结构（P1-B 范围已实现，其余仍 TODO）

### Workbench 与统一 Event Detail（P1-B 工程 IMPLEMENTED）

- 左主区约 72%、右事件详情约 28%；左上双固定摄像头约 31%、SLAM/空间调度地图约 69%。地图是视觉主角，摄像头是感知入口；右详情从全局 Header 下沿开始、顶部贴齐、独立滚动。
- 白模、Topology Anchor、机器人、路线、事件 marker 必须共享唯一 **MapCanvas** 坐标系，基于 `object-contain` 内层真实画布；不能以外层 container 百分比独立定位。
- `EventDetailPanel` 是全产品唯一事件详情标准：`mode="live"` 动态跟随 Runtime，`mode="history"` 只读展示事件发生当时 snapshot，绝不重跑模型、Scheduler 或机器人；字段、卡片、图片、顺序、颜色和 stage hierarchy 一致。

### Event Center（P1-D IMPLEMENTED）

定位为 **AI Event Handling Archive Center / AI 事件处置档案中心**，不是普通告警列表。复用同一 `CleaningEvent` / SQLite，不得维护独立 Mock 数据。主状态固定为：全部、处理中、已自主闭环、待人工处理、异常；正常 `HUMAN_FALLBACK` 是合理业务兜底，绝不是异常。详情从紧凑两级 Event List 右侧以约 42–46% 宽历史 `EventDetailPanel` 打开；`/events?event=EVT-xxxx` 保存选中状态，刷新可恢复，首次进入不自动打开第一条。

### Analytics

定位为 **AI Autonomous Cleaning Operations Analysis Center / AI 自主清洁运营分析中心**，而非传统物业驾驶舱。三层是 Autonomy Outcome、Operational Efficiency、Optimization Advice；顶部 5 KPI 固定为自主闭环率、人工介入率、首次处置成功率、平均响应时间、平均闭环时间，均由后端 `CleaningEvent` / transition 真实计算。主视觉是复用园区/SLAM white model 的 30 天空间事件热力图，数据源为明确标识的“30 天结构化 Demo Historical Baseline + 当前 Runtime CleaningEvent Increment”，不能冒充客户真实历史。

### Robot Operations Agent

唯一的运营与自然语言任务编排层：Workbench / Event Center 使用同一个可拖动 Floating Window；没有已保存 UI position 时默认在左下角，用户拖动后的 localStorage 位置优先；Analytics 改用右侧固定 Agent Panel；三页共享 `AgentSession`、Action Audit、Task context，只随 Page Context 改变呈现。它有任务级自主权，不具有基础设施级配置权；具体界限见 `DECISIONS.md` 与 `ARCHITECTURE.md`。

### Advanced Technical Observability / 高级模式

Advanced 是 **Technical Observability & Execution Trace Inspector**，面向售前、解决方案工程师、技术负责人、客户 IT 与面试官，回答本次事件的模型、工具、空间、调度、路线、模式与失败层级；它不是客户运营页、管理员配置后台、训练平台、SLAM 编辑器或黑客终端。它只读投影真实 Runtime records，允许用户主动切换 LIVE / Stable Replay，不允许修改地图、标定、Coverage、禁行区、范围、机器人能力、Scheduler policy、阈值、Dijkstra topology、安全策略、门禁/电梯权限或 Agent 工具权限。

目标布局为左侧约 62–65% Execution Trace、右侧约 35–38% Selected Node Detail，以 **Trace → Node → Inspect** 为核心，默认不铺满 JSON。四大模块固定为：AI Recognition Trace；Spatial / Capability / Scheduling / Route Trace；Runtime / Model / Tool / Error Observability；System Reality Matrix。所有技术展示必须可回溯 backend record / response / audit / transition，不得前端伪造 trace、tool call、latency、error、source badge、model status 或真实性状态。

## 6. CURRENT IMPLEMENTATION vs LOCKED TARGET

| 范畴 | 当前实现事实 | 锁定目标 / 差距 |
|---|---|---|
| 定位 | P1-A bbox→共享四点映射，非法输入停止派单；P1-B 同一 MapCanvas 显示落点 | 不宣称真实生产 SLAM |
| 路径 | P1-A Dijkstra `plan_route()` 保存 node_path/segments；P1-B 连续插值、电梯入口停留与终态路线保留 | 不宣称 A* Runtime 或真实机器人遥测 |
| Multi-view | P1-C 已实现 Single-view → evidence gate → model auto-tool，仅在成功 fetch 后追加模型选定的合法补图 | 核心顺序已完成；P1-G 连续多次 LIVE 稳定性与完整最终验收仍待执行 |
| Demo04 | 活跃阶段 API 已删除 cloud 大件直接人工分支；确定性回归通过，最新真实 LIVE→Replay 人工闭环通过，P1-A 工程验收通过 | Cloud → Locate → Capability Engine 零候选 → `HUMAN_FALLBACK` →人工完成→验收 |
| Event Center | P1-D 紧凑 archive list、URL state、过滤/五类状态与同一 history 快照详情 | 最终跨页面/全流程回归仍属 P1-G |
| Analytics | P1-E同库历史与Runtime增量、可追溯5KPI、热图/时段/精确档案跳转、任务区间利用率 | P1-F真实Agent建议已接入；可用时长仍是PoC假设，非生产uptime |
| Optimization / Agent | P1-F真实model工具调用、代码白名单、Task/Fleet/Action Audit、共享会话与只读缓存建议 | ASR/真实设备/生产权限未配置；不声称生产自治系统 |
| Advanced | 技术状态卡片 + 当前事件 JSON 基础 shell | Read-mostly Trace Inspector：结构化 Trace / Node Detail、Reality Matrix、Runtime/Tool/Error Observability，只读真实 audit records |
| MapCanvas / Fleet | P1-A SQLite Fleet 与进程重启测试；P1-B 唯一内层投影、正式资产栏、ID-only 刷新恢复 | 本地视觉映射是示意投影，不是第二套导航算法 |
| Stable Replay | 活跃阶段 API 已接入版本化、证据/模型/Prompt 匹配的 LIVE records；Demo01 真实回放通过，P1-A 工程验收通过 | 不允许旧合成 replay 代替真实 records；其它 Runtime 重跑，无 silent fallback |

## 7. 不可违反边界

- Robot-first + Human Fallback；人工不是 Scheduler 候选。LLM 只理解事件/能力建议/验收，不能选 `robot-a` / `robot-b` / `robot-c` 或控制路线。
- LIVE 失败必须 `HUMAN_REVIEW`，绝不 silent fallback；Stable Replay 只能由用户在现有 Advanced shell 的最小 AI Runtime 控制区主动选择且透明标识。该控制区仅包含 LIVE / Stable Replay 主动选择、云端模型可用状态、最近请求状态和最近 latency；Advanced 完整产品化仍属于后续 Batch。
- Event Center、Analytics、Workbench 必须使用同一 CleaningEvent / SQLite；历史详情必须读取历史 snapshot，不能被当前 Fleet 覆盖。
- Advanced 不是独立 Runtime，不能重跑模型、Scheduler 或 Route Planner；只能投影现有事件、Agent、空间、调度、验证、provider 与真实性元数据记录，不得展示 Chain-of-Thought、API Key、Secret、Access Token、Authorization Header 或环境变量值。
- 不引入第二 UI System、Three.js、ROS/RMF runtime、Docker/K8s、大型本地模型。不得修改 `robot-a` / `robot-b` / `robot-c` 的内部 ID、Phase 2 空间基础、Phase 3 调度规则。
