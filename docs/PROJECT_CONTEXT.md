# PROJECT_CONTEXT.md

# AI 自主清洁 Demo｜项目长期上下文

> 本文档是项目长期记忆主文档。  
> 后续 Codex 开发时，如聊天上下文与本文档冲突，应优先检查 `DECISIONS.md` 中的最新决策，并以最后明确确认的方案为准。

---

# 1. 项目基本信息

## 1.1 项目名称

正式业务名称：

**基于固定摄像头边云模型协同识别联动机器人 AI 自主清洁闭环系统**

当前 Demo 工程名称：

**AI 自主清洁 Demo**

本地工程目录：

项目根目录

---

## 1.2 项目背景

传统清洁机器人通常依赖：

- 固定路线；
- 定时任务；
- 人工发现问题；
- 人工派单；
- 人工确认清洁效果。

其核心问题不是机器人本身不会移动，而是机器人缺少一个能够动态感知整个园区环境的“任务来源”。

本项目利用园区已有固定摄像头，对公共区域地面进行持续视觉感知，并将 AI 识别结果与机器人 SLAM 地图进行空间映射，使机器人能够根据真实环境事件动态接收任务。

最终形成：

**固定摄像头发现问题 → AI 研判 → 空间定位 → 机器人调度 → 自动清洁 → 固摄验收 → 数据闭环**

---

## 1.3 为什么做这个项目

该项目有两个背景。

### 真实项目背景

真实项目已经存在以下核心业务方向：

- 固定摄像头识别清洁事件；
- 边缘模型 + 云端模型协同；
- SLAM 地图；
- 摄像头画面与机器人二维地图的空间映射；
- 调用机器人执行清洁；
- 固定摄像头进行清洁后复核。

### PoC 背景

现有 V1 Demo 已经能够跑通：

- YOLO；
- Qwen-VL；
- 机器人模拟调度；
- 清洁后复核；
- Streamlit 页面。

但 V1 存在：

1. 前端过于简单；
2. 缺乏园区级空间调度；
3. 缺少异构机器人能力模型；
4. Agent 设计不足；
5. 缺少多摄像头联合研判；
6. 缺少运营数据持续优化；
7. 更像 AI API 串联 Demo，而不是完整 AI 解决方案。

因此 的目标不是简单增加功能，而是把项目升级成适合 **AI 解决方案专家岗位面试** 的完整 PoC。

---

# 2. 项目商业目标

价值优先级已经确认。

## 第一价值：降低保洁人工投入

通过：

- 自动发现；
- 自动研判；
- 机器人承担标准化地面清洁；
- 自动调度；
- 自动验收；

减少人工巡查和重复性清洁投入。

项目不强调“完全替代人工”。

目标是：

**尽可能提高机器人自主闭环任务比例，使人工只处理机器人能力边界外的复杂任务。**

---

## 第二价值：提高问题响应和闭环效率

传统：

人工巡查 → 发现垃圾 → 通知人员 → 人员处理 → 人工确认。

目标：

AI发现 → AI研判 → 自动定位 → 自动调度 → 自动清洁 → 自动验收。

---

## 长期增量价值：数据驱动运营优化

长期积累：

- 垃圾发生位置；
- 时间；
- 类型；
- 响应时间；
- 机器人任务；
- 清洁结果；

形成：

- 高发区域；
- 高发时段；
- 机器人利用率；
- 清洁效率；
- 热力图。

再由 Optimization Agent 提供运营优化建议。

方向由：

**Reactive Cleaning**

逐步升级到：

**Autonomous Cleaning**

再进一步升级到：

**Predictive Cleaning**

---

# 3. 主要目标用户

主要面向：

- 园区物业管理人员；
- 商业综合体运营管理人员；
- 写字楼物业；
- 园区保洁管理人员；
- 机器人运营管理人员；
- 数字化运营管理人员。

当前 Demo 主要用于：

**AI 解决方案专家岗位面试展示。**

---

# 4. 核心业务闭环

完整业务流程如下。

---

