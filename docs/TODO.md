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

## Phase 4｜AI Lab 兼容性验收（等待人工确认）

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
- [ ] 用户最终验收确认后，才可进入 Phase 5

---

## Phase 5｜Multi-view Perception Agent

- [ ] 接入 LangGraph
- [ ] Camera Coverage Tool
- [ ] Frame Fetch Tool
- [ ] VLM Tool
- [ ] Agent Camera Selection
- [ ] Max Additional Cameras = 2
- [ ] Max Agent Iterations = 2
- [ ] CONFIRM
- [ ] REJECT
- [ ] HUMAN_REVIEW
- [ ] Decision Trace
- [ ] 不显示 Chain-of-Thought

---

## Phase 6｜Analytics + Optimization

- [ ] 生成 30 天模拟历史数据
- [ ] Spatial Heatmap
- [ ] Time Distribution
- [ ] Top Hotspots
- [ ] Robot Utilization
- [ ] Autonomous Closure Rate
- [ ] Human Intervention Rate
- [ ] First-pass Success Rate
- [ ] Average Response Time
- [ ] Average Closure Time
- [ ] Multi-view Recovery Rate

### Optimization Agent

- [ ] Heatmap Tool
- [ ] Robot Utilization Tool
- [ ] Task History Tool
- [ ] Generate Optimization
- [ ] 待机点优化建议
- [ ] 主动巡检频率建议
- [ ] 资源配置建议

---

## Phase 7｜Interview UX

- [ ] Operations Dashboard
- [ ] AI Event Center
- [ ] Robot Orchestration
- [ ] Optimization Center
- [ ] AI Lab
- [ ] Scenario Launcher
- [ ] Robot Animation
- [ ] Elevator Animation
- [ ] Skybridge Animation
- [ ] Camera → SLAM Animation
- [ ] Decision Trace
- [ ] Why Robot X
- [ ] Before / After
- [ ] Heatmap
- [ ] KPI

---

# 五、固定 Demo Scenario

- [ ] Scenario 01：Outdoor Autonomous / Robot A
- [ ] Scenario 02：Multi-view Heavy Cleaning / Robot B
- [ ] Scenario 03：Cross-building Orchestration / Robot C
- [ ] Scenario 04：Capability Boundary / Human Fallback

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
