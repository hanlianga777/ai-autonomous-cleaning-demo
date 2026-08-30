# AI 自主清洁 Demo｜锁定决策

> **状态：LOCKED · 2026-08-30**
> 本文件只记录当前有效决策及明确替代关系。除标明 IMPLEMENTED 的事实外，其余产品/技术方案均为 LOCKED TARGET，不得被写成已实现。

## P1-D 档案实现边界（IMPLEMENTED · A/E PASS · 2026-08-30）

`GET /api/event-archive` 是 CleaningEvent + transition 的只读投影，不建立第二份事件数据库，也不读取当前 Fleet 覆盖历史。正常 Human Fallback 属于待人工处理；人工完成后的 CLOSED 仅在“全部”中标为人工处置后闭环，不混入“已自主闭环”或仍待人工。各分类计数先应用其它筛选，再按类别统计，不要求相加等于全部。发现时间排序不使用最后更新时间。

`/events?event=` 只恢复历史选择。非 Workbench 页面不自动推进阶段或轮询当前任务；历史页只做 GET。右侧 44% 保留 shell，内容必须与 selected event ID 相同；更换/失败时不显示另一事件快照。无时区 SQLite 时间按 UTC，操作员本地时间筛选显式转换为 UTC。新记录轮询不抢详情，不由前端补造状态。

## P1-C 工程决策补充（IMPLEMENTED · A/E PASS）

- 活跃 `cloud-review` 内先单视角，再依据 evidence sufficiency 执行可选自主补证；旧独立 `multi-view` stage 不能被调用方用来绕过单视角。
- LIVE provider 输出严格匹配 `VISUAL_JUDGMENT_SCHEMA` 全部字段，拒绝缺字段/额外字段/非布尔/非有限 confidence；`need_clean`、`decision_confidence` 仅为 Phase 3 兼容投影，与 `need_action`、`confidence` 同值。存储 provenance envelope 仅由显式 projection validation 读取，不放宽 provider 合约。
- 单视角/二审保持现有型号；真实图像 + function calling 使用可配置 `DASHSCOPE_AGENT_MODEL=qwen3-vl-plus`，经同一个 DashScope transport，始终 `tool_choice=auto`。最多 2 台额外 camera、2 个实际 fetch acquisition rounds；额外硬限 6 次 model turns、每 turn 最多 2 个 tool calls，**不表示允许 6 轮取证**。
- 保持 Fusion 权重与门槛。主图 + 1 台合法且成功 fetch 的补图已属于多视角：只有成功 fetch audit 与 evidence asset 的 camera 交集非空，final evidence_sufficient=true 且实际 image_count>=2，才计 multiview consistency；候选/metadata/失败 fetch 不计。
- semantic Replay 升级为 `p1c.visual-pipeline.v1`，保存 first/final/independent second 与安全 model tool turns；旧 P1-A semantic record 不自动兼容。verification 仍用既有 `p1a.ai-response.v1`。Replay 只替换模型返回，Coverage/Fetch/policy/Fusion/后续阶段现场执行，来源与历史 latency 明示。
- Demo02 新主图为受控 optical-ambiguity variant，原图保留、补图不变；它是测试输入，不是伪造识别输出，不代表真实相机同步。它不能写入固定 confidence 或强制补证结论。

## D01｜产品边界与技术底座

**P1-A Closure 工作树决策（2026-08-30，IMPLEMENTED · Reviewer A/E PASS）**：P1-A 时 Stable Replay 的 SQLite response bundle 使用 `p1a.ai-response.v1`（当前 semantic 已由上方 P1-C 合约替代，verification 保留），匹配图像字节、模型、Prompt 合约和事实 context，且关联存在的 LIVE event。旧未版本化/畸形/不匹配记录不可用；缺记录安全转 HUMAN_REVIEW。Replay 标注 source=REPLAY、保留历史耗时但本次 model elapsed_ms=null；不保存或直接播放预计算 workflow。机器人与人工完成共用 after-evidence verification workflow。Camera→SLAM 非法输入/输出持久化 structured SPATIAL_ERROR，不派单、不生成路线。Fleet 初始化 INSERT OR IGNORE，显式 Reset 才重置；新事件本身不隐式清除其它任务终点。