## 4.1 园区 SLAM 建图

真实业务中：

先由工作人员使用手持 SLAM 建图设备对园区进行人工扫描。

生成：

- 楼栋地图；
- 楼层地图；
- 室外区域地图。

地图随后经过编辑和适配，并导入机器人平台。

当前 园区结构：

### A 栋

- B1 地下停车场；
- 1F 大堂 / 公共区域；
- 2F 公共区域。

### B 栋

- 1F 大堂 / 公共区域；
- 2F 公共区域。

### 室外

- 园区道路；
- 公共广场；
- 楼栋外花岗岩区域。

A、B 两栋 2F 之间存在：

**Skybridge / 空中连廊**

两栋分别具有电梯系统。

---

# 5. 固定摄像头与 SLAM 地图标定

每个固定摄像头需要进行空间标定。

核心方式：

1. 在固定摄像头画面中选取 4 个固定关键点；
2. 找到这 4 个点在机器人 SLAM 二维地图中的对应位置；
3. 建立摄像头视觉空间与机器人二维地图之间的映射；
4. 后续摄像头识别到垃圾后，根据垃圾在画面中的位置推算机器人可使用的 SLAM 坐标。

数据关系：

`Camera Image Coordinate (u,v)`

↓

`4-point Mapping`

↓

`SLAM Coordinate (x,y)`

↓

`Building / Floor / Zone`

↓

`Robot Navigation Goal`

注意：

真实项目已经确认采用“四点绑定建立空间映射”的业务方式。

真实生产系统底层具体采用何种数学算法尚未明确，不应虚构。

PoC 可以实现稳定、可重复计算的二维四点映射。

---

# 6. AI 感知流程

## 6.1 边缘侧初筛

固定摄像头视频首先经过边缘视觉模型。

当前技术路线：

**Ultralytics YOLO**

V1 已实际使用：

`YOLO26n`

主要输出：

- class；
- bbox；
- confidence；
- camera_id；
- timestamp。

V1 曾使用候选类别：

- bottle；
- cup；
- handbag。

后续会扩展业务语义，不应局限于上述类别。

---

## 6.2 云端 VLM 二次研判

边缘检测产生疑似事件后，将关键帧上传云端多模态模型。

当前模型：

**Qwen-VL / 阿里云百炼**

主要判断：

- 是否真的需要清洁；
- 物体 / 污染类型；
- 污染形态；
- 大小；
- 地面材质；
- 污染程度；
- 清洁能力要求。

例如：

奶茶打翻：

- pollution_form = liquid
- severity = high
- surface = tile
- required = wet_cleaning + strong_suction + scrubbing

---

# 7. 多视角 Perception Agent

这是当前 设计中第一个真正意义上的 Agent。

目标：

**解决单固定摄像头因为遮挡、反光、距离、小目标等原因产生的不确定视觉判断。**

正常高置信度事件：

不调用 Agent。

低置信度灰区事件：

触发 Multi-view Perception Agent。

流程：

事件初步位置

↓

查询 Camera Coverage

↓

判断哪些其他摄像头能够覆盖同一区域

↓

Agent 选择有效摄像头

↓

获取近同步画面

↓

调用 VLM 综合研判

↓

输出：

- CONFIRM
- REJECT
- HUMAN_REVIEW

Agent 可使用：

- Camera Coverage Tool
- Frame Fetch Tool
- VLM Tool

禁止输出 Chain-of-Thought。

只允许前端显示：

- Tool Call；
- Evidence；
- Selected Cameras；
- Final Confidence；
- Decision。

---

# 8. Cleaning Task Profile

事件确认后，不直接调用机器人。

系统需要把视觉结果转换成业务任务：

**Cleaning Task Profile**

主要字段：

- object_type；
- pollution_form；
- severity；
- estimated_area；
- surface；
- required_capabilities；
- priority；
- building；
- floor；
- zone；
- SLAM x/y。

这是连接：

**视觉 AI**

与

**机器人任务编排**

之间的重要中间层。

---

# 9. 机器人体系

