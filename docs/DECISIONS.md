# AI 自主清洁 Demo｜锁定决策

> **状态：LOCKED · 2026-08-29**
> 本文件只记录当前有效决策及明确替代关系。除标明 IMPLEMENTED 的事实外，其余产品/技术方案均为 LOCKED TARGET，不得被写成已实现。

## D01｜产品边界与技术底座

**LOCKED**：这是可解释、可演示的园区自主清洁 PoC，不宣称真实生产机器人、电梯、时间同步、动态避障或生产阈值已部署。React + TypeScript + Vite + Tailwind + shadcn/ui 是唯一 UI 底座；ECharts 用于数据可视化，React Flow 仅用于确有必要的关系/流程。后端维持 FastAPI 模块化单体 + SQLite；禁止第二 UI System、Three.js、ROS/RMF runtime、Docker/K8s、大型本地模型。

## D02｜第一部分与工作台信息架构

**LOCKED**：本批只完成自主清洁工作台及四个 Demo。左主区约 72%、右详情约 28%；左上双固定摄像头约 31%、地图约 69%。右详情从 Header 下方开始、独立滚动。整体是浅色、克制、低饱和蓝的企业 SaaS；删除“系统在线”和无意义装饰状态。

**LOCKED**：客户层使用业务中文；技术术语仅 Advanced/技术详情按需显示。一级导航保留“自主清洁工作台、事件中心、运营分析、高级模式”，但后三者完整建设不是本批范围。

## D03｜机器人、Agent 与确定性决策

**LOCKED**：Robot A 处理室外其他小型垃圾；Robot B 处理液体/重污；Robot C 处理室内轻量干垃圾且可 B1→电梯→B2→连廊→A2；Robot D 仅未来配送资产，不进清洁 Scheduler。保持 Robot-first + Human Fallback，人工不是候选。

**LOCKED**：LLM 只做事件语义、所需能力建议、清洁验收；Capability Engine + Scheduler 是 Robot A/B/C 的唯一选择器。Camera→SLAM、Route Planner、Scheduler、Verification 不是 Agent。Multi-view Agent 只在 Demo02 灰区触发，只能使用已锁定工具、最多 2 补充摄像头/2 轮，且客户不展示 Chain-of-Thought。

## D04｜云端模型、门控与 Replay

**LOCKED**：LIVE 必须调用真实 Qwen-VL/DashScope，禁止写死结果、特判成功、人工加置信度或 silent fallback。Prompt 提供 camera/location/surface、YOLO 类别/置信度/ROI、限定 ontology；Qwen 不选机器人。首次 `>=.85` 进入系统判断；`.50–.85` 必须独立二审且不得收到首轮回答；`<.50` 人工复核。`need_clean=false`（语义确为无需处置）、unknown、ignore 是 veto；通用 raw `next_action=human_review` 不能覆盖满足 Fusion 的系统决策，raw action 只在 Advanced。

**LOCKED**：Fusion 仅为 `0.60 raw cloud + 0.20 YOLO 类别一致性 + 0.12 camera/location/time 一致性 + 0.08 multiview 一致性`。客户展示 raw 模型百分比和“综合处置评分：N分”，不把 Fusion 写成百分比。

**LOCKED**：Stable Replay 仅回放此前真实成功调用的结构化 AI 证据；Camera→SLAM、Capability、Scheduler、Dijkstra、机器人状态、SQLite transitions 必须仍现场执行。默认 LIVE；仅 Advanced 可主动选 Replay，并在主工作台轻量透明标识。LIVE 失败一律 `HUMAN_REVIEW`。

## D05｜MapCanvas、路线与 Fleet 状态

**LOCKED / TODO**：白模、anchor、机器人、路线、marker 使用唯一 MapCanvas 坐标系，基于 object-contain 内层真实画布，不得依据外层 div 百分比。地图文字只允许 A栋、B栋、1F、2F。目标使用小型低饱和红 marker，路线/移动规范遵从项目事实源；机器人持续插值，电梯入口暂停约 1 秒并显示“乘梯中”，不做 3D。