`need_clean` 表示包括人工清运在内的环境处置需求，不代表机器人可处理；模型仍可对合法暂存/无需清理给出 false，不能因为要展示 Demo04 而绕过 veto。用户已正式确认 Demo04 的两纸箱为废弃、待清运大件物品，不是合法暂存、补货或待使用物资。该事实只作为有来源、相机/事件范围的 `zone_type=egress_or_public_corridor`、`storage_policy=objects_not_allowed_to_remain`、`object_context=confirmed_discarded_items_awaiting_removal` 进入模型上下文；Cloud 判语义，不判谁处置。只有 Capability zero candidate 可产生 HUMAN_FALLBACK。上下文变化使旧 Replay key 失效，模型 false/ignore 仍然 veto。

**LOCKED**：这是可解释、可演示的园区自主清洁 PoC，不宣称真实生产机器人、电梯、时间同步、动态避障或生产阈值已部署。React + TypeScript + Vite + Tailwind + shadcn/ui 是唯一 UI 底座；ECharts 用于数据可视化，React Flow 仅用于确有必要的关系/流程。后端维持 FastAPI 模块化单体 + SQLite；禁止第二 UI System、Three.js、ROS/RMF runtime、Docker/K8s、大型本地模型。

## D02｜产品页面与数据统一

**LOCKED**：Workbench 回答“现在正在发生什么”；Event Center 回答“一个 AI 事件发生了什么、系统为何这样处理、如何闭环”；Analytics 回答“历史事件整体说明什么、下一步如何优化”。三者必须使用同一套 `CleaningEvent` / SQLite / history snapshot，不能分别维护 Mock 数据。

**LOCKED**：客户层使用业务中文；技术术语仅 Advanced/技术详情按需显示。一级导航保留“自主清洁工作台、事件中心、运营分析、高级模式”。Event Center 已按 P1-D 实现；Analytics、Robot Operations Agent 和 Advanced 完整产品化分别属于 P1-E/F/H。本批只允许在现有 Advanced shell 增加最小 AI Runtime 控制区：LIVE / Stable Replay 主动选择、云端模型可用状态、最近请求状态、最近 latency；不得借此重做完整 Advanced 页面。

## D03｜机器人正式命名与能力边界

**LOCKED**：内部 ID 保持 `robot-a` / `robot-b` / `robot-c` / `robot-d`；客户名称固定为赛特净界 S5、高仙 Omnie、蜗小白 SC50、普渡 FlashBot Max（可辅助标注“闪电匣 · 楼宇配送机器人”）。

**LOCKED**：Product Capability 与 Deployment Policy / Demo Configuration Capability 必须分开。公开产品定位不等于本 PoC 的服务区域、任务角色或限制；不得把 Demo 的地毯轻量垃圾配置伪造成厂商公开原生承诺。

**LOCKED**：赛特净界 S5 在 Demo 中只承担室外道路/广场/其他小型干垃圾/树叶；高仙 Omnie 优先承担液体污渍和较重室内清洁；蜗小白 SC50 是楼栋室内轻量清洁配置，支持瓷砖，Demo 配置支持地毯区域轻量垃圾，处理纸屑、杯子、易拉罐、小瓶等，弱化重液体，并允许 B1F→电梯→B2F→Skybridge→A2F；普渡 FlashBot Max 仅未来配送，`cleaning capability = none`，不进 Cleaning Scheduler。

**LOCKED**：保持 Robot-first + Human Fallback，人工不是候选。Capability Engine + Scheduler 是 `robot-a` / `robot-b` / `robot-c` 的唯一选择器；LLM、Multi-view Agent、Robot Operations Agent 都不能选清洁机器人或控制路线。

