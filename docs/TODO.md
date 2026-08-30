# AI 自主清洁 Demo｜真实任务清单

> **状态：LOCKED · Post-merge Interview Freeze · 2026-08-30**
> Unified Implementation merge baseline: `8341eb079fe5a700b4931e0112fdbe5552297785`
> Current main HEAD: 以 GitHub main / `git rev-parse HEAD` 为准
> 历史实施分支 `codex/unified-implementation` / `bdd08e02e0e4fc96d9ad6229949f2c8bf3812136` 仅作历史记录。
> `[x]` 仅代表满足对应验收条件；`[ ]` 包含尚未实现或尚未验收的 LOCKED TARGET。Unified Implementation 已合并，P1-A/B/C/D/E/F/H/G 工程验收通过；用户展示验收仍独立。

## 已实现基线（IMPLEMENTED，禁止回退）

- 阶段 REST Runtime、SQLite transition audit、Cloud/assign/verify 边界、旧 `/runs/*` 410。
- 受控 bbox、真实 Qwen transport、独立二审/Fusion、Phase 2 空间基础、Phase 3 Capability/Scheduler、Dijkstra global topology planner / `plan_route()`。
- **历史基线**曾有基础 Multi-view LangGraph、基础 Event Center、Analytics 聚合、确定性 Optimization recommendation 与 Advanced shell；它们不替代后续 P1-C/D/E/F/H 的已实现产品能力，旧 Optimization endpoint 已退役410。
- Demo01、Demo02、Demo04 的既有真实运行记录；Demo03 在 P1-B 历史测试曾为 `HUMAN_REVIEW`，该失败保留；P1-G 正式五次 LIVE 均 CLOSED，见最新验收记录。

## P1-A｜真实清洁 Runtime 与产品名称（先完成）

**Closure 状态：IMPLEMENTED · Reviewer A/E PASS。** 真实 Demo01/Demo04 LIVE→persist→Replay 均闭环；此前 Demo04 业务语义阻塞已由用户确认的 scoped metadata 解除，未更改模型结果或能力/调度规则。

- [x] Demo04 业务事实确认、metadata→Scenario/Camera/Zone context→一/二审透传与持久化、模型 veto 不覆盖、旧 context Replay 拒绝、真实 LIVE→Replay 人工闭环。
- [x] Reviewer A/E 最终 PASS，完整测试/构建和六文档一致性核查通过；按独立 P1-A commit/push 交付。
- [ ] P2 后续强化：Fleet/event/transition 跨表原子事务与多请求并发保护；route error 的 assigned reservation 释放；旧 Phase 3 fixtures 静态 map 兼容兜底；API/browser E2E；主工作台外静态旧机器人名称清理；秒级 timestamp 精度与根目录测试相对路径可移植性；P1-H 统一错误层级。不能把多用户/进程崩溃中途原子恢复宣称已经验收。旧合成 replay 已删除，不再作为遗留项。

- [x] **共享 Fleet / 活跃 Runtime 命名投影**：内部 ID 不变；共享 Fleet 与当前事件候选使用四个正式客户名称，Product Capability 与 Demo Configuration 分开。非活跃旧 UI 文案清理留 P2；未来 Analytics/Task/Action Card 的全产品投影随对应阶段完成。
- [x] **Camera→SLAM Runtime 接入**：`locate` 从主 bbox 计算接地点，调用 `map_pixel_to_slam()`，持久化 map/x/y/building/floor/zone；marker 只在定位后出现，客户/Advanced 按锁定层级显示。
- [x] **Dijkstra global topology planner / `plan_route()` Runtime 接入**：`start-navigation` 读取共享 Fleet 当前 map 与已定位 target map，调用 `plan_route()`，将 connector graph 转为可视 anchor path；删除 demo_id 固定路径。
- [x] **Demo04 正确能力边界**：移除 cloud 阶段大件直接人工特判；完整运行 Cloud → Locate → Capability Engine → zero candidate → `HUMAN_FALLBACK` → 人工完成 → verify。
- [x] **共享 Fleet 状态与真实时间**：机器人位置、电量、状态使用同一读模型；任务终点保留，new demo/reset 才复位；前端读取 SQLite transition timestamp、真实 duration、真实 cloud latency。
- [x] **Stable Replay 重定义**：只保存/选择既有真实 AI structured evidence 回放，其他 Runtime 阶段仍真实执行；P1-A 当时在 Advanced 的最小 AI Runtime 控制区提供 LIVE / Stable Replay 主动选择、云端模型可用状态、最近请求状态和 latency；P1-H 已将其纳入完整只读 Trace Inspector。

