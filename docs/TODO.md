# TODO.md

# AI 自主清洁 Demo｜任务清单

---

# 一、已完成

## Phase 1｜工程骨架

- [x] 创建 项目根目录 独立工程
- [x] FastAPI 后端
- [x] SQLite 初始化
- [x] `/api/health`
- [x] `/api/dashboard`
- [x] React + TypeScript + Vite
- [x] Tailwind CSS
- [x] shadcn/ui
- [x] 引入 Apache ECharts
- [x] 建立运营 Dashboard
- [x] 展示园区基础信息
- [x] 展示 Robot A/B/C 基础状态
- [x] 显示 `DEMO MOCK MODE`
- [x] 为后端不可用情况增加前端 Mock fallback
- [x] 修复 localhost / 127.0.0.1 CORS 问题
- [x] Vite `/api` 本地代理
- [x] 页面 API 失败时仍能正常渲染

---

## Phase 2｜Spatial Engine

- [x] 一键启动 / 停止脚本，以及端口复用保护
- [x] 6 张模拟 SLAM Map：OUTDOOR、A_B1、A_1F、A_2F、B_1F、B_2F
- [x] 可通行区域、障碍、Zone、Camera、Robot、Elevator、Entrance / Exit 与 Navigation Node 数据
- [x] Global Spatial Graph：Floor / Zone / Elevator / Skybridge / Map Connector
- [x] Dijkstra Local / Global Route
- [x] Camera 数据模型、Coverage Polygon 与邻接摄像头
- [x] CAM-A1-01 四点标定、Pixel(u,v) → SLAM(x,y) 与 Building/Floor/Zone 输出
- [x] 前端空间地图、路径与标定映射展示
- [x] 验收：A-2F → A-B1、B-1F → A-1F、重复映射稳定性

---

# 二、已完成

## Phase 3｜Workflow + Scheduler

暂时全部使用 Mock AI。

- [x] CleaningEvent 数据结构
- [x] TaskProfile
- [x] RobotCapability
- [x] RobotState
- [x] AssignmentCandidate
- [x] AssignmentDecision
- [x] NavigationPlan
- [x] VerificationResult
- [x] HumanFallbackWorkOrder

### Capability Engine

- [x] indoor / outdoor
- [x] surface
- [x] pollution type
- [x] required capability
- [x] elevator
- [x] skybridge
- [x] accessibility
- [x] battery
- [x] robot state

### Scheduler

- [x] Hard Constraint Filtering
- [x] Soft Score
- [x] 权重配置文件
- [x] 候选机器人评分
- [x] Reject Reason
- [x] `Why Robot X?` 决策数据

### Workflow State Machine

- [x] DETECTED
- [x] JUDGING
- [x] MULTI_VIEW
- [x] CONFIRMED
- [x] REJECTED
- [x] LOCATING
- [x] PROFILING
- [x] CAPABILITY_CHECK
- [x] SCHEDULING
- [x] ASSIGNED
- [x] NAVIGATING
- [x] WAITING_ELEVATOR
- [x] IN_ELEVATOR
- [x] SKYBRIDGE
- [x] ARRIVED
- [x] CLEANING
- [x] VERIFYING
- [x] RETRY
- [x] HUMAN_FALLBACK
- [x] CLOSED
- [x] FAILED

### 运行机制

- [x] 每次状态变更保存 SQLite
- [x] SSE 推送前端
- [x] Mock Robot Adapter
- [x] Mock Verification
- [x] Human Fallback

---

# 三、当前最高优先级

## Phase 5｜Multi-view Perception Agent（已验收）

Phase 4 已正式验收通过。当前限制：**REAL MODE 尚未使用真实 YOLO 权重和 Qwen-VL Key 完成实跑验证**。

---

# 四、后续 Phase 详细清单

## Phase 4｜YOLO + Qwen-VL + AI Lab

- [x] 在未找到 V1 代码时，以适配器重建 YOLO / Qwen-VL 集成边界
- [x] 可选 Ultralytics YOLO26n 本地权重适配器
- [x] DashScope Qwen-VL OpenAI-compatible JSON 适配器
- [x] MP4 首 / 中 / 尾关键帧逻辑
- [x] `REAL AI MODE` 运行条件解析与明确错误返回
- [x] `DEMO MOCK MODE` 稳定降级
- [x] 独立 AI Lab 页面
- [x] 图片上传（JPG / JPEG / PNG / WEBP）
- [x] MP4 上传（20 MB 上限）
- [x] VLM JSON 与 Task Profile 展示
- [x] 保持 AI Lab 与固定 Scenario / 调度执行分离
- [x] `ai-lab.v1` REAL / MOCK 统一 Schema 与 `need_clean` 字段
- [x] AI结果 → Phase 3 CleaningEvent / TaskProfile 兼容测试
- [x] 4 个业务输入经原 Capability Engine / Scheduler 预检
- [x] AI Lab 与 Phase 2 共用 `map_pixel_to_slam`，并补齐 `map_id`
- [x] 用户最终验收确认，可进入 Phase 5
- [ ] 使用真实 YOLO 权重和 Qwen-VL Key 完成 REAL MODE 实跑验证