## D04｜Cloud VLM、门控与 Stable Replay

**LOCKED**：LIVE 必须调用真实 Qwen-VL/DashScope，禁止写死结果、特判成功、人工加置信度或 silent fallback。Prompt 可提供 camera/location/surface、YOLO 类别/置信度/ROI、限定 ontology；Qwen 不选机器人。

**LOCKED**：第一次真实 Cloud VLM 的 confidence disposition 只在最终充分证据产生后执行，Evidence Sufficiency Gate 优先。最终 `confidence >= 0.85` 不触发独立 second review，进入系统 Fusion / 业务判断；`0.50 <= confidence < 0.85` 进入独立 targeted second review；`confidence < 0.50` 进入 `HUMAN_REVIEW`，禁止自动执行。二审不得读取上一轮模型答案或 reasoning；若该最终结论来自合法 Multi-view evidence set，二审可读取该 evidence set。`need_clean=false`（语义确为无需处置）、unknown、ignore 是 veto；通用 raw `next_action=human_review` 不能覆盖满足 Fusion 的系统决策，raw action 只在 Advanced。

**LOCKED**：Fusion 仅为 `0.60 raw cloud + 0.20 YOLO 类别一致性 + 0.12 camera/location/time 一致性 + 0.08 multiview 一致性`。客户展示 raw 模型百分比和“综合处置评分：N分”，不把 Fusion 写成百分比。

**LOCKED**：Stable Replay 仅回放此前真实成功调用的结构化 AI 证据；Camera→SLAM、Capability、Scheduler、Dijkstra global topology planner / `plan_route()`、机器人状态、SQLite transitions、Verification 必须仍现场执行。默认 LIVE；仅现有 Advanced shell 的最小 AI Runtime 控制区可主动选 Replay，并在主工作台轻量透明标识。LIVE 失败一律 `HUMAN_REVIEW`。

## D05｜MapCanvas、路线、Fleet 与时间

**IMPLEMENTED / LOCKED（P1-B）**：白模、anchor、机器人、路线、marker 使用唯一 MapCanvas 坐标系，基于 `object-contain` 内层真实画布，不得依据外层 div 百分比。地图基础文字只保留 A栋、B栋、1F、2F；机器人持续插值，电梯入口暂停约 1 秒并显示“乘梯中”，不做 3D。该插值明确为 PoC 视觉节奏，完成后才提交真实 complete-navigation 阶段；无合法 node_path 不画路线。

**IMPLEMENTED / LOCKED（P1-A/B）**：`locate` 以 bbox 底边中心（液体用合理区域代表点）调用 `map_pixel_to_slam(camera_id,u,v)`，持久化 building/floor/zone/map/x/y，之后才显示 marker。Scheduler 当前 map 与 target map 调 Dijkstra global topology planner / `plan_route()`；不是 Demo ID 固定路线。Demo03 基线故事为 B1F → 电梯 → B2F → Skybridge → A2F 地毯易拉罐；连续运行仍遵守当前 Fleet，不能偷偷重置位置以强制重复基线路线。

**IMPLEMENTED / LOCKED（P1-B）**：任务后机器人保留终点与低透明路线；Demo03 验收失败 `HUMAN_REVIEW` 仍在 A2F，Demo04 人工路径无人移动。复位仍遵守 P1-A 显式 baseline/reset 边界，不因普通新事件或刷新自动复位。客户时间轴只读 SQLite transition timestamp；处理中显示真实持续时间，模型可显示真实 latency。路线起点取 ASSIGNED 快照，不用终态 Fleet 倒推。

**P1-B 刷新/失败边界**：localStorage 仅保存当前 event ID；GET SQLite 重建，不保存第二份事件/Fleet/route。sessionStorage request keys 防止同一会话刷新重发；异步快照不得覆盖不同 event 或倒退 transition。网络结果不确定时保留记录、只读同步，不自动重试模型或 Replay。该机制不等于跨标签页/服务器端全局幂等，后者仍待 P1-H。创建失败只显示本地连接提示，不捏造已保存 HUMAN_REVIEW。