**LOCKED / TODO**：任务后机器人保留任务终点与低透明路线；Demo03 Human Review 仍在 A2F，Demo04 人工路径无人移动。仅新 Demo 或“重置演示”复位。地图、hover、Scheduler、未来 Event Center/Assistant 必须读同一 Fleet 状态。

## D06｜定位、路径与时间的真实数据源

**LOCKED / TODO**：`locate` 以 bbox 底边中心（液体用合理区域代表点）调用 `map_pixel_to_slam(camera_id,u,v)`，持久化 building/floor/zone/map/x/y，之后才显示 marker，Scheduler/Route 读取同一目标坐标。客户仅显示可读位置/SLAM 坐标，Advanced 才显示 pixel/mapping 细节。

**LOCKED / TODO**：路线必须由 Scheduler 当前 map 与 target map 调 `plan_route()` 的 Dijkstra 全局拓扑生成，再投影为前端 anchor sequence；不是 Demo ID 固定路线。Demo03 从 B1F 至 A2F，并展开电梯/连廊锚点。

**LOCKED / TODO**：客户时间轴只读 SQLite transition timestamp；处理中显示真实持续时间，模型可显示真实 latency。自动跟随只有一次 smooth scroll，用户手动上滚暂停并出现“回到当前进度”；CLOSED 后不强制滚动。

## D07｜四场景与面客表达

**LOCKED**：客户类目固定为“其他小型垃圾、液体污渍、易拉罐、大件物品、树叶”。bbox 为受控边缘证据：1.5–2px 低饱和红、外扩 8–12%、小标签外置、相邻标签错位。

**LOCKED**：双监控默认左 Demo01 after、右 Demo03 after；各 Demo 运行/验收/关闭的切换严格按 `PROJECT_CONTEXT.md` 的锁定矩阵执行。Demo02 补充摄像头只能在详情 Multi-view 阶段展示，不能替换顶部双监控；该阶段只并排展示 A1-02/A1-04，不重复 A1-01。

**LOCKED / TODO**：Demo03 验收为目标 ROI 验收：输入原类别、bbox/ROI、before/after 全图与 ROI，忽略任务机器人、人员、光影、无关变化；因非目标干扰 retry 时做独立 ROI 二审。Demo04 必须经 Cloud → Locate → Capability 零候选 → Human Fallback，面客语义是“需要处置：是 / 机器人清洁：不适用”，不可把“不需要清洁”作为核心结论。

## D08｜阶段 Runtime（已实现，继续锁定）

**IMPLEMENTED / LOCKED**：阶段 API 与 SQLite 审计已拆分；Cloud 仅在 cloud-review，Scheduler 仅在 assign，Verification 仅在 verify 或 Demo04 人工完成后。`assignment_decision` 是当前行动机器人的唯一事实源；旧 `/runs/*` 已 410。后续实现必须保留该边界，不能回到“先算完整结果再播放”。

## SUPERSEDED 决策索引

| 旧方案 | 新决策 |
|---|---|
| demo_id 直接给固定 location | Camera→SLAM 真实运行时定位（TODO） |
| demo_id 固定 navigation anchors | Scheduler current map + target map → Dijkstra（TODO） |
| Demo04 cloud 阶段直接 Human Fallback | Cloud → Locate → Capability 零候选 → Human Fallback（TODO） |
| HUMAN_REVIEW 截断/重建时间轴 | 完整历史永久保留（TODO） |
| CLOSED 自动复位机器人 | 终点保留，new demo/reset 才复位（TODO） |
| raw Qwen next_action 当客户系统建议 | 模型判断与系统业务决策分离 |
| “地面纸巾”“大型纸箱”面客类目 | 其他小型垃圾 / 大件物品 |
| 前端 startedAt + 固定 offset 假时间 | SQLite transition timestamp（TODO） |
| Multi-view 再次展示主视角大图 | EDGE 展示主视角；Multi-view 仅两补充图 |
| LIVE 失败偷偷成功回放 | NO SILENT FALLBACK |