---

## Phase 5｜Multi-view Perception Agent

- [x] 接入 LangGraph
- [x] Camera Coverage Tool（复用 Phase 2 `CAMERAS` Coverage 数据）
- [x] Frame Fetch Tool
- [x] VLM Tool
- [x] Agent Camera Selection
- [x] Max Additional Cameras = 2
- [x] Max Agent Iterations = 2
- [x] CONFIRM
- [x] REJECT
- [x] HUMAN_REVIEW
- [x] Decision Trace
- [x] 不显示 Chain-of-Thought
- [x] Scenario 02：低置信度奶茶污渍 → Multi-view CONFIRM → 原 Scheduler 选择 Robot B

---

## Phase 6｜Analytics + Optimization

- [x] 生成 30 天模拟历史数据
- [x] Spatial Heatmap
- [x] Time Distribution
- [x] Top Hotspots
- [x] Robot Utilization
- [x] Autonomous Closure Rate
- [x] Human Intervention Rate
- [x] First-pass Success Rate
- [x] Average Response Time
- [x] Average Closure Time
- [x] Multi-view Recovery Rate

### Optimization Agent

- [x] Heatmap Tool
- [x] Robot Utilization Tool
- [x] Task History Tool
- [x] Generate Optimization
- [x] 待机点优化建议
- [x] 主动巡检频率建议
- [x] 资源配置建议
- [x] Phase 6 已验收，可进入 Phase 7

---

## Phase 7｜Interview UX

- [x] Operations Dashboard
- [x] AI Event Center
- [x] Robot Orchestration
- [x] Optimization Center
- [x] AI Lab
- [x] Scenario Launcher
- [x] Robot Animation（Mock 状态回放）
- [x] Elevator Animation（Mock 状态回放）
- [x] Skybridge Animation（Mock 状态回放）
- [x] Camera → SLAM Animation
- [x] Decision Trace
- [x] Why Robot X
- [x] Before / After
- [x] Heatmap
- [x] KPI

---

## Phase 8｜客户演示工作台产品化

- [x] 默认首页重构为自主清洁任务工作台，原 Phase 1–7 页面移至技术后台 / AI 能力验证
- [x] Scenario 02 三栏业务流：现场、空间执行、当前任务
- [x] 复用 `ai-lab.v1`、Multi-view Agent、`map_pixel_to_slam`、Scheduler、Verification
- [x] Camera + Event + View 的 `sample_data/camera_events` 素材目录与 metadata 契约
- [x] 三视角证据、空间映射、Robot B 路线动画、清洁、固定摄像头验收、闭环 UI
- [x] 技术详情按第二层 / 第三层收纳，不显示 Chain-of-Thought
- [x] 浏览器验收 Scenario 02 的完整 Mock 流程
- [x] 入库 4 组经授权现场演示素材（共 9 张 PNG），保持 Camera + Event + View 契约
- [x] 四个 Scenario 的素材化工作台：Robot A、B 多视角、C 跨楼栋、Human Fallback
- [x] 上传清洁前原图后 SHA-256 匹配受控场景并自动运行完整业务流
- [x] 展示 AI 研判、Camera → SLAM、Capability / Scheduler、路径、状态审计、Before / After 验收
- [x] Scenario 04 明确展示人工工单与待回传验收，不伪造清洁后照片
- [x] 素材化工作台 API、后端测试、前端构建与浏览器验收
- [x] 修复旧 FastAPI 服务被复用导致 `/api/workbench/*` 404、前端只显示 `Not Found` 的启动兼容性问题
- [x] 客户首屏改为运营指挥台：A/B/C 位置、状态、电量、活动、工单队列、SLAM 任务图、任务详情与审计常驻可见
- [x] 新增 `operations.v1` 服务端 `DEMO_PLAYBACK` 读模型；不新增 Scheduler / 状态机 / 坐标映射，不以前端定时器伪造业务状态
- [x] 离线 / 接口异常时保留完整指挥台框架和明确启动提示，不白屏
- [x] 验收 `operations.v1`、四场景创建、受控图片上传匹配、26 个后端单元测试、前端生产构建与浏览器交互

---

## Phase 8R｜客户产品化 + Scenario 02 REAL AI 闭环

