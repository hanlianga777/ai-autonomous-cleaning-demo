# AI 自主清洁 Demo｜锁定决策

> **状态：LOCKED · Post-merge Interview Freeze · 2026-08-30**
> Unified Implementation merge baseline: `8341eb079fe5a700b4931e0112fdbe5552297785`
> Current main HEAD: 以 GitHub main / `git rev-parse HEAD` 为准
> 历史实施分支 `codex/unified-implementation` / `bdd08e02e0e4fc96d9ad6229949f2c8bf3812136` 仅作历史记录。
> 本文件只记录当前有效决策及明确替代关系。除标明 IMPLEMENTED 的事实外，其余产品/技术方案均为 LOCKED TARGET，不得被写成已实现。

## AI-UI-01｜Robot Operations Agent UI Shell（LOCKED TARGET · 2026-08-30）

- 最新用户确认的 AI-UI-01 优先于旧 P1-F UI Shell 表述。旧“Workbench / Event Center 共享横向长条 Floating Window、仅 Header / Drag Handle 拖动、现有展开式 Tool/Task Panel”是历史实现描述，**SUPERSEDED BY AI-UI-01**，且当前代码仍属 `IMPLEMENTATION_DIVERGENCE`；不得作为当前 LOCKED TARGET 或写成 AI-UI-01 已实现。
- Workbench / Event Center 继续使用同一个 Robot Operations Agent，但默认入口必须是左下小型圆形/球形、可在整个浏览器可视区域合法范围内拖动并持久化的 AI 悬浮球；默认不遮挡核心内容，收起时只保留该圆球。
- 点击圆球必须弹出完整 AI Assistant Chat Window，包含 Assistant 欢迎/身份、历史消息、用户消息、AI 回复、明显输入区、发送入口、必要状态和关闭/收起回圆球；不得把原横条 Tool/Task Panel 原地展开当作满足。
- Analytics 不显示浮动球。旧“右侧上半 AI运营建议、下半完整 Chat”的方案已被 **ANALYTICS-DELTA-01 SUPERSEDED**：AI运营建议在左侧 KPI 后以最多三列横向卡呈现，右侧固定 AI Area 只保留完整 Robot Operations Agent Chat。该右侧区域应独立布局/滚动；左侧长 Analytics 内容不得把 Chat 输入入口推到整页底部，进入页面的当前可视高度内必须能找到聊天入口。
- 三页仍共享同一个 Agent、Agent Session、Task / Audit / Backend State，即“一个 Agent，两种 UI 投影”；禁止新增 Analytics Agent、Optimization Agent 或第二 Conversation Agent。完整的逐项目标、当前偏差和验收标准见 `INTERVIEW_DEMO_RECONCILIATION.md#ai-ui-01ai-运营入口与聊天交互`。

## WB-DETAIL-01｜面客事件处置详情与实时业务进度（LOCKED TARGET · 2026-08-30）

- Workbench 右侧“最近事件处置详情”是客户/面试官实时业务展示，不是工程日志、Debug/免责/数据库 Trace/算法参数面板；首屏只回答事件、AI 结论、系统下一步、机器人执行位置和 AI 验收闭环。技术事实、raw evidence、latency、错误、schema、算法/PoC 边界统一由 Advanced / Technical Detail 投影，Workbench 只保留低干扰全局 `POC / DEMO` 身份提示。
- 旧客户层显示“完整处置过程/真实阶段记录/事件已持久化/受控边缘检测/非本地 YOLO/历史 schema/PoC 插值非遥测/API latency/内部 error、schema、evidence、technical reason”等表述，及 P1-C 对客户展示 Tool Trace/Evidence 明细、D05 对客户显示模型 latency 的旧 UI 表述，**SUPERSEDED BY WB-DETAIL-01**。这些底层事实仍保留且在 Advanced 可审计；当前 Workbench 仍显示它们属于 `IMPLEMENTATION_DIVERGENCE`。
- Workbench 必须以真实 Runtime 渐进展示事件：确定性业务阶段约 1.5–3 秒可感知，真实 Cloud/Multi-view/Verification 仅按真实调用/响应推进，Dijkstra route 的 PoC playback 连续移动，Cleaning 不可瞬跳 Verify。不得伪造 Cloud latency、路径、ETA、设施、状态或验收结论。
- Cloud 仅显示最终有效 AI研判置信度和清晰字段行；Fusion 显示“系统处置评分 N分”，不显示为百分比。真实 spatial 必须显示客户地图名、Building/Floor/Zone 与 SLAM X/Y；Capability/Assignment 只用正式机器人名，真实 hard filter→eligible→score→assignment，FlashBot Max 不进清洁候选；route 只显示后端真实数据，缺 distance/ETA 即为实施 Gap。
- 四个 Workbench demo 必须按其真实业务流程终态化；Workbench-origin demo 和 Agent-origin task 的 ownership 必须清楚，故障必须成为明确错误或 HUMAN_REVIEW 并释放下一次启动条件。右侧必须保留 after image → AI验收结果/置信度 → CLOSED 或真实后续处置的清晰业务闭环。完整的逐项目标、证据门槛和当前偏差见 `INTERVIEW_DEMO_RECONCILIATION.md#wb-detail-01面客事件处置详情与实时业务进度`；本条未实施，不得写为 IMPLEMENTED。

## WB-MAP-01｜机器人资产与园区空间调度地图（LOCKED TARGET · 2026-08-30）

- Workbench 中央区域是客户/面试官的“园区空间调度”总览，而不是 SLAM/Fleet/Topology/Backend 调试器。左侧四台正式命名机器人必须以统一网格卡显示名称、图片、业务状态、电量、业务位置；默认卡不显示内部 ID、map/zone、Task ID、坐标或能力列表，详细 SLAM/能力/当前任务仅在地图 marker hover 显示。被实际派发的机器人必须以克制企业 SaaS 视觉突出，禁止霓虹/赛博风。
- 旧 P1-B 白模 anchor-to-anchor 线性插值、弱路线、技术术语（`FLEET ASSETS` / Fleet / Backend Route / Topology / PoC 模拟状态）、小“事件位置”marker、地图右上重复状态卡及其作为面客空间总览的旧视觉方案，**SUPERSEDED BY WB-MAP-01**。Dijkstra 顺序、MapCanvas 内层坐标、Fleet position、电梯/连廊事实与 P1-B playback runtime 仍保留；当前面客地图仍是 `IMPLEMENTATION_DIVERGENCE`。
- 所有客户路线/事件/设施/位置只来自 backend deterministic spatial/runtime facts。六张 2D SLAM map、Camera→SLAM、connector graph、Dijkstra、Fleet position、电梯/连廊与 Capability policy 是既有事实：S5 仅室外，Omnie 仅 A栋室内且不跨连廊，SC50 可经电梯/连廊。不得以视觉效果突破这些边界。
- 当前 anchor projection 只证明 route 的跨楼/电梯/连廊拓扑顺序，不能证明沿道路/走廊/连廊中心线可行走，属 `IMPLEMENTATION_GAP`。未来须将 backend business route 投影为统一维护的 Demo Navigation Waypoint Geometry；不要求 Nav2/动态避障/production costmap，但禁止穿墙、穿楼、道路外漂移、室内上马路或跨楼直线。
- 地图必须在真实 demo stage 中演进：空闲无路线、发现事件点、派单路线/选中高亮、导航沿合法 waypoints、真实电梯停留、连廊移动、到达/清洁/验收、CLOSED 绿色完成和路线弱化。路线必须明显且层级为事件点 > 当前机器人 > 已走 > 待走；Demo01 S5 室外道路、Demo02 Omnie A栋、Demo03 SC50 B1F→电梯→B2F→连廊→A2F 都必须由用户可见验证。完整的 15 项目标和证据门槛见 `INTERVIEW_DEMO_RECONCILIATION.md#wb-map-01机器人资产与园区空间调度地图`；本条未实施，不得标记 IMPLEMENTED/USER_ACCEPTED。