## P1-B｜Workbench、MapCanvas 与 EventDetailPanel（工程 IMPLEMENTED · A/E PASS）

- [x] **P1-B MapCanvas / backend topology 投影（历史已实现事实）**：建立 `object-contain` 内层画布转换，保留真实 backend route order、marker、Fleet 与电梯停留，修复 letterbox 漂移。其 anchor-to-anchor 线性 visual path、弱路线和技术化资产栏已被 **WB-MAP-01 SUPERSEDED**，不得当作面客空间调度已完成。
- [x] **P1-B 机器人路线 playback（历史已实现事实）**：真实 topology anchor path 连续插值、已走/未走路径与电梯入口约 1 秒停留；CLOSED / HUMAN_REVIEW 保留终点和路线。它不等同业务可行走 Waypoint Geometry。
- [ ] **WB-MAP-01｜机器人资产与园区空间调度地图（LOCKED TARGET；未 IMPLEMENTED）**：中央区域改为客户空间调度总览；四张正式命名机器人卡统一显示名称/图片/状态/电量/位置，hover 才给 SLAM/能力/任务，选中机器人克制高亮。清理客户英文/工程术语、重复右上状态卡；强化路线和动态业务事件点。保留 backend 作为所有 route/waypoint/distance/ETA/设施/起终点事实源，建立统一 Demo Navigation Waypoint Geometry，杜绝穿墙/穿楼/漂移/前端或 LLM 编造路线。用户必须亲见 Demo01 S5 室外、Demo02 Omnie A栋、Demo03 SC50 B1F→电梯→B2F→连廊→A2F 的合法动画，才可 USER_ACCEPTED。未来报告须逐项交付 WB-MAP-01.1–01.15 的 Requirement→Code→Test→Screenshot/User Acceptance；任一缺失不得 IMPLEMENTED。详见 `INTERVIEW_DEMO_RECONCILIATION.md#wb-map-01机器人资产与园区空间调度地图`。
- [x] **布局与双监控矩阵**：实现 72/28、31/69、右详情独立滚动、145–155px 资产栏、相机 `object-contain` 规范；四个 Demo before/after 状态矩阵；Demo02 补充图永不替换顶部监控。
- [ ] **WB-CAMERA-01｜固定摄像头监控墙与“AI机器人调度大脑”（LOCKED TARGET；未 IMPLEMENTED）**：顶部改为三路等宽动态监控墙，无事件三路 normal/after，事件主 camera 第一槽 before 原图、无 YOLO/bbox/算法标签；卡片用红/橙/短绿的真实 Runtime 状态表达清洁前后与 AI验收。客户卡仅地点、中心半透明播放视觉入口、右下动态时间，使用不拉伸的 cover/crop；Evidence/Advanced 保留原比例与 bbox。删除双路/受控证据小字、Camera ID/技术 badge、旧页面名/顶部 stage/LIVE/Replay，客户页面统一“AI机器人调度大脑”；Demo control 保持“…”二级入口。Demo01–04 都要展示同一完整监控循环。未来报告须逐项交付 WB-CAMERA-01.1–01.19 的 Requirement→Code→Test→Screenshot/User Acceptance；任一缺失不得 IMPLEMENTED，用户未亲眼验收不得 USER_ACCEPTED。详见 `INTERVIEW_DEMO_RECONCILIATION.md#wb-camera-01固定摄像头监控墙与ai机器人调度大脑页面表达`。
- [x] **统一 EventDetailPanel**：实现 `mode="live"` / `mode="history"`；实时自动跟随一次 smooth scroll，历史只读不滚动、不重跑；统一字段、卡片、颜色、stage hierarchy、历史 snapshot。
- [x] **P1-B 客户表达收敛（历史已实现事实）**：全量 enum 中文化；Fusion “N分”、系统决策分层；客户层不展示 raw next_action / 公式 / Chain-of-Thought。其旧 Workbench 详情视觉范围被 **WB-DETAIL-01 SUPERSEDED**，不得把历史收敛写成新面客详情已完成。
- [ ] **WB-DETAIL-01｜面客事件处置详情与实时业务进度（LOCKED TARGET；未 IMPLEMENTED）**：Workbench 右侧从技术流程/免责面板改为面客实时业务详情；业务阶段逐步可感知，Cloud/Multi-view/Verification 只按真实调用推进，导航/清洁可感知但不伪造事实。客户卡只呈现事件、识别、单一最终 AI置信度、系统处置评分 N分、真实二维空间定位、正式机器人名及真实 hard filter→score→assignment、真实路线和 after image→AI验收→结果；技术 trace/latency/schema/PoC 边界移 Advanced。四 Demo 必须可终态化，失败释放启动条件，WorkBench/Agent ownership 清楚；route 缺 distance/ETA 是实施 Gap，不能编造。未来报告必须逐项交付 WB-DETAIL-01.1–01.11 的 Requirement→Code→Test→Screenshot/User Acceptance，任一缺失不得 IMPLEMENTED。详见 `INTERVIEW_DEMO_RECONCILIATION.md#wb-detail-01面客事件处置详情与实时业务进度`。