## D06｜Event Center

**LOCKED**：Event Center 正式名为 **AI Event Handling Archive Center / AI 事件处置档案中心**，是 read-only trace，不是普通告警列表。实时创建的 `CleaningEvent` 应立即出现在列表；默认发现时间倒序，新增事件不能抢走用户当前查看的历史详情，只提示“有 N 条新事件”。

**LOCKED**：主筛选固定为全部、处理中、已自主闭环、待人工处理、异常。处理中为已进入处置但未 terminal；已自主闭环为“无人介入 + 机器人执行 + fixed-camera verification PASS + CLOSED”；待人工处理包含 `HUMAN_FALLBACK` / `HUMAN_REVIEW` 并在 Item 内细分搬运/复核；异常只表示 Cloud、定位、规划、调度、验证等系统或流程失败。正常 Human Fallback 绝不标为异常。

**LOCKED**：支持按 Event Type、Camera ID、Building/Floor、Robot Name、Event ID 搜索；轻量筛选为时间范围、事件类型、处置方式（机器人自主处置 / 人工兜底 / 人工复核 / 系统异常）。列表采用两级紧凑信息，不在主列表展示 YOLO/Qwen/Fusion、SLAM x/y、bbox、Dijkstra route、latency 或 `required_capabilities`。

**LOCKED**：Workbench 的 `EventDetailPanel` 是唯一详情标准。Event Center 必须使用 `EventDetailPanel(mode="history")`：只读、不重跑模型/调度/机器人、不自动滚动，展示事件发生时 Fleet、robot、route、AI、verification snapshot。左侧紧凑 Event List，右侧约 42–46% 宽 Drawer；`/events?event=EVT-xxxx` 保存选择，首次进入不自动打开第一条，切换事件不得 close/open 闪烁。

## D07｜Analytics

**LOCKED**：Analytics 正式名为 **AI Autonomous Cleaning Operations Analysis Center / AI 自主清洁运营分析中心**，不是物业驾驶舱。三层为 Autonomy Outcome、Operational Efficiency、Optimization Advice；所有 KPI 由后端 CleaningEvent / Transition 计算，前端不得 hardcode，只有真实计算才显示 period-over-period trend。

**LOCKED**：顶部 5 KPI 固定为自主闭环率、人工介入率、首次处置成功率、平均响应时间、平均闭环时间。自主闭环率是有效事件中“无人介入 + Robot 完成 + verification PASS + CLOSED”；人工介入率是发生 `HUMAN_REVIEW` 或 `HUMAN_FALLBACK` 的有效事件比例；首次处置成功率为第一次清洁后第一次 verification PASS；平均响应从确认/可处置到机器人或人工实际开始；平均闭环从发现到 `CLOSED`。处理中和系统异常须有明确 denominator 规则，不能为了加总好看强行凑 100%。

**LOCKED**：主视觉为 **Campus Spatial Event Heatmap / 园区历史事件空间热力图**，复用 Campus / SLAM white model，以 map_id/x/y/event_type/timestamp 聚合。低频浅蓝灰、中频低饱和蓝、高频 amber/orange；不使用红黄绿气象图，实时路线不是主角。数据源为明确标识的“近30天 · 演示历史数据”结构化 Seed History + 当前 Runtime CleaningEvent Increment，绝不冒充真实客户历史。

**LOCKED**：过滤为事件类型（全部、其他小型垃圾、液体污渍、易拉罐、大件物品）和时段（全天、06–10、10–14、14–18、18–22）。热点 drill-down 展示区域、总数、类型、时段、平均闭环，并可跳 Event Center 携带 location/type/time 筛选。辅助模块仅保留事件结构分析、高发区域与时段规律、清洁机器人运营效率；FlashBot Max 不参与清洁利用率排名。

## D08｜Robot Operations Agent 与 Policy Guard