## WB-CAMERA-01｜固定摄像头监控墙与“AI机器人调度大脑”（LOCKED TARGET · 2026-08-30）

- Workbench 顶部是客户实时监控墙，不是 CV/YOLO/Evidence Debug 或 Camera 配置页。默认三路等宽同行监控，无 event 时全为清洁后的正常图；event 时真实主 camera 必在第一槽显示清洁前原图，另两路正常。顶部墙永不显示 YOLO/bbox/类别/置信度/Camera ID/Evidence 技术标签，受控检测与完整 evidence 保留给 Event Detail/Advanced。
- 旧“两路重点区域”、`grid-cols-2`、`object-contain` 黑边、Workbench bbox overlay、Camera ID/前后证据/controlled evidence badge、无播放按钮/时钟、标题解释小字、旧“自主清洁工作台”页面名、Header stage/LIVE/Stable Replay 技术状态，是历史 UI 方案，**SUPERSEDED BY WB-CAMERA-01**；当前 active implementation 属 `IMPLEMENTATION_DIVERGENCE`。内部 `PrototypeWorkbench`/route 无需为客户文案重构。
- Card 以克制业务状态显示红色事件、橙色处理中、短绿色验收通过后恢复正常；默认只显示地点、中心半透明播放视觉入口、右下每秒 `HH:mm:ss` 展示时间。面客墙允许无拉伸的 cover/crop，Evidence/Advanced 继续完整比例/bbox 对齐。Demo Operator Control 可保留在低干扰“…”二级入口。
- 所有 Camera state、before/after 切图与 AI验收结果必须从真实 Runtime/asset/verification 投影；不得伪造 RTSP、原始 camera OSD、检测或验收。Demo01–04 都必须让用户见证“正常→事件原图无框→处理中→清洁后→AI验收→正常”。完整 19 项目标和用户验收门槛见 `INTERVIEW_DEMO_RECONCILIATION.md#wb-camera-01固定摄像头监控墙与ai机器人调度大脑页面表达`；本条未实施，不得标记 IMPLEMENTED/USER_ACCEPTED。

## P1-G 验收执行边界（IMPLEMENTED；不替代用户主观展示验收）

- 通用 verification 的 target ROI 只能由主相机 controlled edge 的合法 normalized bbox union 推导；同一 normalized ROI 同时裁取 before/after，不得使用场景专用坐标、supporting-camera bbox 或猜测目标。primary verifier 必须同时获得 before/after 全图及这对 ROI；缺失、畸形、非法 bbox、非有限数值或不匹配 Replay 一律安全失败。
- primary verifier 的失败最多允许一次独立 target-ROI review；独立调用只能收到 paired ROI 和 factual context，不能收到 primary 的答案、confidence 或 reasoning。二审通过可以闭环当前事件，但不重写 primary verdict，Analytics first-pass 仍以 primary 为准。所有 verification JSON 继续严格校验 bool、枚举与有限 raw float，禁止通过 round/bool/string coercion 把失败提升为成功。
- 已保存 P1G qualifying LIVE：Demo01 5/5、Demo02 5/5、Demo03 5/5、Demo04 3/3；同 fingerprint post-review Replay 四 Demo 各3/3，Replay 无新 Cloud request。backend 164=161 PASS+3 paid opt-in skipped、frontend46/build、bash-n/diff与 A/B/C/D/E 均 PASS，故 P1-G 工程/自动化/浏览器验收为 **IMPLEMENTED**。Unified Implementation 已合并至 current main；用户主观展示验收仍独立。

## P1-H 可观测性边界（IMPLEMENTED · A/E PASS · 2026-08-30）

- Advanced GET只投影SQLite已保存事实；点击节点不调用模型、Scheduler、Dijkstra或Fleet更新。新事件独立Trace UUID，Ops每次消息独立request trace，Task明确event/origin request关联；不得按共享session把不同任务的请求混为一个事件。
- legacy未记录Trace显示LEGACY_MISSING，GET不补写；model_records新增关联列但不改变Replay payload/fingerprint。Replay只重用AI响应，工具/阶段真实重跑，其tool duration不得用历史model latency冒充。
- 错误API仅返回8类taxonomy code与安全说明；结构化字段白名单递归过滤，不返回原始Prompt、模型思维链、原话、密钥、token、base64或本地路径。模型/阶段真实start/duration仅新执行时采集；旧数据缺值不倒推。
- Reality来源使用锁定6类；未执行/未选择另设execution_status。边缘节点额外明确CONTROLLED EDGE DEMO；controlled evidence不是生产YOLO/RTSP，PoC不是设备遥测。当前Trace Inspector以集成事件为入口，不能声称已有独立原生Task Inspector。

## P1-F 执行与真实性边界（IMPLEMENTED · A/E PASS · 2026-08-30）