验收：前端 17/17、backend 64 PASS + 2 opt-in skipped、build 与 diff check PASS；主代理实际浏览器验证 Demo04 人工闭环、Demo03 跨楼导航/验收失败保留、同会话云端处理中刷新不重复请求、终态刷新、history 只读、1024/1440/1920 桌面布局。详情见测试事实源。最终产品/用户验收仍未代替。

- [ ] **P1-B/P1-H P2**：同会话 request keys 的终态清理、跨标签页/后端全局幂等、网络结果不确定时的审计恢复流程；当前只读 GET 同步，绝不自动重发模型。未知模型 enum 统一中文待复核，不把未识别语义编造成肯定结论。
- [x] **P1-G Demo03 ROI 工程收口**：P1-B 当时的真实模型曾返回“地面上仍有红色罐体未清理”，verification_pass=false 并转 HUMAN_REVIEW；该历史事实保留。当前通用 ROI/独立二审、5/5 qualifying LIVE、浏览器跨页与 A/E 工程结论均已完成；Demo03 两次 second review 是语义灰区二审，非真实独立 ROI verification。用户主观展示验收仍独立。

## P1-C｜新 Multi-view Perception Agent（IMPLEMENTED · A/E PASS）

- [x] **Single-view Cloud schema 与 Gate 顺序**：第一次仅输入主视角、YOLO bbox/detection、必要 Camera Context；输出 `event_type`、`need_action`、`confidence`、`evidence_sufficient`、`ambiguity_type`。Evidence Sufficiency Gate 优先于最终 confidence disposition：可恢复不足先补证，最终充分 evidence 才进入 `>=0.85` / `0.50 <= confidence < 0.85` / `<0.50` 处置。
- [x] **Evidence acquisition Agent**：以 `tool_choice=auto` 实现 `find_supporting_cameras()`、`fetch_camera_evidence()`、`finish_visual_judgment()` 等价工具；当证据不足、歧义可由额外视角缓解且存在合法 camera 时，模型自主选择补证摄像头，最多 2 路、最多 2 rounds；无合法 camera、fetch 失败或最终仍不充分则 `HUMAN_REVIEW`，不允许 demo_id 或固定 confidence branch。
- [x] **PoC Evidence Adapter、二审与审计**：明确 controlled evidence assets，不伪称真实 RTSP 同步；持久化 Agent Start、single-view result、sufficiency、ambiguity、tool call、candidates、selected cameras、fetch、multi-view result、final decision、latency。最终 `0.50 <= confidence < 0.85` 的 independent second review 可读取合法 evidence set，但不读取上一轮模型答案或 reasoning。
- [x] **Demo02 真实演示**：CAM-A1-01 单视角的液体/反光歧义必须由模型自己发起 Tool Call；补充图来自 tool audit，客户只显示 Tool Calls、Evidence、Selected Cameras、Final Confidence、Decision，不显示 Chain-of-Thought。