**LOCKED / TODO**：系统只保留两个必要 Agent：Multi-view Perception Agent（主动视觉取证）与 Robot Operations Agent（自然语言理解、运营分析、白名单工具选择、低风险任务执行、Observe/Replan/Close）。不得新增 Heatmap / Scheduler / Dijkstra / Camera-to-SLAM / RAG Agent；RAG 仅可作为 Robot Operations Agent 的 Knowledge Tool。

**LOCKED / TODO**：Robot Operations Agent 有 Read Tools（事件、详情、KPI、热点、利用率、robot/fleet/capability/POI/location/task/camera evidence 等）及低风险 Action Tools（创建清洁/配送/待命任务、dispatch/pause/resume/cancel、请求证据、状态更新）。任务可直接执行但必须经 Policy Guard；Relocation 目标只可来自合法 POI / approved location，Agent 不得直接控制底盘坐标。

**LOCKED / TODO**：Agent 永远没有 `update_slam_map`、禁行区/范围/能力/标定/Coverage/Scheduler policy/自动处置阈值/速度/门禁/电梯权限等 Write Tools。安全边界必须由代码级工具白名单实现，不是 Prompt 自律。物理动作需写 Action Audit：用户原话/ASR、intent、tool/args、Policy Guard、Task ID、机器人、结果、异常、replan、最终状态。

## D09｜Agent 页面形态、Analytics Advice 与语音

**LOCKED / TODO**：只有一个共享 Robot Operations Agent。Workbench 与 Event Center 是可拖动 Floating Window：没有已保存 UI position 时默认左下角，已保存的 localStorage position 优先；仅 Header/Drag Handle 可拖、不能出 viewport、展开/收起保持位置、跨 Workbench/Event Center 与刷新保持。Analytics 不显示 Floating Agent，改为右侧固定 Panel：上半 AI 运营优化建议，下半同一 Agent 对话。切页不丢 `AgentSession`、`AgentMessage`、`AgentActionAudit`、Task context。

**LOCKED / TODO**：Page Context 自动注入：Workbench 当前 event/fleet/map/robot/camera/stage；Event Center 为 selected event snapshot/filters；Analytics 为 time window/type/hotspot/robot/KPI/chart context。真实机器人动作必须返回读取后端真实 Task 的 Action Card（Task ID、机器人、取件/目标、状态），不能只说“已安排”。语音只是同一 Agent 输入：Microphone → real ASR → transcript → Agent，不是当前清洁 Demo 的主要演示路径；禁止 fake voice interaction。若麦克风显示为可用，必须真实调用已配置的 ASR provider；未配置时必须 disabled 或明确显示“语音服务未配置”，禁止预设文本、前端 timer 或 mock transcript 冒充识别成功。

**LOCKED / TODO**：Analytics Advice 不是第三个 Optimization Agent。确定性 Analytics Engine 负责 KPI/Heatmap/Time/Utilization；Robot Operations Agent 最多 3–4 次 Read Tool 后给 3–4 条含发现、数据依据、建议、相关事件的只读建议。默认显示最近 snapshot（Data Window / Generated At），仅用户点击才重新生成；不得自动改 Scheduler、阈值、范围、能力或地图。

## D10｜Multi-view Perception Agent

**IMPLEMENTED / LOCKED（P1-C）**：新链路固定为：Fixed Camera → Edge YOLO / controlled edge evidence → **Single-view Cloud VLM** → Evidence Sufficiency Judgment → conditional Multi-view Perception Agent → Multi-view Cloud VLM → Business Decision → Camera→SLAM → Capability → Scheduler → Robot → Verification。`confidence` 与 `evidence_sufficient` 是不同字段；Single-view VLM 应输出 event type、need action、confidence、evidence sufficient、ambiguity type（reflection / occlusion / perspective / lens contamination / insufficient view / small object / semantic uncertainty / other）。