- Robot Operations Agent 与 Multi-view 共用现有 Qwen transport，但工具白名单不同；`tool_choice=auto`，Ops 每轮最多8工具/4写操作，建议最多4只读工具。未知工具、额外坐标参数、越界 POI/机器人范围均由代码拒绝并审计，不依赖 Prompt 自律。
- 清洁只包装现有 eligible CleaningEvent；先 create、dispatch，再由原有 workflow stage 执行。不从自然语言伪造 TaskProfile，不改变 Robot-first + Human Fallback。Task lease 同时保护 Agent 与原 Workbench stage，暂停/取消不能由另一入口绕过。
- Task/Fleet 短事务使用 SQLite BEGIN IMMEDIATE；云端调用在事务外并持有 durable task lease。清洁暂停/恢复同步 Fleet 并恢复实际原状态。终点/电量/Task 保留到重启；有活动 Operations 任务时必须先取消再 Reset Fleet。
- `X-Operations-Session` 校验 UI task action 与 task.session_id 一致；这是本地 PoC 会话边界，不是生产登录权限系统。清洁完整阶段事实仍以 CleaningEvent transitions 为准，Task 的 workflow_transitions 是只读投影，不复制第二份真相。
- 原生 DeliveryTask 绑定 robot-d，Approved POI + Dijkstra；其“仅操作员显式推进 POC SIMULATION 取件/乘梯/送达”的旧客户交互已被 **OPS-AUTO-01 SUPERSEDED**。未来由后端 Show Runtime 自动演示真实持久化状态，仍不 fake 外部 callback。robot-d 室内/电梯/连廊为明确的 PoC deployment policy；缺失/拒绝权限 fail closed。美团/饿了么/京东/淘宝闪购仅 Adapter registry + AUTH REQUIRED。
- Advice 使用同一个 Operations Agent 的只读工具能力，显式请求后缓存 3–4 条，包含实际 Data Window/Generated At/关联事件，验证引用来自所读集合；不能自动改配置。旧 `/api/optimization/recommend` 410。模型定性建议不是统计显著性证明或生产收益承诺。
- 档案列表/详情继续只读；共享 Agent 中由用户主动发起的白名单 task action 是单独审计入口，不是档案浏览自动派单。ASR 未配置时 disabled，未实现真实语音 provider。

## P1-E 指标与数据来源实现边界（IMPLEMENTED · A/E PASS · 2026-08-30）

- 演示历史与 Runtime 均在 CleaningEvent/transition SQLite；Seed 仅启动幂等插入，不在 GET 生成第二份数据，不更新 Fleet/模型记录。Archive、detail、Analytics 均标 DEMO_HISTORY，历史 seed 不能进入实际集成 Runtime。
- “有效业务处置结论”分母为非系统异常的 CLOSED/HUMAN_FALLBACK/HUMAN_REVIEW；仍自动处理中与系统异常单列排除。自主闭环同时要求 robot+verification PASS+CLOSED+无人工；人工介入统计任何 HF/HR，不人为补齐100%。
- 首次成功分母仅首次验收有明确布尔结果的事件；重试成功不能覆盖首次失败。响应样本仅 CLOUD_REVIEW→NAVIGATING 或有记录的 HUMAN_STARTED/HUMAN_WORK_STARTED；HUMAN_COMPLETED 不冒充开始。闭环时间仅 DETECTED→CLOSED；缺观察空值并公开样本数。
- 利用率 = 任务活跃区间并集 / 可用区间；当前缺真实 roster/uptime provider，明确使用 PoC 假定连续可用窗口(00–24)归一化，不称真实在线率、不修改 Fleet/Scheduler。窗口前任务仅计窗口内活跃区间；窗口内新任务与 carry-over 分开计数；FlashBot Max 排除。
- D07 时段保持全天、06–10、10–14、14–18、18–22（Asia/Shanghai，左闭右开）；旧单小时参数仅兼容 API，不替代锁定 UI。热点携带 map/x/y/type/time_slot/UTC window 至 Event Center；未经过 LOCATED 的 Runtime 模板坐标不能进入热图。

## P1-D 档案实现边界（IMPLEMENTED · A/E PASS · 2026-08-30）

`GET /api/event-archive` 是 CleaningEvent + transition 的只读投影，不建立第二份事件数据库，也不读取当前 Fleet 覆盖历史。正常 Human Fallback 属于待人工处理；人工完成后的 CLOSED 仅在“全部”中标为人工处置后闭环，不混入“已自主闭环”或仍待人工。各分类计数先应用其它筛选，再按类别统计，不要求相加等于全部。发现时间排序不使用最后更新时间。

`/events?event=` 只恢复历史选择，档案浏览本身只做 GET；P1-F共享Agent的用户显式任务操作单独鉴权审计，不由档案浏览另行触发。旧“非 Workbench 页面不自动推进阶段”的页面绑定执行语义已被 **OPS-CONTINUITY-01 SUPERSEDED**：已开始任务必须由后端 Show Runtime 继续，Event Center 只读取投影。右侧 44% 保留 shell，内容必须与 selected event ID 相同；更换/失败时不显示另一事件快照。无时区 SQLite 时间按 UTC，操作员本地时间筛选显式转换为 UTC。新记录轮询不抢详情，不由前端补造状态。

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

**LOCKED**：客户层使用业务中文；技术术语仅 Advanced/技术详情按需显示。一级导航保留“自主清洁工作台、事件中心、运营分析、高级模式”。Event Center/Analytics/Operations/Advanced分别已按P1-D/E/F/H实施。早期仅shell控制区限制已被Unified P1-H明确授权取代，但不得扩展为配置后台。

## D03｜机器人正式命名与能力边界

**LOCKED**：内部 ID 保持 `robot-a` / `robot-b` / `robot-c` / `robot-d`；客户名称固定为赛特净界 S5、高仙 Omnie、蜗小白 SC50、普渡 FlashBot Max（可辅助标注“闪电匣 · 楼宇配送机器人”）。

**LOCKED**：Product Capability 与 Deployment Policy / Demo Configuration Capability 必须分开。公开产品定位不等于本 PoC 的服务区域、任务角色或限制；不得把 Demo 的地毯轻量垃圾配置伪造成厂商公开原生承诺。

**LOCKED**：赛特净界 S5 在 Demo 中只承担室外道路/广场/其他小型干垃圾/树叶；高仙 Omnie 优先承担液体污渍和较重室内清洁；蜗小白 SC50 是楼栋室内轻量清洁配置，支持瓷砖，Demo 配置支持地毯区域轻量垃圾，处理纸屑、杯子、易拉罐、小瓶等，弱化重液体，并允许 B1F→电梯→B2F→Skybridge→A2F；普渡 FlashBot Max 仅未来配送，`cleaning capability = none`，不进 Cleaning Scheduler。

**LOCKED**：保持 Robot-first + Human Fallback，人工不是候选。Capability Engine + Scheduler 是 `robot-a` / `robot-b` / `robot-c` 的唯一选择器；LLM、Multi-view Agent、Robot Operations Agent 都不能选清洁机器人或控制路线。

## D04｜Cloud VLM、门控与 Stable Replay

**LOCKED**：LIVE 必须调用真实 Qwen-VL/DashScope，禁止写死结果、特判成功、人工加置信度或 silent fallback。Prompt 可提供 camera/location/surface、YOLO 类别/置信度/ROI、限定 ontology；Qwen 不选机器人。