当前系统规划 4 类机器人。

其中 3 类参与当前 Demo。

---

## 9.1 Robot A｜Outdoor Sweeper

定位：

室外清扫机器人。

主要负责：

- 园区道路；
- 公共广场；
- 楼栋外围花岗岩地面；
- 室外普通小型垃圾。

约束：

- 不进入楼栋；
- 不乘电梯；
- 不通过 Skybridge。

---

## 9.2 Robot B｜Heavy Scrubber

定位：

重度清洁 / 重度洗地机器人。

主要能力：

- 强吸水；
- 强吸力；
- 强刷洗；
- 拖洗；
- 重污染处理。

典型场景：

- 奶茶打翻；
- 大面积水渍；
- 黏性液体；
- 较难清洗污渍；
- 停车场；
- 环氧地坪；
- 硬质瓷砖。

特点：

- 体型较大；
- 噪声相对高；
- 公共区域体验较弱；
- 可乘电梯。

真实项目中主要配置于 A 栋。

---

## 9.3 Robot C｜Indoor Light Cleaner

定位：

室内轻量日常清洁机器人。

主要能力：

- 纸屑；
- 纸杯；
- 易拉罐；
- 小型塑料瓶；
- 灰尘；
- 少量干垃圾；
- 地毯；
- 瓷砖。

特点：

- 体积小；
- 噪声低；
- 更适合客户可见公共区域；
- 更适合日常高频轻清洁；
- 可乘电梯；
- 可通过空中连廊跨楼栋。

真实项目中主要配置于 B 栋。

设计允许 Robot C：

B 栋

→ 电梯

→ B栋2F

→ Skybridge

→ A栋2F

→ 电梯

→ A栋其他楼层。

---

## 9.4 Robot D｜Delivery Robot

新增配送机器人。

当前仅作为未来平台扩展资源存在。

现阶段：

- 纳入机器人类型概念；
- 不定义具体产品能力；
- 不参与清洁调度；
- 不设计配送 Workflow；
- 不在当前 Demo Scenario 中演示。

其目的只是为后续园区机器人统一编排能力预留扩展空间。

---

# 10. Robot-first + Human Fallback

当前方案明确采用：

**Robot-first**

而不是：

**Human vs Robot 同池竞争**

规则：

只要存在能够安全有效完成任务的机器人，就优先由机器人自主执行。

人工保洁只在以下情况介入：

1. 机器人能力无法覆盖；
2. 大型纸箱；
3. 大垃圾袋；
4. 大件杂物；
5. 需要人工拾取；
6. 机器人不可达；
7. 多次自动清洁失败。

人工不是 Scheduler 的普通候选资源。

人工属于：

**Fallback / Exception Handling**

---

# 11. Capability Engine

调度前首先进行硬约束过滤。

考虑：

- indoor / outdoor；
- surface；
- pollution type；
- required capability；
- elevator；
- skybridge；
- accessibility；
- battery；
- robot state。

如候选机器人数量为：

`0`

则：

`HUMAN_FALLBACK`

如：

`1`

则可直接选择。

如：

`>1`

进入 Scheduler Soft Score。

---

# 12. Scheduler

正常机器人调度不是 Agent。

采用：

**Constraint + Scoring + Workflow**

主要评分因素：

| 因素 | Demo 初始权重 |
|---|---:|
| Task Capability Fit | 25 |
| ETA / Distance | 25 |
| Battery | 15 |
| Current Workload | 10 |
| Zone Fitness | 10 |
| Floor / Elevator Cost | 5 |
| Cross-building Cost | 5 |
| Noise / Public-space Fitness | 5 |

权重必须配置化。

不得把这些 Demo 权重描述为真实生产参数。

真实客户项目需重新标定。

---

# 13. Global Spatial Graph

园区不是单张地图。

当前设计：

- OUTDOOR
- A_B1
- A_1F
- A_2F
- B_1F
- B_2F

跨地图依靠：

- Elevator Connector；
- Skybridge Connector；
- Entrance / Exit；
- Map Connector。