**IMPLEMENTED / LOCKED（P1-C）**：Evidence Sufficiency Gate 的优先级高于最终 confidence disposition。Single-view VLM 同时返回 `confidence`、`evidence_sufficient`、`ambiguity_type`；当 `evidence_sufficient=false`，且 ambiguity 为 reflection / occlusion / perspective / lens_contamination / insufficient_view 等可由额外视角缓解的问题，并存在合法 supporting cameras 时，Multi-view Agent 可通过真实 model tool calling 先主动补证。此时不得仅因 Single-view `confidence < 0.50` 提前终止为 `HUMAN_REVIEW`。正确顺序为 Single-view evidence → evidence sufficiency → 可恢复时自主 Multi-view evidence acquisition → final semantic judgment → confidence gate。

**IMPLEMENTED / LOCKED（P1-C）**：Multi-view 是 Active Visual Evidence Acquisition，不是 “if confidence < threshold” Workflow。模型先只看 Main Camera Image、YOLO bbox/detection、必要 Camera Context；以 `tool_choice=auto` 自主决定是否补证、选哪 1–2 路、是否继续、何时停止。没有合法 supporting camera、Evidence Fetch 失败，或最多 2 rounds 后仍 `evidence_sufficient=false` 时，必须 `HUMAN_REVIEW`；即使 raw confidence 较高，最终 `evidence_sufficient=false` 也不得自动机器人处置。不得按 `demo_id` 强制、不得初轮塞三图、不得 `tool_choice=required`、不得前端 `setTimeout` 假装 Agent。

**IMPLEMENTED / LOCKED（P1-C）**：Agent 只有 `find_supporting_cameras()`、`fetch_camera_evidence()`、`finish_visual_judgment()` 这类等价工具；最多 2 路额外摄像头、最多 2 个 evidence acquisition rounds。PoC Evidence Adapter 可返回 controlled evidence assets，必须如实说明，不得假装 RTSP 同步；未来可替换 RTSP/VMS/NVR/Camera Platform。Agent 不得改 Coverage、邻接、calibration、SLAM、地图、机器人、confidence 或自动处置阈值。

**IMPLEMENTED / LOCKED（P1-C）**：Demo02 必须由真实模型自主发起 Tool Call：CAM-A1-01 单视角看到液体/反光歧义 → Coverage candidate search → 选择 1–2 路（受控证据可为 A1-02/A1-04）→ evidence fetch → multi-view Cloud → final semantic judgment → confidence gate → 高仙 Omnie → verification → CLOSED。最终 `0.50 <= confidence < 0.85` 的 independent targeted second review 可读取本次合法取得的完整 evidence set，但不得读取上一轮模型答案或 reasoning。客户 UI 只展示来自 Agent Trace / Tool Audit / Cloud Response / Transition 的精简中文步骤，不展示 Chain-of-Thought；Advanced 才看技术 trace。

## D11｜External Delivery Platform Integration

**LOCKED / TODO**：清洁仍是主业务；配送用于证明 Robot Operations Agent 可跨业务扩展。对外只表述“在获得相应平台授权、开发者资质及 API 权限后，可接收园区相关配送订单/状态并与楼宇配送机器人任务双向同步”。未授权时只能显示 `ADAPTER READY` / `AUTH REQUIRED`，绝不显示 `CONNECTED` 或伪造平台 callback。

**LOCKED / TODO**：真实 Platform Webhook 后走确定性 Delivery Adapter → Address / POI Normalization → Policy → Delivery Workflow → FlashBot Max → Status Callback；地址模糊、自然语言变更、机器人/电梯异常、目标冲突等不确定情况才由 Robot Operations Agent 介入。

## D12｜阶段 Runtime（已实现，继续锁定）

**IMPLEMENTED / LOCKED**：阶段 API 与 SQLite 审计已拆分；Cloud 仅在 cloud-review，Scheduler 仅在 assign，Verification 仅在 verify 或 Demo04 人工完成后。`assignment_decision` 是当前行动机器人的唯一事实源；旧 `/runs/*` 已 410。后续实现必须保留该边界，不能回到“先算完整结果再播放”。