**LOCKED**：第一次真实 Cloud VLM 的 confidence disposition 只在最终充分证据产生后执行，Evidence Sufficiency Gate 优先。最终 `confidence >= 0.85` 不触发独立 second review，进入系统 Fusion / 业务判断；`0.50 <= confidence < 0.85` 进入独立 targeted second review；`confidence < 0.50` 进入 `HUMAN_REVIEW`，禁止自动执行。二审不得读取上一轮模型答案或 reasoning；若该最终结论来自合法 Multi-view evidence set，二审可读取该 evidence set。`need_clean=false`（语义确为无需处置）、unknown、ignore 是 veto；通用 raw `next_action=human_review` 不能覆盖满足 Fusion 的系统决策，raw action 只在 Advanced。

**LOCKED**：Fusion 仅为 `0.60 raw cloud + 0.20 YOLO 类别一致性 + 0.12 camera/location/time 一致性 + 0.08 multiview 一致性`。客户展示 raw 模型百分比和“综合处置评分：N分”，不把 Fusion 写成百分比。

**LOCKED**：Stable Replay 仅回放此前真实成功调用的结构化 AI 证据；Camera→SLAM、Capability、Scheduler、Dijkstra global topology planner / `plan_route()`、机器人状态、SQLite transitions、Verification 必须仍现场执行。默认 LIVE；仅 Advanced 的受控 AI Runtime 区可主动选 Replay，并在主工作台轻量透明标识。LIVE 失败一律 `HUMAN_REVIEW`。

## D05｜MapCanvas、路线、Fleet 与时间

**IMPLEMENTED / LOCKED（P1-B runtime） / WB-MAP-01 UI target**：白模、机器人、路线、marker 使用唯一 MapCanvas `object-contain` 内层坐标系，不得依据外层 div 百分比。P1-B 的 anchor path、线性插值、弱路线与技术文案是历史实现，作为面客空间总览已被 **WB-MAP-01 SUPERSEDED**；当前视觉是 `IMPLEMENTATION_DIVERGENCE`。保留真实 backend node/segment order、电梯暂停与无合法 node_path 不画路线；未来以统一 deterministic Demo Navigation Waypoint Geometry 呈现合法可行走路线，不要求 3D/Nav2/动态避障。

**P1-B Camera evidence runtime IMPLEMENTED / WB-CAMERA-01 UI target**：before/after asset、persisted controlled bbox、真实 Cloud/Verification 和完整原图坐标事实继续有效；旧 Workbench 双槽 `object-contain` 证据墙、监控墙直接显示 bbox/置信度、Camera ID/证据 badge 及客户 Header 技术状态 **SUPERSEDED BY WB-CAMERA-01**。面客墙必须使用三路动态槽位、无 bbox 的原始 before/after 画面、业务状态/地点/播放视觉入口/展示时钟；Evidence/Advanced 保持原比例和 bbox 真实性。

**IMPLEMENTED / LOCKED（P1-A/B）**：`locate` 以 bbox 底边中心（液体用合理区域代表点）调用 `map_pixel_to_slam(camera_id,u,v)`，持久化 building/floor/zone/map/x/y，之后才显示 marker。Scheduler 当前 map 与 target map 调 Dijkstra global topology planner / `plan_route()`；不是 Demo ID 固定路线。Demo03 基线故事为 B1F → 电梯 → B2F → Skybridge → A2F 地毯易拉罐；连续运行仍遵守当前 Fleet，不能偷偷重置位置以强制重复基线路线。

**IMPLEMENTED / LOCKED（P1-B runtime） / WB-DETAIL-01 UI target**：任务后机器人保留终点与低透明路线；Demo03 验收失败 `HUMAN_REVIEW` 仍在 A2F，Demo04 人工路径无人移动。复位仍遵守 P1-A 显式 baseline/reset 边界，不因普通新事件或刷新自动复位。客户时间轴可只读 SQLite transition timestamp 与处理中真实持续时间；“客户层显示模型真实 latency”已被 **WB-DETAIL-01 SUPERSEDED**，真实 latency 仍由 Advanced 投影。路线起点取 ASSIGNED 快照，不用终态 Fleet 倒推。

**P1-B 刷新/失败边界**：localStorage 仅保存当前 event ID；GET SQLite 重建，不保存第二份事件/Fleet/route。sessionStorage request keys 防止同一会话刷新重发；异步快照不得覆盖不同 event 或倒退 transition。旧“任何网络结果均不自动重试模型”的表述被 **AI-RESILIENCE-01** 限定覆盖：仅由后端对已分类瞬时 provider 故障做一次重试，前端不得重试 storm 或 Replay。该机制不等于跨标签页/服务器端全局幂等，后者为 P2。创建失败只显示本地连接提示，不捏造已保存 HUMAN_REVIEW。

## D06｜Event Center

**P1-D 历史实现 / EVENT-01 当前 LOCKED TARGET**：旧“**AI Event Handling Archive Center / AI 事件处置档案中心**”“read-only trace”及首页 SQLite/不重跑等技术表述，**SUPERSEDED BY EVENT-01**；不得继续作为面客页面目标。Event Center 当前目标是“事件中心”的 AI 清洁事件档案/工单中心：同一 `CleaningEvent` 实时进入、默认发现时间倒序、新事件不得抢走当前详情，只提示“有 N 条新事件”。列表以事件、地点、发现时间、处置方式、执行者、当前/最终状态为主，技术 ID/模式只可用于搜索或 Advanced。

**LOCKED**：主筛选固定为全部、处理中、已自主闭环、待人工处理、异常。处理中为已进入处置但未 terminal；已自主闭环为“无人介入 + 机器人执行 + fixed-camera verification PASS + CLOSED”；待人工处理包含 `HUMAN_FALLBACK` / `HUMAN_REVIEW` 并在 Item 内细分搬运/复核；异常只表示 Cloud、定位、规划、调度、验证等系统或流程失败。正常 Human Fallback 绝不标为异常。

**LOCKED**：支持按 Event Type、Camera ID、Building/Floor、Robot Name、Event ID 搜索；轻量筛选为时间范围、事件类型、处置方式（机器人自主处置 / 人工兜底 / 人工复核 / 系统异常）。列表采用两级紧凑信息，不在主列表展示 YOLO/Qwen/Fusion、SLAM x/y、bbox、Dijkstra route、latency 或 `required_capabilities`。

**P1-D 基础 / EVENT-01 当前 LOCKED TARGET**：Workbench 的 `EventDetailPanel` 仍是唯一详情事实投影，Event Center 必须使用同一 renderer 的 read-only mode：不重跑模型/调度/机器人、不自动滚动，展示事件发生时的 evidence、空间、robot、route、AI、verification snapshot。旧紧凑技术列表、历史专用标题/字段、或与 Workbench 不同的详情视觉壳均 **SUPERSEDED BY EVENT-01**；两页只允许 live action 与 read-only 的差异。`/events?event=EVT-xxxx` 保存选择，首次进入不自动打开第一条，切换不得闪烁。

## D07｜Analytics

