# AI 自主清洁 Demo｜锁定决策

> **状态：LOCKED · 2026-08-29**
> 本文件只保留当前有效决策和已明确替代关系。未列出的历史结论不应被当作当前要求。

## D01｜产品目标与真实性边界

**LOCKED**：项目是面试用、可解释的自主清洁 PoC，不宣称真实机器人、真实电梯、真实多机位时间同步或生产阈值已经部署。真实项目基础与 PoC 增强需区分。

## D02｜技术与架构边界

**LOCKED**：React + TypeScript + Vite + Tailwind + shadcn/ui 是唯一 UI 底座；ECharts 用于数据可视化；React Flow 仅在确有流程/关系展示需求时引入。禁止 MUI、Mantine 等第二套设计系统。后端保持 FastAPI 模块化单体 + SQLite；不引入 ROS/RMF runtime、Docker、K8s 或大本地模型。

## D03｜机器人职责

**LOCKED**：Robot A 处理室外小垃圾；Robot B 处理液体/重污；Robot C 处理室内轻量干垃圾并可经 B1→电梯→B2→空中连廊→A2 跨楼；Robot D 只作配送扩展资产，不进入清洁 Scheduler。采用 Robot-first + Human Fallback；人工不是调度候选。

## D04｜确定性调度与 Agent 边界

**LOCKED**：Capability Engine + Scheduler 是唯一 Robot A/B/C 选择器，LLM 不得选择或控制机器人。Camera→SLAM、Route Planner、Scheduler、Verification、Heatmap 不是 Agent。仅保留 Multi-view Perception Agent 与 Optimization Agent；任何新 Agent 必须由用户确认。

## D05｜空间与地图

**LOCKED**：园区使用 6 张模拟 SLAM map、Global Spatial Graph、四点 Camera→SLAM 映射和确定性路由；白模为静态背景，动态信息使用 SVG/DOM，不引入 Three.js。客户地图主体只保留 A栋、B栋、1F、2F；目标用图形 Marker，不显示“清洁目标”、道路、电梯或连廊技术文字。

## D06｜客户信息架构与语言

**LOCKED**：一级导航固定为“自主清洁工作台、事件中心、运营分析、高级模式”。客户层只使用业务中文；YOLO/Qwen-VL/DashScope/Scheduler/JSON/raw 字段只在高级模式或技术详情显示。

## D07｜工作台布局和监控

**LOCKED**：工作台由左导航、中间主业务区（约 70–72%）和右侧独立滚动事件详情（约 28–30%）组成，尽量一屏。默认两路监控：左 Demo01 后图、右 Demo03 后图，均 `object-contain`。运行时：Demo01 左换前图；Demo02 左换 CAM-A1-01；Demo03 右换前图；Demo04 右换主摄像头；验收结束后恢复默认后图。

## D08｜受控边缘证据

**LOCKED**：Demo bbox/置信度是 `CONTROLLED_EDGE_DEMO`，不得说成真实 YOLO。数值固定为 Demo01 81%；Demo02 58/63/61%；Demo03 84%；Demo04 82%。bbox 比目标外扩约 8–12%，线宽约 1.5–2px；Demo02 三视角统一命名“液体污渍”。

## D09｜云端大模型与融合门控

**LOCKED**：面客称“云端大模型”。首次 `>=.85` 进入业务判断；`.50–.85` 必须独立二次复核；`<.50` 人工复核。二次提示不得携带首轮答案。系统综合处置评分与模型原始置信度分开，使用 D10 的公式；显式 `need_clean=false`、`unknown`、`ignore` 始终 veto 自动派发。

## D10｜Evidence Fusion Composite Disposal Score

**LOCKED**：`0.60 × 原始云端置信度 + 0.20 × YOLO类别一致性 + 0.12 × 摄像头/地点/时间映射一致性 + 0.08 × 多视角一致性`。禁止给 Qwen 置信度直接加固定百分点，也不得以融合覆盖模型 veto。

## D11｜Demo04 人工闭环

**LOCKED**：Demo04 必须遵循：大件纸箱 → 云端确认/人工边界 → 人工工单 → 模拟人工完成 → 同机位 after 图 → 真实云端验收 → PASS 后闭环。after 图仅删除两只纸箱，路径为 `sample_data/camera_events/CAM-A2-11/event-oversized-box-004/after.png`，已入 Git。

## D12｜运营数据和 AI 助手

**LOCKED**：运营数据来源是“30 天结构化演示历史基线 + 新运行 Demo 写入 SQLite 的实时增量”；KPI、热力、利用率由程序计算，模型不能编造数字。运营建议与两个 AI 助手若实现，必须是同一只读云端 Assistant 后端，只允许查询/分析/建议，不能创建任务、调机器人或改配置。

## SUPERSEDED 决策索引

以下历史决策不再有效，保留仅用于追溯：

| 历史主题 | 状态 | 由何替代 |
|---|---|---|
| 固定 Scenario 与真实 AI Lab 完全分离、Qwen 仅 secondary evidence | **SUPERSEDED** | D07–D10：受控证据可进入真实云端语义和既有调度链路；AI Lab 仍保留独立测试职责 |
| 旧 REAL/MOCK 把“稳定回放”作为客户菜单多行入口 | **SUPERSEDED** | D06、D07：客户演示菜单只保留四个场景；REAL/MOCK/回放仅在高级技术语义中明确 |
| 旧 YOLO 灰区阈值（0.55）及单次 Qwen `next_action=dispatch_robot` 是唯一门控 | **SUPERSEDED** | D09、D10：`.50–.85` 独立二次复核 + 融合分数，模型 veto 保留 |
| 三入口（工作台/工单中心/运营分析）或五入口技术后台 | **SUPERSEDED** | D06：四个一级页面 |
| 四宫格监控、仅上传入口、独立低保真 prototype 不 fetch | **SUPERSEDED** | D07：双监控、集成工作台与 SQLite 事件 |
| “Demo04 无 after 图且直接结束” | **SUPERSEDED** | D11：人工完成后真实云端验收闭环 |

## 当前未锁定项

- 真实生产 Camera→SLAM 数学、真实多机位时间同步、阈值标定、Scheduler 权重、设备遥测、真实机器人/电梯接口均未确认。
- UI 细节及 P0/P1 实现路线必须以 `TODO.md` 为准；不得把它们误写为已验收决策。