验收：22 targeted PASS、backend 86 PASS + 3 paid opt-in skipped、frontend 17/build PASS、真实 LIVE→Replay 与浏览器闭环 PASS。影像版本、真实模型返回与完整编辑提示见测试事实源；新 `primary-ambiguous-v2.png` 为公开受控成像模糊 variant，原图保留。2 camera/2 acquisition rounds 外另设 6 model turns 保护限，不增加取证轮次。这是 P1-C 当时的验收；P1-G 后续五次稳定性证据见最新记录。

## P1-D｜Event Center（IMPLEMENTED · A/E PASS）

- [x] **统一事件索引与状态映射**：同一 CleaningEvent / SQLite；全部、处理中、已自主闭环、待人工处理、异常五类状态；正常 `HUMAN_FALLBACK` 不得归为异常。
- [x] **搜索、筛选与两级 List**：支持 Event Type、Camera ID、Building/Floor、Robot Name、Event ID、时间范围、事件类型、处置方式；默认倒序、新事件不抢占当前历史详情。
- [x] **History Detail Drawer 与 URL State**：右侧 42–46% `EventDetailPanel(mode="history")`；`/events?event=...` 可恢复选择；首次进入不自动选中；切换内容不闪烁。
- [x] **read-only trace 边界**：不做删除、批量状态修改、批量派发、CSV/Excel 导出或其他批量运营动作。

验收：archive backend7/7、frontend archive7/7（全量24/24）、full backend93 PASS+3paid opt-in skipped、build/diff check与浏览器PASS，Reviewer A/E PASS。修复历史ID错配、轮询重叠、新提示闭包/分页、UTC筛选和分类类型；D无未解决核心P0/P1。更大数据量的服务端SQL索引/聚合优化可后续扩展，不宣称生产规模验收。

## P1-E｜Analytics（IMPLEMENTED · A/E PASS）

- [x] **可追溯 Analytics data model**：结构化 30 天 Seed History + 当前 Runtime CleaningEvent Increment；明确“近30天 · 演示历史数据”；真实计算 event/transition-derived 指标，移除固定 response/closure/utilization 与虚构趋势。
- [x] **5 KPI**：实现并记录有效事件 denominator：自主闭环率、人工介入率、首次处置成功率、平均响应时间、平均闭环时间；处理中/系统异常处理规则可审计。
- [x] **Campus Spatial Event Heatmap**：用 map_id/x/y/event_type/timestamp 聚合，复用 SLAM white model；实现 type/time filters、热点 drill-down、跳转 Event Center 的 location/type/time URL filter。
- [x] **辅助分析**：事件结构、区域/时段规律、清洁机器人运营效率；FlashBot Max 不进清洁利用率排名；利用率必须由任务状态时间 ÷ 可用时间计算。

验收：backend定向12/12、完整105项=102PASS+3paid opt-in skipped、前端32/32、build/diff check、实际热点→81条对应档案/Seed来源/UTC范围浏览器验收，A/E PASS。默认近30天；自定义范围按实际period返回；时段保持D07四bucket。

- [ ] **P1-E P2**：Seed滚动插入保留旧档案，未来明确保留/归档策略（当前不自动删用户数据）；真实availability/uptime provider仍缺，利用率假定24小时连续可用；后续按需在UI展示carried_tasks；ECharts首次引入后bundle>500KB可按路由拆包。旧固定Optimization API已在P1-F退役410，客户Analytics接真实只读Agent建议。

## P1-F｜Robot Operations Agent 与配送扩展基础（IMPLEMENTED · A/E PASS）