**P1-E 历史实现 / ANALYTICS-01 当前 LOCKED TARGET**：旧 `AI Autonomous Cleaning Operations Analysis Center / AI 自主清洁运营分析中心` 大标题、三层纵向长页、客户数据来源说明、筛选栏和 Data Composition 卡 **SUPERSEDED BY ANALYTICS-01**。当前面客产品为一级“运营分析”，二级“运营洞察”（默认）与“数据统计”：运营洞察单屏按 5 KPI → 最多三列横向 AI运营建议 → 近30天 Heat Layer 排列，右侧只保留固定共享 Chat；数据统计一屏 2×2；客户不必滚动长页才理解结果。此前右侧 Advice + Chat 布局 **SUPERSEDED BY ANALYTICS-DELTA-01**。所有 KPI 仍只能由后端 CleaningEvent / Transition 的确定性计算提供，前端和 Agent 不得 hardcode/编造。

**LOCKED**：5 KPI 固定为自主闭环率、人工介入率、首次处置成功率、平均响应时间、平均闭环时间。客户卡仅名称、核心值、轻量图标；旧样本/统计口径/分子分母/责任边界文案 **SUPERSEDED BY ANALYTICS-01**，但其真实定义仍在 Backend、测试与 Advanced。自主闭环率是有效事件中“无人介入 + Robot 完成 + verification PASS + CLOSED”；人工介入率是 `HUMAN_REVIEW` 或 `HUMAN_FALLBACK` 的有效事件比例；首次处置成功率为第一次 verification PASS；平均响应为确认至实际开始；平均闭环为发现至 `CLOSED`。处理中/系统异常的 denominator 规则仍不可伪造。

**P1-E 数据基础 / ANALYTICS-01 当前 LOCKED TARGET**：Heatmap 继续以真实 `map_id/x/y/zone` 位置事实聚合，并保留热点到 Event Center 的只读 drill-down；旧 Scatter/symbolSize 气泡和粗粒度 overview projection 是 `IMPLEMENTATION_DIVERGENCE`，**SUPERSEDED BY ANALYTICS-01**。正式视觉必须是半透明连续 Gaussian/Blur Density Heat Layer：低频蓝/青、中频黄、较高橙、最高红，保留底图可读性；仅 Top 2–3 慢呼吸。未来必须建立可验证 Heatmap Projection Geometry 和五个 Canonical Zone 的确定性测试，禁止把热点放到错误楼栋/建筑外。客户不默认显示来源说明；正式 Interview Dataset 仅 Canonical 30-day DEMO_HISTORY + 合法 Interview Runtime，排除开发/测试/验收/Legacy 脏数据。

**P1-E API/事实基础 / ANALYTICS-01 当前 LOCKED TARGET**：事件类型/时段/日期过滤保留为后端能力但从客户运营洞察移除，正式窗口固定近30天。数据统计必须把 raw event type 先归一为 Canonical Customer Event Type 再聚合，未知/旧数据只允许一行“待研判”。热点 Top 标签只显示地点/事件数，其余 hover 只显示地点、30天数量、主要事件类型；内部 ID/坐标不面客显示。Event Center drill-down 仍携带合法位置/时间查询且不重跑 Runtime。时段、利用率、事件类型结构和闭环表现改在数据统计 2×2 中呈现；FlashBot Max 继续排除清洁利用率。

## D08｜Robot Operations Agent 与 Policy Guard

**IMPLEMENTED / LOCKED（P1-F）**：系统只保留两个必要 Agent：Multi-view Perception Agent（主动视觉取证）与 Robot Operations Agent（自然语言理解、运营分析、白名单工具选择、低风险任务执行、Observe/Replan/Close）。不得新增 Heatmap / Scheduler / Dijkstra / Camera-to-SLAM / RAG Agent；RAG 仅可作为 Robot Operations Agent 的 Knowledge Tool。

**IMPLEMENTED / LOCKED（P1-F）**：Robot Operations Agent 有 Read Tools（事件、详情、KPI、热点、利用率、robot/fleet/capability/POI/location/task/camera evidence 等）及低风险 Action Tools（创建清洁/配送/待命任务、dispatch/pause/resume/cancel、请求证据、状态更新）。任务可直接执行但必须经 Policy Guard；Relocation 目标只可来自合法 POI / approved location，Agent 不得直接控制底盘坐标。

**IMPLEMENTED / LOCKED（P1-F）**：Agent 永远没有 `update_slam_map`、禁行区/范围/能力/标定/Coverage/Scheduler policy/自动处置阈值/速度/门禁/电梯权限等 Write Tools。安全边界必须由代码级工具白名单实现，不是 Prompt 自律。物理动作需写 Action Audit：用户原话/ASR、intent、tool/args、Policy Guard、Task ID、机器人、结果、异常、replan、最终状态。

## D09｜Agent 页面形态、Analytics Advice 与语音

**P1-F 历史实现 / AI-UI-01 当前 LOCKED TARGET**：P1-F 已实现且保留的事实是唯一共享 Robot Operations Agent，以及跨页不丢失 `AgentSession`、`AgentMessage`、`AgentActionAudit`、Task context。其旧 UI Shell（Workbench / Event Center 横向 Floating Window、仅 Header / Drag Handle 拖动、现有展开式 Tool/Task Panel）**SUPERSEDED BY AI-UI-01**，当前实现记录为 `IMPLEMENTATION_DIVERGENCE`。AI-UI-01 要求 Workbench / Event Center 默认左下圆形可拖动 AI 悬浮球、点击后的完整 Chat Window；Analytics 不显示圆球，右侧固定区只保留完整 Chat，而 AI建议位于左侧 KPI 后的横向卡。旧“右侧 Advice + Chat” **SUPERSEDED BY ANALYTICS-DELTA-01**；聊天入口在当前可视高度内可发现。三页继续共享同一 Agent、Session、Task / Audit / Backend State，不得新建第二 Agent。

**P1-F runtime 基础 / ANALYTICS-01 当前 LOCKED TARGET**：Page Context 继续注入 Workbench event/fleet/map/robot/camera/stage、Event Center selected snapshot/filters、Analytics KPI/hotspot/chart；任务仍从真实后端 Task 返回。旧面客 Chat 显示 Tool Audit、request/completion/model turn/policy/raw result/Task ID，以及 disabled 麦克风/“语音服务未配置”文字，**SUPERSEDED BY ANALYTICS-01**。三页同一完整 Chat 只显示用户问题、AI回答和必要状态；任务仅显示简洁业务确认卡（正式机器人名、合法起终点、状态），技术审计在 Advanced。语音入口从当前面客 Chat 完全移除，不以 disabled 替代。

**P1-F runtime 基础 / ANALYTICS-01 当前 LOCKED TARGET**：Analytics Advice 不是第三个独立运营分析 Agent。确定性 Engine 继续提供 KPI/Heatmap/Time/Utilization，Robot Operations Agent 只可总结事实、提供建议或经 Policy Guard 执行合法任务，不能发明数字/区域/机器人/ROI/收益或改 Scheduler/阈值/范围/能力/地图。旧 3–4 条、Data Window/Generated At、related events、长 evidence/内部资源名的客户展示 **SUPERSEDED BY ANALYTICS-01**：默认最多三条，每条标题 + 一句发现 + 一句可执行建议；完整证据链只在 Advanced。