例如 Robot C：

B栋1F

→ B栋电梯

→ B栋2F

→ Skybridge

→ A栋2F

→ A栋电梯

→ A栋1F

→ Target。

Global Route 使用：

- Dijkstra
或
- A*

不使用 LLM 进行确定性路径规划。

---

# 14. 清洁执行与验收

机器人执行：

ASSIGNED

↓

NAVIGATING

↓

ARRIVED

↓

CLEANING

↓

VERIFYING

机器人返回 Completed：

**不能直接关闭事件。**

必须重新调用固定摄像头进行清洁后复核。

判断：

- remaining_pollution；
- confidence；
- PASS / FAIL。

PASS：

关闭事件。

FAIL：

可进入 Retry。

如果再次失败：

重新生成 / 更新 Task Profile

↓

Capability Check

↓

可能更换更强机器人。

仍无法完成：

Human Fallback。

---

# 15. 数据沉淀与 Optimization Agent

系统长期保存：

- timestamp；
- building；
- floor；
- zone；
- SLAM x/y；
- object_type；
- pollution_type；
- robot_id；
- response_time；
- closure_time；
- verification；
- human_intervention。

Analytics Engine 负责：

- Spatial Heatmap；
- Time Distribution；
- Robot Utilization；
- Autonomous Closure Rate；
- Human Intervention Rate；
- First-pass Success Rate；
- Average Response Time；
- Average Closure Time；
- Multi-view Recovery Rate。

注意：

**热力图不是 Agent。**

数据统计不是 Agent。

Optimization Agent 只负责：

读取已经计算的数据

↓

解释异常和趋势

↓

生成运营策略建议。

例如：

A栋1F东入口 17:30–19:00 高频出现垃圾

+

同期 Robot C 空闲率较高

↓

建议调整 Robot C 待机点或主动巡检时间。

当前不建议直接用热力图修改 CV 模型识别置信度，以避免数据反馈偏差。

---

# 16. Agent / Workflow 边界

当前项目核心原则：

> 确定性问题使用 Workflow / Algorithm；  
> 不确定性问题才使用 Agent。

当前 MVP 真正保留两个 Agent：

## Agent 1

Multi-view Perception Agent

解决：

视觉证据不充分。

## Agent 2

Cleaning Optimization Agent

解决：

历史运营数据如何转化成优化策略。

Planner Agent：

只预留。

暂不作为 MVP 必做内容。

以下均不是 Agent：

- YOLO；
- Qwen-VL；
- Spatial Engine；
- Camera → SLAM Mapping；
- Capability Engine；
- Scheduler；
- Route Planner；
- Elevator Connector；
- Robot Adapter；
- Verification；
- Heatmap；
- State Machine。

---

# 17. Demo 状态机

主要状态：

- DETECTED
- JUDGING
- MULTI_VIEW
- CONFIRMED
- REJECTED
- LOCATING
- PROFILING
- CAPABILITY_CHECK
- SCHEDULING
- ASSIGNED
- NAVIGATING
- WAITING_ELEVATOR
- IN_ELEVATOR
- SKYBRIDGE
- ARRIVED
- CLEANING
- VERIFYING
- RETRY
- HUMAN_FALLBACK
- CLOSED
- FAILED

每一次状态变化：

- 写入数据库；
- 通过 SSE 推送前端。

超时机制目前尚未最终确认。

---

# 18. Demo AI 置信度 Policy

当前仅作为 Demo 初始配置：

## 初次判断

`>= 0.85`

直接确认。

`0.55 <= confidence < 0.85`

触发 Multi-view。

`< 0.55`

Reject 或 Human Review。

## Multi-view 后

`>= 0.85`

Confirm。

`0.60–0.85`

Human Review。

`< 0.60`

Reject。

以上参数必须配置化。

不是生产项目最终参数。

---

# 19. 系统技术架构

## 前端

当前已经确认：

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Apache ECharts

React Flow：

仅在后续 Workflow / Decision Graph 真有必要时使用。

当前不强制。