## D13｜Advanced Technical Observability / 高级模式

**LOCKED / TODO**：Advanced 正式定位为 **Technical Observability & Execution Trace Inspector**，是 read-mostly 技术透明、运行审计与执行链路查看页面；它不是普通客户运营页、管理员配置后台、模型训练平台、SLAM 编辑器、Scheduler 配置台、参数调试后台或黑客终端。沿用 React + TypeScript + Vite + Tailwind + shadcn/ui，浅色、克制、企业 SaaS；禁止黑客终端、霓虹、赛博朋克、Glassmorphism、复杂 3D 或第二 UI System。

**LOCKED / TODO**：只允许查看、审计、追溯、展开技术详情与用户主动切换 LIVE / Stable Replay。绝不允许编辑 SLAM、Camera Calibration、Camera Coverage、禁行区、清洁/巡检范围、机器人 Capability、Scheduler Policy、自动处置 Threshold、Dijkstra topology、门禁/电梯权限、安全速度或 Agent 工具权限；未来 Admin / Configuration 是独立产品能力。

**LOCKED / TODO**：顶部为轻量 Runtime Strip：LIVE / Stable Replay、Cloud Model Available / Unavailable、Last Request Success / Failed / Idle、真实最近 latency；可补 Provider、Model、Request Time，不堆系统指标、不展示 API Key / Secret / Access Token / Authorization Header / 环境变量值。主体为左 62–65% Execution Trace、右 35–38% Selected Node Detail，交互固定为 Trace → Node → Inspect，不默认铺完整 JSON。

**LOCKED / TODO**：四个核心模块固定为：(1) AI Recognition Trace；(2) Spatial / Capability / Scheduling / Route Trace；(3) Runtime / Model / Tool / Error Observability；(4) System Reality Matrix。不得重复放普通 Event List、Analytics KPI / 热力图、业务大屏或普通 Fleet Dashboard。

**LOCKED / TODO**：AI Recognition Trace 固定六段：Edge Detection、Single-view Cloud VLM、Conditional Multi-view Perception Agent、Multi-view Cloud Judgment、Business Decision / Fusion、Verification。未触发 Multi-view 时第 3/4 段如实显示 `NOT_TRIGGERED / EVIDENCE_ALREADY_SUFFICIENT`，不得假装调用。Node 展示结构化输入/输出摘要、camera、bbox/ROI、confidence、evidence sufficiency、ambiguity、latency、second-review status、verification ROI/verdict；禁止 Chain-of-Thought、scratchpad 或 reasoning tokens。Edge 仍为受控 bbox 时必须显示 `CONTROLLED EDGE DEMO`，不得声称 REAL YOLO。

**LOCKED / TODO**：Spatial / Capability / Scheduling / Route Trace 固定四段：Camera→SLAM、Capability Engine、Scheduler、Dijkstra Route。Camera→SLAM 展示 camera、bbox ground point、u/v、4-point homography、calibration status、building/floor/zone/map/x/y；Capability 展示 TaskProfile、硬约束、候选与 Demo Configuration 边界；Scheduler 展示 current state/map/battery/task/route cost/capability fit/priority 与 `AssignmentDecision`；Dijkstra 展示 start/target map、node/segment path、cost、数量与小 topology preview。清洁机器人选择永远来自 Capability Engine + Scheduler，不得标为 LLM / Agent selected robot；Dijkstra 只代表园区级全局 topology planning，不等于 Nav2 或局部动态避障。