## D10｜Multi-view Perception Agent

**IMPLEMENTED / LOCKED（P1-C）**：新链路固定为：Fixed Camera → Edge YOLO / controlled edge evidence → **Single-view Cloud VLM** → Evidence Sufficiency Judgment → conditional Multi-view Perception Agent → Multi-view Cloud VLM → Business Decision → Camera→SLAM → Capability → Scheduler → Robot → Verification。`confidence` 与 `evidence_sufficient` 是不同字段；Single-view VLM 应输出 event type、need action、confidence、evidence sufficient、ambiguity type（reflection / occlusion / perspective / lens contamination / insufficient view / small object / semantic uncertainty / other）。

**IMPLEMENTED / LOCKED（P1-C）**：Evidence Sufficiency Gate 的优先级高于最终 confidence disposition。Single-view VLM 同时返回 `confidence`、`evidence_sufficient`、`ambiguity_type`；当 `evidence_sufficient=false`，且 ambiguity 为 reflection / occlusion / perspective / lens_contamination / insufficient_view 等可由额外视角缓解的问题，并存在合法 supporting cameras 时，Multi-view Agent 可通过真实 model tool calling 先主动补证。此时不得仅因 Single-view `confidence < 0.50` 提前终止为 `HUMAN_REVIEW`。正确顺序为 Single-view evidence → evidence sufficiency → 可恢复时自主 Multi-view evidence acquisition → final semantic judgment → confidence gate。

**IMPLEMENTED / LOCKED（P1-C）**：Multi-view 是 Active Visual Evidence Acquisition，不是 “if confidence < threshold” Workflow。模型先只看 Main Camera Image、YOLO bbox/detection、必要 Camera Context；以 `tool_choice=auto` 自主决定是否补证、选哪 1–2 路、是否继续、何时停止。没有合法 supporting camera、Evidence Fetch 失败，或最多 2 rounds 后仍 `evidence_sufficient=false` 时，必须 `HUMAN_REVIEW`；即使 raw confidence 较高，最终 `evidence_sufficient=false` 也不得自动机器人处置。不得按 `demo_id` 强制、不得初轮塞三图、不得 `tool_choice=required`、不得前端 `setTimeout` 假装 Agent。

**IMPLEMENTED / LOCKED（P1-C）**：Agent 只有 `find_supporting_cameras()`、`fetch_camera_evidence()`、`finish_visual_judgment()` 这类等价工具；最多 2 路额外摄像头、最多 2 个 evidence acquisition rounds。PoC Evidence Adapter 可返回 controlled evidence assets，必须如实说明，不得假装 RTSP 同步；未来可替换 RTSP/VMS/NVR/Camera Platform。Agent 不得改 Coverage、邻接、calibration、SLAM、地图、机器人、confidence 或自动处置阈值。

**IMPLEMENTED / LOCKED（P1-C runtime） / EVENT-01、WB-DETAIL-01 UI target**：Demo02 必须由真实模型自主发起 Tool Call：CAM-A1-01 单视角看到液体/反光歧义 → Coverage candidate search → 选择 1–2 路（受控证据可为 A1-02/A1-04）→ evidence fetch → multi-view Cloud → final semantic judgment → confidence gate → 高仙 Omnie → verification → CLOSED。最终 `0.50 <= confidence < 0.85` 的 independent targeted second review 可读取本次合法取得的完整 evidence set，但不得读取上一轮模型答案或 reasoning。旧“客户 UI 展示 Agent Trace / Tool Audit / Evidence 明细”的视觉范围已被 **WB-DETAIL-01 / EVENT-01 SUPERSEDED**：客户只看业务进度；仅在 Event Detail 的 AI evidence 区如实展示与图片匹配的受控 edge YOLO bbox/对象/置信度、两张等宽补证图片和独立的 Multi-view VLM judgement。Advanced 才显示工具/参数/轮次/API 等技术 trace，仍禁止 Chain-of-Thought。

## D11｜External Delivery Platform Integration

**LOCKED / TODO**：清洁仍是主业务；配送用于证明 Robot Operations Agent 可跨业务扩展。对外只表述“在获得相应平台授权、开发者资质及 API 权限后，可接收园区相关配送订单/状态并与楼宇配送机器人任务双向同步”。未授权时只能显示 `ADAPTER READY` / `AUTH REQUIRED`，绝不显示 `CONNECTED` 或伪造平台 callback。

**LOCKED / TODO**：真实 Platform Webhook 后走确定性 Delivery Adapter → Address / POI Normalization → Policy → Delivery Workflow → FlashBot Max → Status Callback；地址模糊、自然语言变更、机器人/电梯异常、目标冲突等不确定情况才由 Robot Operations Agent 介入。

## D12｜阶段 Runtime（已实现，继续锁定）

**IMPLEMENTED / LOCKED**：阶段 API 与 SQLite 审计已拆分；Cloud 仅在 cloud-review，Scheduler 仅在 assign，Verification 仅在 verify 或 Demo04 人工完成后。`assignment_decision` 是当前行动机器人的唯一事实源；旧 `/runs/*` 已 410。后续实现必须保留该边界，不能回到“先算完整结果再播放”。

## D13｜Advanced Technical Observability / 高级模式（P1-H capability IMPLEMENTED；ADVANCED-01 UI LOCKED TARGET）

**P1-H backend capability IMPLEMENTED / ADVANCED-01 current LOCKED TARGET**：Advanced Trace、Runtime/Tool Audit、Reality Matrix、持久化 Trace、API、脱敏和测试继续是 read-mostly 技术透明/审计能力，不是客户运营页、配置后台、训练平台、SLAM/Scheduler 编辑器或黑客终端。旧 **Technical Observability & Execution Trace Inspector** 前端页面及其动态展示，**SUPERSEDED BY ADVANCED-01**：正式面试前端改为用户技术图片讲解页；这不是删除底层能力。

**IMPLEMENTED / LOCKED**：底层仍只允许查看、审计、追溯，绝不允许编辑 SLAM、Camera Calibration、Camera Coverage、禁行区、清洁/巡检范围、机器人 Capability、Scheduler Policy、自动处置 Threshold、Dijkstra topology、门禁/电梯权限、安全速度或 Agent 工具权限；未来 Admin / Configuration 是独立产品能力。旧前端 LIVE / Stable Replay 切换控件 **SUPERSEDED BY ADVANCED-01**，不得出现在正式面试 Advanced 页面。