禁止混入第二套 UI Design System，例如：

- MUI
- Mantine

UI 目标：

- 简洁；
- 克制；
- 企业级 SaaS；
- Fleet Management；
- Digital Operations；
- 少 AI 味；
- 不做霓虹科技大屏；
- 不做大量玻璃拟态；
- 不做无意义渐变；
- 不做夸张圆角；
- 地图是主视觉区域。

---

## 后端

- Python
- FastAPI
- SQLite
- SSE

---

## AI

### V1 已跑通

- Ultralytics YOLO
- YOLO26n
- Qwen-VL
- Alibaba Cloud DashScope / 百炼

### 计划

- 复用 V1 AI 能力；
- REAL MODE；
- MOCK MODE。

LangGraph：

计划只用于：

- Multi-view Perception Agent；
- Optimization Agent。

当前尚未实施。

---

# 20. AI Lab

最终需要保留独立：

**AI Lab / Live Test**

用于：

- 上传图片；
- 上传 MP4；
- YOLO；
- 关键帧；
- Qwen-VL；
- 输出结构化结果；
- Task Profile。

Scenario：

负责稳定面试演示。

AI Lab：

负责证明真实 AI 模型确实可以运行。

如果 API Key 存在：

REAL MODE。

不存在：

MOCK MODE。

必须明确展示当前模式。

---

# 21. 当前固定 Demo Scenario

## Scenario 01

Outdoor Autonomous

室外普通垃圾

→ Robot A

→ Outdoor Route

→ Clean

→ Verify

→ Closed。

## Scenario 02

Multi-view Heavy Cleaning

A栋1F疑似奶茶污渍

→ 初始低置信度

→ Multi-view Agent

→ Camera Coverage

→ VLM Confirm

→ Robot B

→ Heavy Cleaning。

## Scenario 03

Cross-building Orchestration

A栋1F普通轻垃圾

Robot C 位于 B栋

→ Scheduler

→ B栋电梯

→ B栋2F

→ Skybridge

→ A栋2F

→ A栋电梯

→ A栋1F

→ Target。

## Scenario 04

Robot Capability Boundary

大型纸箱 / 大垃圾袋

→ 所有 Robot Capability 不满足

→ Human Fallback

→ 人工工单。

Robot D 不参与上述 Scenario。

---

# 22. 当前代码状态

## V1

曾经已经跑通：

- YOLO26n；
- Qwen-VL；
- 视频关键帧；
- robot_dispatch；
- 清洁后复核；
- Streamlit；
- JSON 闭环结果。

V1 代码并未被当前 Codex 工作区自动发现。

Phase 4 已不等待该代码而完成可替换适配器实现；日后找到 V1 时仅作为模型权重、Prompt 或实现对照。

---

## Phase 1

已完成并人工验收。

当前目录：

项目根目录

已经实现：

- FastAPI；
- SQLite；
- React；
- TypeScript；
- Vite；
- Tailwind；
- shadcn/ui；
- Dashboard；
- 3 台清洁机器人基础数据；
- 园区基础信息；
- DEMO MOCK MODE；
- `/api/health`；
- `/api/dashboard`；
- 前端离线 Mock fallback。

ECharts 已纳入依赖，但 Phase 1 尚未正式使用。

---

# 23. Phase 1 已出现并解决的问题

曾出现：

打开前端为白屏 / 页面无法正常加载。

根因：

- 前端使用 `127.0.0.1:5173`；
- 后端 CORS 最初只允许 `localhost:5173`；
- API 请求失败；
- 前端缺少完整 fallback。

已解决：

1. FastAPI CORS 同时允许：
   - localhost:5173
   - 127.0.0.1:5173

2. Vite 增加 `/api` 代理；

3. 前端默认使用相对 `/api`；

4. 后端不可用时 Dashboard 仍使用稳定内置 Mock；

5. 页面显示后端离线提示，而不是白屏。

---

# 24. 当前代码状态更新

**Phase 2｜Spatial Engine 已完成，并通过本地单元测试与前端生产构建验证。**

