# AI 自主清洁 Demo｜真实任务清单

> **状态：LOCKED · 2026-08-29**
> `[x]` 仅代表代码与技术验证已存在；`[ ]` 是已确认但尚未实现的 LOCKED TARGET。未经用户验收或代码/测试证据，禁止把 TODO 改为 IMPLEMENTED。

## 已实现基线（IMPLEMENTED，禁止回退）

- 阶段 REST Runtime、SQLite transition audit、Cloud/assign/verify 边界、旧 `/runs/*` 410。
- 受控 bbox、真实 Qwen transport、独立二审/Fusion、Demo02 三图首次 Prompt、Multi-view Agent 限制。
- Phase 2 空间基础、Phase 3 Capability/Scheduler、现有 topology 投影；当前地图已读取 assignment 决定激活机器人。
- Demo01、Demo02、Demo04 的既有真实运行记录；Demo03 本轮验收为 `HUMAN_REVIEW`，不能视为闭环成功。

## P1-A｜先完成真实数据闭环（依赖最低）

- [ ] **Camera→SLAM Runtime 接入**：`locate` 从主 bbox 计算接地点，调用 `map_pixel_to_slam()`，持久化 map/x/y/building/floor/zone；marker 只在定位后出现，客户/Advanced 各按锁定层级显示。
- [ ] **Dijkstra global topology planner / `plan_route()` Runtime 接入**：`start-navigation` 读取共享 Fleet 当前 map 与已定位 target map，调用 `plan_route()`，将真实 connector graph 转为可视 anchor path；删除 demo_id 固定路径。
- [ ] **Demo04 正确能力边界**：移除 cloud 阶段大件直接人工特判；完整运行 Cloud → Locate → Capability Engine → zero candidate → HUMAN_FALLBACK → 人工完成 → verify。
- [ ] **共享 Fleet 状态**：将机器人真实位置、电量、状态统一为同一读模型；任务终点保留，new demo/reset 才复位，所有后续模块读同一源。
- [ ] **Stable Replay 重定义**：只保存/选择既有真实 AI 结构化证据回放，其他 Runtime 阶段仍真实执行；本批可在现有 Advanced shell 增加最小 AI Runtime 控制区，提供 LIVE / Stable Replay 主动选择、云端模型可用状态、最近请求状态和最近 latency；不得重做完整 Advanced 页面，LIVE 永不 silent fallback。

## P1-B｜MapCanvas 与机器人执行视觉（依赖 P1-A）

- [ ] **唯一 MapCanvas**：构建 object-contain 内层画布坐标转换，白模、anchor、route、marker、机器人统一投影；修复 letterbox 漂移并重新校准 A/B/C/D 初始视觉位置/opacity。
- [ ] **连续路线移动**：对真实 anchor path 插值；未走/已走路线、少量箭头和小 marker 按锁定规格渲染；Robot C 电梯入口暂停约 1 秒、显示“乘梯中”、再从 B2F 出口继续。
- [ ] **任务终态视觉**：CLOSED/HUMAN_REVIEW 保留终点和已走路线；Demo04 无机器人移动；新增显式“重置演示”且只在此/新 Demo 清空临时地图状态。

## P1-C｜主工作台布局、监控与详情（可与 P1-B 部分并行）

- [ ] **布局收敛**：实现 72/28、31/69、右详情贴 Header 独立滚动、145–155px 资产栏、顶栏减法和相机 object-contain 宽度规范。
- [ ] **双监控状态矩阵**：落实四个 Demo 的 before/after 切换、关闭后默认 after 恢复、事件图固定采集时间、播放按钮改轻量事件状态；Demo02 补充图永不替换顶部监控。
- [ ] **事件详情时间与跟随**：用 SQLite transitions 的真实时间、运行 duration、真实 latency；保留完整历史，单一 smooth auto-follow，手动滚动暂停/恢复，CLOSED 停止强制滚动。
- [ ] **Multi-view 演示叙事**：只展示 A1-02/A1-04 等宽并排图与 camera/confidence；实现可见的四步 Agent 过程、轻量停顿和 fade-in，不重复 A1-01。
- [ ] **客户中文化与云端结果块**：全量 enum 中文化，字段层级清晰；raw 模型百分比、Fusion “N分”、系统决策分层显示；raw next_action 不出客户层。
- [ ] **能力匹配紧凑表**：三行候选比较 + 真实调度原因，Demo04 显示零候选；客户层不展示公式。

## P1-D｜Demo03 目标级验收与回归（依赖 P1-A/C）

- [ ] **ROI verification**：before/after 全图 + 原 bbox ROI + 原事件类型进入验收 Prompt；忽略机器人、人员、阴影、光照、无关变化。
- [ ] **独立 ROI 二审**：首次 retry/human review 主因属于非目标干扰时，独立复核且不输入首轮答案。
- [ ] **完整 LIVE/Replay 回归**：Demo01/03 各 LIVE 5 次至少 4 次正确闭环；Demo02 连续 5 次至少 4 次真实执行 Multi-view Agent workflow（使用受控多视角证据资产）后正确闭环；Demo04 LIVE 3 次全量正确人工闭环；四 Demo Stable Replay 各 3 次 100% 稳定。记录 raw confidence、二审、Fusion、system decision、robot、Dijkstra global topology planner / `plan_route()` route、verification、final、latency。

## 后续 Batch（非本批）

- [ ] Event Center 复用详情、筛选/字段/异常处理。
- [ ] Analytics 的完整 KPI/热力与真实只读运营建议。
- [ ] 统一只读 AI Assistant 及事实问答/禁止操作测试。

## 不在授权范围

- ROS 2、Nav2/Open-RMF runtime、Docker/K8s、Kafka/Redis/PostgreSQL、真实机器人/电梯/门禁、RAG、Planner Agent、VLA、预测/RL、真实本地 YOLO 主链路。