**P1-H historical UI / backend capability retained**：Runtime Strip、63/37 Trace → Node → Inspect、Node detail、tool/error/reality projection和相应安全脱敏仍可作为工程能力/测试事实；其面试前端展示方案 **SUPERSEDED BY ADVANCED-01**。不得显示 Runtime、Provider/Model、latency、Node、Tool、Trace、Reality Matrix 或任何 LIVE/Replay UI；技术图容器才是正式页面主体。

**IMPLEMENTED backend capability retained**：AI Recognition、Spatial/Capability/Scheduling/Route、Runtime/Model/Tool/Error、System Reality Matrix 四类 Trace 继续存在并可审计；它们不再是面试 Advanced 页的默认四个 UI 模块。

**IMPLEMENTED backend capability retained**：AI Recognition Trace 继续记录 Edge Detection、Single-view Cloud VLM、Conditional Multi-view Perception Agent、Multi-view Cloud Judgment、Business Decision / Fusion、Verification。Multi-view 未发生时仍如实记录，且禁止 Chain-of-Thought、scratchpad/reasoning tokens；受控 edge 仍不得冒充 REAL YOLO。旧 Node 输入/输出/bbox/ROI/confidence/latency 等前端展示 **SUPERSEDED BY ADVANCED-01**，不在正式页面默认显示。

**IMPLEMENTED backend capability retained**：Spatial / Capability / Scheduling / Route Trace 继续保存 Camera→SLAM、Capability Engine、Scheduler、Dijkstra Route 的真实事实；清洁机器人仍只由 Capability Engine + Scheduler 选择，Dijkstra 仍仅代表园区级全局 topology。旧 camera/u-v/calibration、约束、评分、node/cost 等 Trace 前端展示 **SUPERSEDED BY ADVANCED-01**，不在正式页面默认显示。

**IMPLEMENTED backend capability retained**：Runtime Observability 继续保存 Runtime/Model/Tool/Error/Recovery，Tool Trace 继续保存真实 trigger/start/duration/status/summary，错误 taxonomy 与 LIVE failure 禁止 silent Replay 的事实不变。上述 Runtime、Tool、Error 的动态前端 UI **SUPERSEDED BY ADVANCED-01**。

**IMPLEMENTED backend capability retained**：Source Badge、Reality Status/Matrix 继续从 Runtime/configuration/evidence/authorization facts 自动投影，覆盖模型、证据、空间、调度、路线、机器人、设施、验证、Replay、Delivery 与 ASR，前端不得伪造/手改。旧 Source Badge/Reality Matrix 的 Advanced 默认展示 **SUPERSEDED BY ADVANCED-01**。

**IMPLEMENTED backend capability retained**：Advanced API 仍只读投影 CleaningEvent transitions、Cloud requests、Agent Audit、spatial/capability/assignment/route/verification/provider/reality metadata；不得独立重跑模型、Scheduler 或 Route Planner，也不得伪造这些记录。Trace ID 关联与原生 Delivery/Relocation 的 P2 边界不变。正式 Advanced 面试页不再默认请求/展示这些数据，改为 ADVANCED-01 图片讲解容器。

## D14｜Interview Demo Batch 1 全局合同（LOCKED TARGET）

**SHOW-BASE-01**：双击 `start_demo.command` 的未来正式行为是建立新的 Show Session，使四个官方 Demo 可立即独立触发；只重建本场 current-event/Fleet/browser session，不删除 Event Center、Analytics、正式 Runtime 或 AI Integration 的历史。新 Session 的 S5、Omnie、SC50、FlashBot Max 分别回各自 canonical 待命点；同一 Session 内不得在 Demo 完成后自动瞬移。不得新增客户可见 Reset 按钮；任何终态或可终止失败必须释放其它 Demo 的触发能力。旧“启动仅复用持久 Fleet，只有人工 Reset 才恢复演示初态”的**启动语义**在正式 Show 场景 **SUPERSEDED BY SHOW-BASE-01**；底层显式 reset 能力和历史保留事实不删除。

**DATA-BOUNDARY-01**：客户默认数据是 Canonical 30-day `DEMO_HISTORY` 与正式 `INTERVIEW_RUNTIME`；TEST、ACCEPTANCE、DEV、DEBUG、LEGACY、INTEGRATION TEST、自动化验收和开发实验均排除于 Event Center、Analytics、Advice、Agent 客户问答及客户报表，但保留在数据库/Advanced/Engineering。未来需由 Codex 建立可靠 runtime/dataset 标识；不得增加客户数据源开关。

**PRESENTATION-01 / LAYOUT-01**：所有面客页统一正式机器人名、客户状态语义和客户空间名；内部 ID、PoC/Mock/Replay/Test 操作文案移至技术层。`1440×900` 与 `1920×1080` 是正式验收基准：Workbench 核心首屏可见，Event Center 列表/详情各自滚动，Analytics KPI→Advice→Heatmap 与右侧固定 Chat 均可发现，Chat 输入固定可见；普通正文主要 13–14px，禁止用大规模 9–10px 小字塞内容，也不得有异常横滚、固定层遮挡或裁剪。

**DEMO-CONTRACT-01**：Demo01 是 S5 室外标准闭环；Demo02 是真实证据不足后由 Agent 自主补证（`primary-ambiguous-v2.png`，不可 demo 特判）；Demo03 是 SC50 从 B1F 经电梯/B2F/空中连廊到 A2F 的跨楼调度；Demo04 是 A2F 大件零清洁候选、FlashBot Max 不得清洁、正确 HUMAN_FALLBACK。推荐讲解顺序 1→2→3→4，但不得强制 UI 顺序。四者同一 Runtime、不同真实分支；未来逐项 LIVE E2E 与一次连续 New Show Session E2E 均为强制验收。完整逐项锁定目标见 `INTERVIEW_DEMO_RECONCILIATION.md`。

## D15｜Interview Demo Batch 2 Agent Runtime 合同（LOCKED TARGET）

**OPS-AUTO-01 / OPS-CONTINUITY-01**：完整且合法的 Delivery、Relocation 或 Agent 主动任务指令可创建→派发→由后端 Show Runtime 自动演示执行；不得要求客户反复 Advance/推进PoC。Delivery 仍依序经过真实持久化状态，阶段可展示约 1.5–3 秒，但 React lifecycle、Timer、Chat 展开或页面可见性不是业务驱动。Chat/Map/Fleet/Event Detail/Backend Task 必须投影同一事实，切页/重挂载/收起 Chat 不得中断；成功、取消或失败全页一致。旧“Delivery/Relocation 必须由操作员逐步 Advance”的**客户执行交互**已被 **OPS-AUTO-01 SUPERSEDED**；底层真实状态机、持久化、route/Fleet Guard 与非伪造事实继续保留。

**AGENT-SESSION-01**：新 Show Session 必须创建新 Robot Operations Agent Session，不能恢复上一场 Chat、interaction context 或 active task；同场所有允许 AI 的页面仍共享一条连续对话。新 Chat 不清空 DATA-BOUNDARY-01 允许的业务查询，且横向运营建议是近30天分析快照、不是 Chat History。