已实现：

- 一键启动 / 停止脚本；
- 6 张二维 SLAM Map；
- Spatial Data Model；
- Global Spatial Graph；
- Elevator；
- Skybridge；
- Camera Coverage；
- Camera → SLAM 四点映射；
- Dijkstra / A*；
- 跨楼层 / 跨楼栋路线。

已验证：

- Robot B：A-2F → A-B1；
- Robot C：B-1F → A-1F；
- Camera Pixel → SLAM 重复调用结果稳定；
- 前端 TypeScript / Vite 生产构建通过。

Phase 3｜Workflow + Scheduler 已完成。实现严格使用 Mock AI、确定性业务规则与 Mock 设备接口；通过自动化测试、REST/SSE API 与浏览器页面验证。

新增能力：

- Cleaning Event、Task Profile、Assignment Candidate / Decision、Navigation Plan、Verification Result 与 Human Fallback Work Order；
- SQLite 持久化事件与全部状态迁移；
- 可解释 Hard Constraint + Soft Score，评分权重仅为 PoC Demo 配置；
- Mock Robot Adapter、Mock Verification 与 SSE 状态流；
- Dashboard 可运行稳定 Mock 事件、展示 Decision Trace 及 `Why Robot X?`。

Phase 4 已正式验收通过：未等待 V1 代码，采用与业务工作流解耦的适配器实现 YOLO、Qwen-VL、AI Lab 及 `ai-lab.v1` 结果到 Phase 3 的非持久化预检。当前限制：**REAL MODE 尚未使用真实 YOLO 权重和 Qwen-VL Key 完成实跑验证**。

Phase 5 已验收完成：仅灰区事件触发 LangGraph Multi-view Perception Agent；它复用 Phase 2 Camera Coverage / Spatial 数据，工具面限定为 Camera Coverage、Frame Fetch、VLM，最多 2 个额外摄像头和 2 次 iteration。Scenario 02（A 栋 1F 疑似奶茶污渍）从 0.67 提升至 0.92，输出 `CONFIRM` 后交回原有 Capability Engine / Scheduler，选择 Robot B；前端仅公开 Tool Calls、Evidence、Selected Cameras、Final Confidence 与 Decision。

---

# 25. 开发阶段规划

## Phase 1

工程骨架。

已完成。

## Phase 2

Spatial Engine。

已完成。

## Phase 3

Workflow + Scheduler。

已完成，全部使用稳定 Mock AI。

## Phase 4

未依赖 V1 源码重建：可选 Ultralytics YOLO 本地适配器、DashScope Qwen-VL JSON 适配器、三关键帧 MP4 策略、独立 AI Lab 与明确 REAL / MOCK 模式。固定 Scenario 不调用该实时链路。

## Phase 5

已完成并验收。严格只在置信度灰区运行；不修改 Phase 3 Scheduler、Capability Engine 或 Robot-first + Human Fallback。

## Phase 6

已完成并验收。Analytics Engine 使用 30 天 / 300 条可复现 Mock 运营记录，输出 Spatial Heatmap、时段分布、热点、机器人利用率及 6 项运营 KPI。Optimization Agent 只读取 Heatmap、Robot Utilization、Task History，生成待机点、主动巡检与资源配置建议；它不改写视觉置信度、Capability Engine、Scheduler 或 Robot-first + Human Fallback，建议必须人工确认后才可成为运营配置。

## Phase 7

已完成并验收。五个一级入口均可用；AI Event Center 可启动 4 个稳定 Scenario；Workflow 结果提供明确标注为 Mock 的 Robot / Elevator / Skybridge 状态回放、Camera → SLAM、Decision Trace、Why Robot X? 与 Before / After 验收摘要。该阶段只做呈现和讲解体验，不改变既有业务规则或声称真实设备遥测。

## Phase 8