**LOCKED / TODO**：Runtime Observability 包含 Runtime Mode、Model Runtime、Agent Tool Trace、Error & Recovery。统一 Tool Trace component 显示 tool、trigger source、start time、duration、status、input/result summary；trigger source 仅为 `MODEL_TOOL_CALL`、`SYSTEM_WORKFLOW`、`USER_ACTION`。错误层级固定为 `MODEL_ERROR`、`TOOL_ERROR`、`POLICY_REJECTED`、`SPATIAL_ERROR`、`SCHEDULER_ERROR`、`ROUTE_ERROR`、`VERIFICATION_ERROR`、`EXTERNAL_ADAPTER_ERROR`；LIVE failure 禁止 silent Replay。Recovery 只可展示 Policy Guard 白名单内 retry/wait/re-query/allowed alternative/notify，不能借 Recovery 改基础设施配置。

**LOCKED / TODO**：关键 Node / Evidence 使用统一 Source Badge：`LIVE MODEL`、`DETERMINISTIC RUNTIME`、`CONTROLLED EVIDENCE`、`POC SIMULATION`、`REPLAY`、`AUTH REQUIRED / NOT CONNECTED`。Reality Status 未来由 Runtime fact、configuration、provider status、evidence source、authorization status 自动决定，前端用户不得手改。System Reality Matrix 至少覆盖 Cloud Qwen、Multi-view Tool Calling、supplemental evidence、YOLO/edge evidence、Camera→SLAM、Capability、Scheduler、Dijkstra、robot movement、elevator/Skybridge、verification、Replay、delivery adapter、FlashBot Max delivery runtime、ASR，并展示 Capability / Current Reality Status / Short Explanation、PoC boundary 与 future adapter replacement point。

**LOCKED / TODO**：Advanced 不是新 Runtime。它只读投影 CleaningEvent transitions、Cloud request records、Agent Action/Tool Audit、spatial mapping、capability evaluation、AssignmentDecision、route、verification、provider status 与 reality source metadata；不得独立重跑模型、Scheduler 或 Route Planner，不得前端伪造 trace、tool call、latency、error、source badge、model status 或 reality status。未来 CleaningEvent / AgentTask 应有独立 Trace ID（不等于 Event ID）串联 Workbench、Event Center、Advanced、Action Card、Tool Trace、Model Request 与 Task Runtime。

## SUPERSEDED 决策索引

| 旧方案 | 新决策 |
|---|---|
| YOLO low confidence → 立即 Multi-view → Cloud | Edge YOLO → Single-view Cloud VLM → Evidence Sufficiency → conditional Multi-view Agent → Multi-view Cloud |
| 按 `demo_id == demo02` 或固定阈值进入 Multi-view | 真实模型以 `tool_choice=auto` 自主工具调用；不得泄漏测试答案 |
| 初轮三张图同时给 Cloud 后假装主动取证 | 初轮只给主视角；补充图只能来自真实 tool call |
| Command Bar + 独立语音入口 + Floating Assistant 三入口 | 一个 Robot Operations Agent；Workbench/Event Center 浮窗，Analytics 固定 Panel；语音只是输入模态 |
| 独立 Analytics Optimization Agent | Robot Operations Agent 的运营分析能力；Analytics Engine 仍确定性 |
| demo_id 直接给固定 location | Camera→SLAM 真实运行时定位（P1-A 代码与测试通过） |
| demo_id 固定 navigation anchors | Scheduler current map + target map → Dijkstra global topology planner / `plan_route()`（P1-A 代码与测试通过） |
| Demo04 cloud 阶段直接 Human Fallback | Cloud → Locate → Capability 零候选 → Human Fallback（P1-A 代码与测试通过） |
| HUMAN_REVIEW 截断/重建时间轴 | 完整历史保留（P1-B 代码、测试与浏览器通过） |
| CLOSED 自动复位机器人 | 终点保留，仅显式 baseline/reset 才复位（P1-A/B 代码、测试与浏览器通过） |
| raw Qwen next_action 当客户系统建议 | 模型判断与系统业务决策分离 |
| “地面纸巾”“大型纸箱”面客类目 | 其他小型垃圾 / 大件物品 |
| 前端 startedAt + 固定 offset 假时间 | SQLite transition timestamp（P1-A 代码与测试通过） |
| LIVE 失败偷偷成功回放 | NO SILENT FALLBACK |