**AGENT-AUTHORITY-01**：Agent 只能理解、编排和调用受限工具；清洁机器人永远由 Capability Engine + Scheduler + Deployment Policy 确定，FlashBot Max 只承担配送。待命必须由用户指定机器人；暂停/取消/抢占必须有明确意图；Demo04 人工完成只可由明确 Operator/User Action 触发。POI、route、Fleet、占用、电量和部署 Guard 均不可绕过，拒绝时必须诚实解释。

**AI-RESILIENCE-01**：仅 provider timeout、临时网络/5xx/rate limit 等明确瞬时技术故障允许一次自动短暂重试；evidence/confidence、Multi-view、Camera→SLAM、Capability zero candidate、route 与其他业务硬约束绝不靠重试刷答案。二次技术失败安全转 HUMAN_REVIEW/终态并释放其它 Demo；LIVE 绝不 silent fallback 到 Stable Replay。客户只见“云端AI研判中”或最终可理解的安全结论，attempt/HTTP 细节留 Advanced/Logs。

## D16｜Interview Demo Batch 3 Evidence / Runtime Integrity（LOCKED TARGET）

**EVIDENCE-INTEGRITY-01**：预置素材文件不等于已发生业务证据。新 CleaningEvent 只可消费 Primary Before、当前 metadata 和已发生 Edge Evidence；After 只在实际 Cleaning 完成后，Demo04 只在明确人工完成后才释放给 fixed-camera Verification。Demo02 Supporting asset 仅在 Single-view insufficiency、Agent 合法选择与成功 fetch 后成立。Event/Agent evidence reads、页面、业务 API、Cloud input 与 Stable Replay 都遵守同一 temporal gate；terminal history 仍可展示已实际发生的完整证据链。旧“完整 asset manifest 可被任意业务 consumer 直接读取”的当前实现是 `EVIDENCE LEAK RISK` / `IMPLEMENTATION_DIVERGENCE`，**SUPERSEDED BY EVIDENCE-INTEGRITY-01**。

**RUNTIME-SINGLE-PATH-01**：Demo01–04 的唯一正式 Mutation Path 是同一 CleaningEvent → Perception → Spatial → Capability/Scheduler → Navigation/Execution → Verification → Archive Runtime。Workbench 只是 projection/control surface，Event Center 只读同一事实，Agent 只能委托同一清洁 Runtime，Analytics 只读同一且符合 DATA-BOUNDARY-01 的事实。现有 Workbench/Operations/AI Lab/Mock/Multi-view/legacy workflow 可执行入口必须在 Unified Implementation 的 Runtime Mutation Path Audit 中逐项分类为 `AUTHORITATIVE INTERVIEW RUNTIME`、`ENGINEERING / TEST ONLY` 或 `RETIRED / REMOVE / 410`；正式 Frontend/Agent 不得使用非权威 mutation path。Stable Replay 仅替换模型响应，继续复用 LIVE 后续业务 stages。

**REQUIREMENT FREEZE**：本次为 Interview Demo Reconciliation 最后一批补充需求。除用户在实施/视觉验收中明确提出新的业务或 UI 问题外，不得主动增加 Agent、业务模块、Demo 或产品定位。下一阶段只有用户明确授权 `UNIFIED INTERVIEW DEMO RECOVERY` 后才可开始，并须先建立逐子项 Matrix，包含 Evidence Availability / Temporal Gate 与 Runtime Mutation Path Audit。

## SUPERSEDED 决策索引

| 旧方案 | 新决策 |
|---|---|
| YOLO low confidence → 立即 Multi-view → Cloud | Edge YOLO → Single-view Cloud VLM → Evidence Sufficiency → conditional Multi-view Agent → Multi-view Cloud |
| 按 `demo_id == demo02` 或固定阈值进入 Multi-view | 真实模型以 `tool_choice=auto` 自主工具调用；不得泄漏测试答案 |
| 初轮三张图同时给 Cloud 后假装主动取证 | 初轮只给主视角；补充图只能来自真实 tool call |
| Command Bar + 独立语音入口 + Floating Assistant 三入口 | 一个 Robot Operations Agent；AI-UI-01 取代旧 Workbench/Event Center 长条浮窗：圆形可拖动入口 → 完整 Chat Window；Analytics 左侧 KPI 后为横向 Advice、右侧固定区只保留 Chat；语音只是输入模态 |
| 独立 Analytics Agent | Robot Operations Agent 的运营分析能力；Analytics Engine 仍确定性 |
| demo_id 直接给固定 location | Camera→SLAM 真实运行时定位（P1-A 代码与测试通过） |
| demo_id 固定 navigation anchors | Scheduler current map + target map → Dijkstra global topology planner / `plan_route()`（P1-A 代码与测试通过） |
| Demo04 cloud 阶段直接 Human Fallback | Cloud → Locate → Capability 零候选 → Human Fallback（P1-A 代码与测试通过） |
| HUMAN_REVIEW 截断/重建时间轴 | 完整历史保留（P1-B 代码、测试与浏览器通过） |
| CLOSED 自动复位机器人 | 终点保留，仅显式 baseline/reset 才复位（P1-A/B 代码、测试与浏览器通过） |
| 正式演示启动仅复用上次 Fleet/current event，需客户手动重置 | **SHOW-BASE-01**：双击启动自动建立新 Show Session、复位本场演示状态但保留历史；无客户 Reset 按钮 |
| 右侧 Advice + Chat 上下分区 | **ANALYTICS-DELTA-01**：左侧 KPI 后横向 Advice，右侧固定区只保留共享完整 Chat |
| 配送/待命必须由客户反复点击 Advance / 推进 PoC 才能走完整状态机 | **OPS-AUTO-01**：明确合法指令自动进入后端 Show Runtime 演示执行；业务状态仍真实持久化、Guard 不变 |
| 预置完整 asset manifest 即可被当前业务页面、Agent/API 或 Replay 任意读取 | **EVIDENCE-INTEGRITY-01**：证据按阶段可用，未来 After/未获取 Supporting 不得泄漏 |
| 多个 legacy/helper workflow 仍可作为正式客户 Runtime 的备用执行入口 | **RUNTIME-SINGLE-PATH-01**：唯一 authoritative Mutation Path；其余必须审计为 Engineering/Test Only 或 Retired |
| raw Qwen next_action 当客户系统建议 | 模型判断与系统业务决策分离 |
| “地面纸巾”“大型纸箱”面客类目 | 其他小型垃圾 / 大件物品 |
| 前端 startedAt + 固定 offset 假时间 | SQLite transition timestamp（P1-A 代码与测试通过） |
| LIVE 失败偷偷成功回放 | NO SILENT FALLBACK |