客户演示工作台产品化层已完成：默认进入中文业务工作台，而非技术 Dashboard。按“发现现场问题 → AI 研判 → 空间定位 → 机器人调度 → 执行清洁 → 固定摄像头验收 → 任务闭环”组织信息。它只编排既有 Phase 4 `ai-lab.v1`、Phase 5 Multi-view、Phase 2 `map_pixel_to_slam`、Phase 3 Scheduler / Verification；不会新建 AI、坐标或调度实现。

已接入四组经授权素材，均存放在 `sample_data/camera_events/<camera>/<event>/`，metadata 只描述摄像头、事件与视角关系。清洁前原图以 SHA-256 精确匹配受控场景：室外纸巾 → Robot A；三机位奶茶液污 → Multi-view CONFIRM → Robot B；二楼易拉罐 → Robot C（电梯 + Skybridge 路线）；走廊大型纸箱 → `HUMAN_FALLBACK`。后者没有清洁后图，因此仅展示已创建的人工工单和“等待回传验收”，严禁伪造通过图。受控匹配是 `DEMO MOCK MODE` 的稳定演示适配；生产任意上传仍需后续 REAL AI 实跑验证。

### Phase 8 指挥台修复（已完成）

客户首屏已调整为“任务指挥台”，而不是以图片上传为中心的单工单播放器。`backend/operations/service.py` 作为唯一的 `operations.v1` 读模型，投影现有 Workflow 审计、Phase 2 机器人空间位置和四场景素材结果；它不会新建或修改 AI、Camera → SLAM、Capability Engine、Scheduler、Route Planner 或 Workflow。前端常驻展示 A/B/C 模拟位置、状态、电量、活动、工单队列、地图、任务详情和审计；场景 / 上传只负责新建演示工单。`DEMO_PLAYBACK` 是透明的模拟回放标识，绝不表示真实设备遥测。

## Phase 8R｜产品化重构 + Scenario 02 REAL AI 闭环

Phase 8R 将客户默认体验收敛为三层信息架构：一级仅保留“自主清洁工作台、工单中心、运营分析”；高级模式保留 Phase 1–7 的技术后台、AI Lab、原始审计与调度解释。`CleaningEvent / Work Order` 是产品核心，Scenario 仅用于快速创建工单。本轮客户默认只产品化 Scenario 02（A 栋 1F 大堂液体污渍 → Robot B）；Scenario 01 / 03 / 04 保留现有技术能力，不继续扩展产品界面，等待该场景验收。

客户业务分类固定为 `liquid`、`can`、`leaf`、`large_object`、`small_litter`。它们与原始 YOLO 类别分离：`BusinessDetection` 同时保存业务类、置信度来源、原始 YOLO 类和 VLM 类；通用 YOLO 没有稳定证据时，不得伪造液体、树叶或大件的 YOLO 框。Camera → SLAM 仍只调用 `spatial.calibration.map_pixel_to_slam`；Scheduler 与 Heatmap 均不是 Agent；机器人、电梯、Skybridge 仍为后端驱动的 Simulation。

REAL AI 接入边界已补齐：根目录 `.env.example` 描述本地 YOLO 权重与 DashScope Key，配置由本地 `.env` 自动读取且被 Git 忽略；`GET /api/system/ai-status` 只报告无密钥的运行状态。当前机器未配置 `.env`、YOLO 权重和 `DASHSCOPE_API_KEY`，因此 **Scenario 02 REAL YOLO + Qwen-VL + post-clean verification 的实跑验收尚未完成**；默认只明确运行 MOCK，不能写成 REAL 通过。

---

# 26. 开源项目参考

后续 Codex 开发时重点参考：

## Navigation2

https://github.com/ros-navigation/navigation2

参考：

- Navigation；
- Path Planning；
- Map Navigation；
- Robot Navigation Architecture。

## Open-RMF

https://github.com/open-rmf/rmf

参考：

- Multi-fleet；
- Task Allocation；
- Lift / Door；
- Building Infrastructure；
- Heterogeneous Robots。

## Open-RMF Demos

https://github.com/open-rmf/rmf_demos

参考：

- 多机器人 Demo；
- 电梯；
- 跨楼层；
- Fleet；
- Map；
- Simulation。