- [x] **Agent runtime / Policy Guard / Audit**：实现白名单 Read Tools、低风险 Action Tools、代码级禁止 Write Tools、Observe/Replan/Close 与 Action Audit；不得产生 Scheduler / Dijkstra / Heatmap / RAG 等额外 Agent。
- [x] **Task 与 Action Card**：实现 Cleaning / Delivery / Relocation Standby Task；POI 白名单；真实 backend Task ID 与 Fleet/Workbench/Agent 共享同一状态；Agent 不直接操作底盘坐标。
- [x] **P1-F 共享 Agent / Session / 状态与真实语音边界（历史已实现事实）**：Workbench、Event Center、Analytics 共享 session / messages / audit / Page Context，语音链路为 Microphone → real ASR → transcript；只有已配置 ASR provider 才能启用麦克风，未配置时 disabled 或显示“语音服务未配置”，禁止预设文本、timer、mock transcript 或 fake animation。此前 UI Shell 的横向浮窗、仅 Header/Drag Handle 拖动和现有展开式 Tool Panel 已被 **AI-UI-01 SUPERSEDED**，不得继续视作当前目标。
- [ ] **AI-UI-01｜Robot Operations Agent UI Shell（LOCKED TARGET；未 IMPLEMENTED）**：Workbench / Event Center 必须为默认左下、可在整个合法 viewport 内拖动且可持久化的小型圆形 AI 悬浮球，收起只留圆球，点击后弹出完整 Chat Window（身份/欢迎、历史、用户/AI 消息、明显输入、发送、状态、关闭回圆球），而非 Tool/Task Panel。Analytics 不用浮动球；固定统一右侧 AI Area 上半 Advice、下半完整 Chat，并以独立布局/滚动保证左侧长内容时进入页面的当前可视高度内仍可找到输入入口。三页继续共用同一 Agent / Session / Task / Audit / Backend State，禁止新建 Analytics / Optimization / 第二 Conversation Agent。未来报告须逐项交付 AI-UI-01.1–01.7 的代码、测试和用户验收；任一缺失不得标记 IMPLEMENTED。详见 `INTERVIEW_DEMO_RECONCILIATION.md#ai-ui-01ai-运营入口与聊天交互`。
- [x] **Analytics Advice**：成为 Robot Operations Agent 的只读能力，最多 3–4 Read Tool calls、3–4 条含数据依据的建议；默认 snapshot，用户点击才重新生成；不自动改变运营配置。
- [x] **Delivery Adapter boundary**：FlashBot Max原生PoC Fleet / DeliveryTask state machine已实现；外部平台仅在合法授权后接入，未授权显示 `ADAPTER READY` / `AUTH REQUIRED`，不得伪造 webhook / callback。

验收：16后端定向、完整121项=118 PASS+3 paid opt-in skipped、前端39/build、实际LIVE待命/配送与只读Advice；A/E PASS。模型语义失败必须可见，不以重试成功抹掉历史。

- [ ] **P1-F P2**：真实身份权限、分布式任务/硬件幂等、生产设备与外部平台授权、ASR provider、审计保留/检索仍待后续；当前单worker启动恢复只标Interrupted不重发。共享Task接口中的workflow_transitions来自原CleaningEvent，不另存第二份清洁trace。

## P1-G｜验收、回归与文档纪律（IMPLEMENTED；用户主观展示验收仍待）

已完成且可只读复核的隔离 acceptance 证据：正式 LIVE batches Demo01 `acceptance-b0af62b416cc4c03be6c304ddb569a40` 5/5、Demo02 `acceptance-20c748edbaa44c9d86f1257412d92198` 5/5、Demo03 `acceptance-cfee4992075a42839a463253fa0f53dd` 5/5、Demo04 `acceptance-da76bfb5b67e4acaad62a5541d2acdd7` 3/3；post-review Replay 四 Demo 各 3/3、无新 Cloud request。结果位于 `/tmp/cleaning-p1g-acceptance.lf8Dla/acceptance.sqlite` 的 append-only `acceptance_runs.payload`，18条 LIVE 的安全字段表在 `AI_INTEGRATION_TEST.md`。A/B/C/D/E 最终 PASS、backend164/frontend46/build/bash-n/diff通过，以下工程项已勾选；用户主观展示验收仍独立，提交和合并状态以 git log 与 remote 为准。