- [x] 一级信息架构收敛为：自主清洁工作台、工单中心、运营分析；Phase 1–7 调试功能保留在高级模式
- [x] CleaningEvent / Work Order 作为产品主对象；新增持久化工单列表读接口
- [x] 默认工作台仅提供 Scenario 02 的快速创建入口；Scenario 01 / 03 / 04 暂停产品化扩展
- [x] 摄像头优先、执行时转 SLAM、验收时转 Before / After 的业务界面
- [x] 仅展示客户业务时间线；工作流枚举、能力约束、路线和原始模型信息收纳在技术详情
- [x] `BusinessDetection` 业务类与 raw YOLO / VLM 类、置信度来源分离
- [x] `.env.example`、本地 `.env` 自动加载、AI 状态 API、密钥与权重 Git 忽略
- [x] 受控清洁前图片的精确检测框 / 置信度回放；主工作台常驻工单详情与业务审计
- [x] 回放 API 与浏览器验证：图片上传 → Robot B 工单 → 红框证据 → SLAM / 调度 → 验收；新实例 Console 0 error
- [ ] 配置本地 YOLO 权重并验证真实加载
- [ ] 配置 `DASHSCOPE_API_KEY` 并验证 DashScope Qwen-VL 可达性
- [ ] Scenario 02：REAL YOLO → REAL Qwen-VL → REAL Multi-view VLM → REAL post-clean AI verification → CLOSED
- [ ] 浏览器 REAL E2E 验收（刷新后工单持久化、Console 0 error）

在上述 REAL 验收通过前，禁止将 Phase 8R 标记为 Done，禁止继续产品化 Scenario 01 / 03 / 04 或进入 Phase 9。

---

# 五、固定 Demo Scenario

- [x] Scenario 01：Outdoor Autonomous / Robot A
- [x] Scenario 02：Multi-view Heavy Cleaning / Robot B
- [x] Scenario 03：Cross-building Orchestration / Robot C
- [x] Scenario 04：Capability Boundary / Human Fallback

---

# 六、待确认

- [ ] 真实生产 Camera → SLAM 底层数学算法
- [ ] 多摄像头近同步 Frame 的生产实现方式
- [ ] 生产环境真实 AI confidence threshold
- [ ] Scheduler 真实权重
- [ ] 最低电量 threshold
- [ ] 机器人任务超时策略
- [ ] Elevator 等待超时
- [ ] Navigation 重试次数
- [ ] Verification 最大 Retry 次数
- [ ] Human Review 真实业务入口
- [ ] Human Work Order 未来接什么工单系统
- [ ] Robot B/C 具体真实厂商型号
- [ ] Robot D 后续配送业务定义

---

# 七、后续优化 / Roadmap

以下不得在当前 MVP 中擅自实施：

- [ ] RAG
- [ ] Planner Agent
- [ ] VLA
- [ ] ROS 2 Runtime
- [ ] Nav2 Runtime
- [ ] Open-RMF Runtime
- [ ] 真实机器人
- [ ] 真实电梯
- [ ] 真实门禁
- [ ] 3D Digital Twin
- [ ] Predictive Model
- [ ] RL
- [ ] PostgreSQL
- [ ] Redis
- [ ] Kafka
- [ ] Docker
- [ ] Kubernetes

---

# 八、GitHub 开源参考任务

后续合适阶段：

- [ ] 阅读 navigation2 架构
- [ ] 阅读 Open-RMF Fleet / Task / Lift 设计
- [ ] 阅读 rmf_demos
- [ ] 对比当前 Global Spatial Graph
- [ ] 对比 Robot Adapter 架构
- [ ] 对比 Elevator Connector
- [ ] Codex 如认为需要 Fork，先提交复用分析，不得直接重构

---

## Custom YOLO Demo Training｜独立前置任务（已完成，未接入）

- [x] 解压并审计 9 张 Demo 图片；生成本地 raw、YOLO train/val、holdout 与中文 review 目录
- [x] 固定五类 id：`liquid=0`、`can=1`、`leaf=2`、`large_object=3`、`small_litter=4`
- [x] 生成标准 YOLO bbox 预标注、清洁后负样本和可视化检查图
- [x] 使用 YOLO11n 训练；MPS 不兼容时自动 CPU fallback；生成本地 `best.pt` / `last.pt`
- [x] 在 9 张原图逐张推理，并执行三组 before / after 负样本测试
- [x] 生成 `docs/YOLO_DATASET_REPORT.md`
- [ ] 用户确认训练结果后，决定是否做下一轮数据补充/标注或接入 Phase 8R REAL adapter

当前结果：只可靠检出 Demo 4 的 `large_object`；`liquid`、`can`、`small_litter` 在 0.25 阈值漏检，`leaf` 无正样本。禁止接入主流程或标为 REAL 验收通过。