原则：

**参考，不等于直接集成。**

当前 禁止为了使用这些项目而强行引入：

- ROS 2；
- Nav2 Runtime；
- Open-RMF Runtime。

如后期确有明显复用价值，Codex 可先提出方案，经确认后再 Fork 或复用。

---

# 27. UI / UX 参考原则

当前确认：

组件底座：

**shadcn/ui + Tailwind CSS**

数据图表：

**Apache ECharts**

可选：

**React Flow**

仅在决策流程 / 图关系确有必要时使用。

可参考：

**Ant Design Pro**

的信息架构，但不要直接照搬其视觉风格。

UI 强调：

- 简约；
- 高级；
- 信息密度合理；
- 企业运营平台；
- Linear / Vercel / 企业 SaaS 式克制感；
- 不做传统蓝色科技驾驶舱；
- 不做明显 AI Generated Dashboard。

---

# 28. 开发环境与约束

用户设备：

- MacBook Air M1（2020）
- 8GB RAM
- ARM64
- 剩余磁盘空间历史约 20GB

工具：

- Cursor
- Git
- Python
- Codex

历史 Python：

`3.14.7`

当前 后端使用：

`.venv`

用户不希望主动安装：

- Docker Desktop
- Kubernetes
- 大型本地模型
- ROS 2
- 复杂基础设施

原因：

- 机器资源有限；
- 面试 Demo 不需要过度工程化。

模型优先调用云端 API。

---

# 29. 项目工程原则

1. 不为了 Agent 而 Agent。
2. 确定性问题使用规则 / 算法 / Workflow。
3. LLM 不直接控制机器人。
4. 所有机器人调度必须可解释。
5. Mock 硬件，但接口设计要符合真实工程。
6. Demo 稳定优先于技术堆叠。
7. REAL MODE 失败时 Scenario 仍必须可演示。
8. 每个 Phase 完成后停止，人工验收后才能进入下一阶段。
9. 不允许 Codex 无授权提前实施后续 Phase。
10. README 与项目记忆文档必须随阶段更新。

---

# 30. 当前已知风险

1. V1 AI 代码尚未迁入。
2. Phase 2 仅使用模拟 SLAM 地图，且当前只有 CAM-A1-01 配置四点标定。
3. Camera → SLAM 真实生产底层数学实现细节尚未明确。
4. Demo Scheduler 权重已配置化，但尚未经过真实数据标定。
5. Demo AI Confidence 阈值尚未经过验证集标定。
6. 电梯 / Skybridge 当前均为 Mock。
7. Human Fallback 当前仅规划为模拟工单。
8. Optimization Agent 当前使用稳定 Mock 长期运营数据，尚未接入真实长期运营数据。
9. 多摄像头帧时间同步机制尚未最终确定。
10. Robot B / C 能力参数目前主要作为 PoC Capability Profile，不应宣传成某真实厂商准确参数。
11. Robot D 目前只有类型定义，不应扩展产品能力。

## 31. Custom YOLO Demo Training（独立前置任务，已完成但未接入）

Phase 8R 的完整 REAL 验收已暂停，未进入新 Phase。本轮只以用户提供的 9 张照片训练固定五类 `liquid / can / leaf / large_object / small_litter` 的 Demo-specific Custom YOLO。有效正样本仅 8 个，`leaf` 没有合法正样本，所有类别均为 LOW DATA。训练、中文 bbox review、逐张推理及 3 组清洁后负样本测试已完成，详见 `docs/YOLO_DATASET_REPORT.md`。

结果只在 0.25 阈值稳定检出 Demo 4 两只 `large_object` 纸箱；`liquid`、`can`、`small_litter` 清洁前图均漏检，`leaf` 不可评估。因此权重仅保存在本地 `models/ai_cleaning_custom_yolo/best.pt`，不提交 Git，**不得**接入 Phase 8R 或声称 REAL 验收通过。MPS 已优先尝试但本机组合报错后回退 CPU；未改动产品 UI、Scheduler、SLAM 或 Agent。