- [x] **Demo01/03/04 LIVE + Replay 回归**：按 `AI_INTEGRATION_TEST.md` 的次数与字段记录 structured 数值摘要、二审、Fusion、system decision、robot、route、verification、final、latency。
- [x] **Demo02 LIVE Agent 回归**：五次均由模型真实触发 Multi-view Tool Calling，经 search → fetch → multi-view Cloud → 高仙 Omnie → verification → CLOSED；无 demo_id、固定阈值或前端动画作弊。
- [x] **Event / Analytics / Agent 回归**：历史 snapshot/Fleet、状态分类/URL、Analytics 真实指标、Action Card/Policy Guard/Audit 与 Delivery Adapter 授权状态已复核；task-owned HF 人工完成唯一 owner、暂停时钟、取消与跨页恢复均有测试/浏览器证据。
- [x] **实现后文档更新**：代码、测试、浏览器和 A/B/C/D/E 工程审查证据已写入六份事实源。

- [ ] **用户展示验收**：全部工程门槛 PASS；提交与合并状态单独以 `git log` 和 remote 核对。用户主观展示验收仍待，不能由本工程验收替代。
- [x] **面客任务卡投影收口**：`robot_id=null` 的 `HUMAN_FALLBACK` 任务显示“处置方式：人工搬运”，不再显示等待机器人；`East Corridor` 统一投影为“东侧走廊”。仅修正文案投影，不改变 Task/assignment 语义。
- [ ] **P2 模型拒绝措辞**：越权请求已拒绝且无写入，但模型可能泛称“联系管理员编辑”；后续收敛措辞，不能暗示当前产品存在可编辑基础设施的管理入口。约 785KB 构建包拆分延续 P1-E P2。

## P1-H｜Advanced Technical Observability（IMPLEMENTED · A/E PASS）

- [x] **Trace Inspector layout**：63/37浅色只读Trace→Node→Inspect，独立AdvancedView；不是配置后台或满屏JSON。
- [x] **AI Recognition 6-stage Trace**：Edge/Single-view/conditionalMulti-view/Multi-viewCloud/Fusion/Verification，未触发如实显示；缺失不伪造。
- [x] **Unified Tool Trace**：MODEL_TOOL_CALL / SYSTEM_WORKFLOW / USER_ACTION，真实start/duration、结果摘要；历史无timing保持空值，不以历史模型latency冒充tool时长。
- [x] **Reality Matrix**：锁定6类来源，execution_status单独显示；edge明确CONTROLLED EDGE DEMO。真实Cloud不等于生产摄像头/YOLO/设备。
- [x] **空间/能力/调度/路线**：只读已保存共享Camera→SLAM、TaskProfile、Capability候选/排除、Scheduler权重得分、Dijkstra节点/代价。
- [x] **Runtime/Model/Error**：真实request metadata及8类taxonomy，API白名单/敏感信息过滤，LIVE失败不Replay；GET不运行模型/调度/路线。
- [x] **Trace关联**：Event/每消息Request/Task独立关联，sharedSession多任务不串Trace；legacy无回填。Replay模型payload不变，真实Runtime新Trace。
- [x] **H工程验收**：14定向、135完整后端（132PASS+3skip）、前端42/build、浏览器、Reviewer A/E PASS。该条保留 H 当时证据；四 Demo 连续 LIVE/Replay 已在后续 P1-G 完成。
- [ ] **P1-H P2**：独立原生Delivery/Relocation Task Trace入口；生产级OTel/跨服务观测、身份权限、审计留存与持续安全审计。当前本地SQLite单worker，不冒称生产追踪系统。

## 后续 Batch（不在 Unified Implementation Batch 的范围）

- [ ] 在 P1-H 完成并验收后，才另行讨论 Advanced 的非必要增强体验；不得稀释已锁定的四模块 Trace Inspector 范围。
- [ ] 经授权的真实 RTSP/VMS/NVR、生产机器人/电梯/门禁与外部配送平台 Adapter。
- [x] **Batch C / Part 3 Advanced**：已按Unified P1-H完成工程验收；非必要增强不在本轮。

## 不在授权范围

- ROS 2、Nav2/Open-RMF runtime、Docker/K8s、Kafka/Redis/PostgreSQL、真实机器人/电梯/门禁、真实本地 YOLO 主链路。
- 让 LLM 或任一 Agent 修改 SLAM/禁行区/清洁范围/巡检范围/机器人能力/Camera Coverage/标定/Scheduler policy/自动处置阈值/安全速度/门禁或电梯权限。
