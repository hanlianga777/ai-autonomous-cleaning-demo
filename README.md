# AI 自主清洁 Demo

面向 AI 解决方案专家岗位展示的园区自主清洁闭环 PoC。目前已完成 **Phase 1–7** 与 **Phase 8｜客户演示工作台产品化层**；主 Scenario 始终可在稳定、可复现的本地 Mock 模式下运行。

## 当前实现范围

- React + TypeScript + Vite 前端，基于 Tailwind CSS 与 shadcn/ui 组件约定
- FastAPI REST API 与 SQLite 初始化
- 东港智慧园区基础模型：A 栋、B 栋及室外区域
- Robot A / B / C 的稳定 Mock 状态数据
- 企业级运营总览：园区概览、基础 KPI、三台机器人状态与系统边界
- 6 张二维模拟 SLAM 地图、固定摄像头 Coverage、全园区 Dijkstra 路线与 Camera → SLAM 四点标定映射
- 空间地图、路径规划与标定映射的前端可视化
- SQLite 工作流审计、SSE 事件流、Mock Robot Adapter、Mock Verification
- 硬约束 Capability Engine、配置化软评分与可展开的 `Why Robot X?` 决策追踪
- 独立 AI Lab：图片 / MP4 上传、YOLO 候选、三帧关键帧策略、Qwen-VL 受约束 JSON 与 Task Profile
- `ai-lab.v1` 统一感知 Schema：`need_clean`、置信度、Task Profile、同源 Camera→SLAM 位置以及非持久化 Scheduler 预检
- 真实 AI 适配器：配置本地 YOLO 权重与 DashScope Key 后启用 `REAL AI MODE`；否则明确降级为 `DEMO MOCK MODE`
- Optimization Center：30 天稳定 Mock 历史、Spatial Heatmap、时段分布、Robot Utilization、KPI 与受限 Optimization Agent
- Interview UX：五个可用一级入口、四类 Scenario 启动卡、状态回放、跨楼栋连接器、Camera → SLAM 与 Before / After 验收讲解
- 默认客户首页：自主清洁任务指挥台。首屏始终展示 Robot A/B/C 的位置、状态、电量、当前工单、6 张 SLAM 地图和业务审计；场景或上传图片只是创建演示工单的入口
- `operations.v1` 服务端演示投影：把既有工作流审计投影为明确标注的 `DEMO PLAYBACK` 遥测，不新增第二套调度、坐标映射或状态机

尚未实现真实设备执行、真实长期运营数据接入与 REAL AI 实跑验证。上传自动匹配仅面向仓库内四张受控清洁前原图；生产环境仍需由真实 YOLO / Qwen-VL 推理替代该 Demo 适配层。当前范围仍为稳定可复现的 PoC Demo。

## 目录

```text
./
├── backend/
│   ├── api/routes.py             # Phase 1 REST endpoints
│   ├── data/mock_data.py         # 稳定 Mock 园区与机器人数据
│   ├── database/connection.py    # SQLite 初始化与读取
│   ├── spatial/                  # 地图、路径规划、四点标定
│   ├── perception/               # REAL / MOCK YOLO、Qwen-VL、关键帧与 AI Lab 编排
│   ├── workflow/                 # 事件状态机与 Mock 事件
│   ├── scheduling/               # 能力约束与可解释评分
│   ├── robots/                   # Unified Mock Robot Adapter
│   ├── verification/             # Mock 验收
│   ├── main.py                   # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/api/                  # 后端 API client
│   ├── src/components/ui/         # shadcn/ui-compatible primitive components
│   ├── src/components/            # Dashboard components
│   ├── src/types/                # API data types
│   └── src/App.tsx                # Operations Dashboard
├── docs/                          # 项目基线、决策、架构与开发交接
└── README.md
```

开始新开发前，请依次阅读 [交接说明](docs/CODEX_HANDOFF.md)、[项目上下文](docs/PROJECT_CONTEXT.md)、[关键决策](docs/DECISIONS.md)、[任务清单](docs/TODO.md) 与 [技术架构](docs/ARCHITECTURE.md)。

## 启动

需要 Python 3.10+ 与 Node.js 20+。

### macOS 一键启动（推荐）

双击 `start_demo.command`。它会自动准备缺失依赖、分别后台启动 FastAPI 与 Vite、避免重复占用 8000 / 5173 端口，并在复用 8000 服务前验证 `operations.v1` API 契约；旧版后端不会被静默复用而造成空白工作台。终端会显示每项服务是已启动还是复用了既有服务。

双击 `stop_demo.command` 可停止由启动脚本创建的进程；它不会终止已在端口上运行、但并非本脚本启动的其他服务。

### 手动启动

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

另开终端：

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:5173`。API 文档位于 `http://localhost:8000/docs`。

本地 Vite 已将 `/api` 代理至 `http://127.0.0.1:8000`，因此可使用 `localhost:5173` 或 `127.0.0.1:5173` 访问前端。后端暂不可用时，Dashboard 仍会显示内置的稳定 Mock 数据与显式离线提示，不会白屏。

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | 服务健康状态与 Mock 模式标识 |
| `GET /api/park` | 园区基础信息 |
| `GET /api/robots` | 三台机器人状态 |
| `GET /api/dashboard` | Dashboard 聚合数据 |
| `GET /api/spatial/overview` | 地图、摄像头与机器人空间概览 |
| `GET /api/spatial/routes?start=&target=` | Dijkstra 全园区路径 |
| `GET /api/spatial/cameras/{camera_id}/map?u=&v=` | Pixel → SLAM 映射 |
| `GET /api/events` | 持久化的清洁事件 |
| `POST /api/events/mock/{template}` | 创建稳定 Mock 事件 |
| `POST /api/events/{event_id}/run` | 运行完整 Mock Workflow |
| `POST /api/scheduler/evaluate?event_id=` | 输出可解释调度决策 |
| `GET /api/events/stream` | SSE 工作流状态流 |
| `GET /api/ai-lab/status` | 已解析的 REAL / MOCK 运行状态（不泄露密钥） |
| `POST /api/ai-lab/analyze?camera_id=` | 上传图片 / MP4 并返回感知链路与 Task Profile |
| `GET /api/workbench/scenario02/assets` | Scenario 02 的 Camera + Event + View 素材清单与缺失状态 |
| `POST /api/workbench/scenario02/run` | 组合既有感知、多视角、调度、执行与验收结果供客户工作台播放 |
| `GET /api/workbench/scenarios` | 四组受控客户演示场景及其 Camera + Event + View 素材清单 |
| `POST /api/workbench/events/{event_id}/run` | 运行所选场景的既有 AI、空间、调度、执行与验收链路 |
| `POST /api/workbench/upload` | 上传受控清洁前原图，SHA-256 匹配场景后自动运行完整闭环 |
| `GET /api/operations/snapshot` | `operations.v1` 指挥台读模型：三台机器人模拟遥测、当前工单与场景目录 |
| `POST /api/operations/runs/{event_id}` | 创建一个既有 Scenario 的服务端可审计演示回放 |
| `POST /api/operations/upload` | 上传受控清洁前原图并创建同一 `operations.v1` 演示回放 |
| `GET /api/operations/work-orders` | 从 SQLite CleaningEvent 生成的客户工单中心索引 |
| `GET /api/system/ai-status` | 无密钥的 YOLO / Qwen-VL / Simulation 真实运行状态 |

## 数据与模式说明

应用启动时会创建 `backend/ai_cleaning_demo.db`，并写入园区和机器人快照。该数据库文件是可再生的本地运行数据，不包含真实客户或设备数据。

默认明确运行在 `DEMO MOCK MODE`。AI Lab 的 `AI_LAB_MODE=auto` 仅在本地权重与 `DASHSCOPE_API_KEY` 均配置时自动启用 `REAL AI MODE`；`AI_LAB_MODE=mock` 可强制稳定 Mock。REAL 管线失败时会明确返回错误，不会伪造成 Mock 或真实结果。

## Phase 8R｜客户产品层与 REAL AI 前置配置

客户默认导航只显示“自主清洁工作台、工单中心、运营分析”。技术后台、AI Lab、Scheduler 与原始审计保留在“高级模式 / 技术详情”。客户默认只产品化 Scenario 02；Scenario 01 / 03 / 04 保留原有技术能力，等待 Scenario 02 验收。

复制 [.env.example](.env.example) 为项目根目录的 `.env`，填入本机模型位置和 DashScope Key。`.env` 与模型权重已被 Git 忽略，启动脚本会打印不含密钥的 AI 状态。

```bash
cp .env.example .env
# 编辑 .env：填写 AI_LAB_YOLO_MODEL 与 DASHSCOPE_API_KEY
```

没有这两项时系统会明确使用 Mock；不会伪造 REAL AI 结果。当前仓库尚未在本机完成 REAL Scenario 02 实跑验收。

## Phase 2｜Spatial Engine

- 6 张二维模拟 SLAM Map：Outdoor、A-B1、A-1F、A-2F、B-1F、B-2F
- `Park → Building → Floor → Zone → (x, y)` 的空间层级与 Zone 属性
- Dijkstra 全园区图：同层、本楼电梯、2F Skybridge 连接器
- 固定摄像头位置、Coverage Polygon、邻接摄像头与四点标定数据
- `CAM-A1-01` 支持可复现的 Pixel → SLAM 单应性映射

Phase 2 不包含机器人调度、任务状态机、YOLO/Qwen-VL、Agent 或 SSE。

## Phase 3｜Workflow + Scheduler

- Cleaning Event、Task Profile、Assignment Decision、Navigation Plan、Verification 与 Human Fallback Work Order
- 所有状态变更写入 SQLite，并经由 SSE 向前端推送
- 确定性 Hard Constraint：服务范围、地面、能力、电梯/Skybridge、可达性、电量与机器人状态
- 配置化 Soft Score：能力适配、ETA、Battery、Workload、Zone、楼层、跨楼栋、噪声
- Mock Robot Adapter 与 Mock Verification；不接真实机器人、不调用 AI
- Dashboard 可运行 4 个稳定 Mock 事件，并展示 Decision Trace 与 `Why Robot X?`

## Phase 4｜YOLO + Qwen-VL + AI Lab

- AI Lab 与固定 Scenario 分开；AI Lab 不自动创建事件或派发机器人
- REAL / MOCK 共用 `ai-lab.v1` Schema；其中 `workflow_input` 是可直接交给 Phase 3 的 CleaningEvent seed，`scheduler_preview` 只做预检、不写库
- 内置 4 个兼容性用例：室外小垃圾 → A、液体重污 → B、室内纸杯 → C、大纸箱/垃圾袋 → Human Fallback
- 图片支持 JPG / JPEG / PNG / WEBP，视频支持 MP4；最大 20 MB
- MP4 REAL 模式提取首、中、尾三个关键帧，选择最高置信度候选帧给 Qwen-VL
- `backend/requirements-real-ai.txt` 是 REAL YOLO / MP4 的可选依赖；主启动脚本不下载模型或安装重型依赖

### 配置 REAL AI MODE

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-real-ai.txt
export AI_LAB_MODE=real
export AI_LAB_YOLO_MODEL=/absolute/path/to/yolo26n.pt
export DASHSCOPE_API_KEY=your_dashscope_key
# 可选：export DASHSCOPE_VL_MODEL=qwen-vl-max
uvicorn main:app --reload --port 8000
```

未完成上述配置时无需阻塞开发或演示：AI Lab 与 Dashboard 都会明确显示 `DEMO MOCK MODE`。

> 当前限制：REAL MODE 尚未使用真实 YOLO 权重和 Qwen-VL Key 完成实跑验证。

## Phase 5｜Multi-view Perception Agent

- 仅在 `0.55 <= confidence < 0.85` 的灰区触发 LangGraph Agent
- 工具面固定为 `Camera Coverage Tool`、`Frame Fetch Tool`、`VLM Tool`，最多选择 2 个额外摄像头、最多 2 次 iteration
- 复用 Phase 2 `CAMERAS` Coverage 与 SLAM 坐标；不另建空间映射
- 最终视觉决策仅为 `CONFIRM`、`REJECT` 或 `HUMAN_REVIEW`
- Dashboard 提供 Scenario 02：A 栋 1F 疑似奶茶污渍（0.67）→ 多视角确认（0.92）→ 原有能力引擎 / Scheduler 选择 Robot B
- UI 仅展示 Tool Calls、Evidence、Selected Cameras、Final Confidence 与 Decision，不暴露 Chain-of-Thought

## Phase 6｜Analytics + Optimization

- 生成并聚合 30 天、300 条可复现 Mock 运营记录
- Optimization Center 使用 Apache ECharts 展示 Spatial Heatmap、时段分布和 Robot Utilization
- 提供自主闭环率、人工介入率、一次通过率、平均响应/闭环时间、Multi-view 恢复率等 KPI
- Optimization Agent 只读取 Heatmap、Robot Utilization、Task History 三个聚合输入，输出待机点、主动巡检与资源配置建议
- 建议不自动修改 YOLO / VLM confidence、Capability Engine、Scheduler 或 Robot-first + Human Fallback，须人工确认后才可转为运营配置

## Phase 7｜Interview UX

- 五个一级入口：运营总览、AI 事件中心、机器人编排、优化中心、AI Lab
- AI 事件中心提供四个可直接运行的稳定 Scenario：Robot A、Robot B 多视角、Robot C 跨楼栋、Human Fallback
- 工作流结果以状态回放呈现 Robot、Elevator、Skybridge；明确标为 Mock 状态，不宣称真实设备遥测
- 展示 Camera → SLAM 映射、Decision Trace、Why Robot X?、Before / After 验收摘要
- 机器人编排页给出能力边界与跨楼栋路径的三句讲解线索

## Phase 8｜客户演示工作台

- 默认首页改为中文优先的“自主清洁任务工作台”；Phase 1–7 页面保留在技术后台与 AI 能力验证入口
- 四组现场素材分别对应：室外纸巾 → Robot A、三机位奶茶污渍 → Robot B、多楼栋二楼易拉罐 → Robot C、大纸箱 → Human Fallback
- 上传任一受控清洁前原图会以 SHA-256 确定性匹配事件，随后复用 `ai-lab.v1`、Phase 2 `map_pixel_to_slam`、Phase 3 Scheduler / Verification；不新增第二套 AI 或坐标算法
- Scenario 02 在 0.67 置信度触发 Phase 5 Multi-view Agent，真实素材的 CAM-A1-02 与 CAM-A1-04 作为两个补充视角；UI 仅展示工具、证据、摄像头、置信度和决定
- 指挥台首屏：三台机器人位置 / 状态 / 电量、工单队列、6 张 2D SLAM 地图、Camera Coverage、选中工单的 AI / 调度 / 路线 / 多视角 / 验收，以及完整业务审计
- `operations.v1` 只将已完成的确定性工作流投影为服务端 `DEMO PLAYBACK`，前端不再用 `setTimeout` 伪造业务状态；所有位置与电量均明确标记为模拟回放，而非设备遥测
- Scenario 04 没有提供清洁后图且应进入人工兜底，工作台明确展示待人工回传验收，不伪造 PASS 图

## 下一阶段边界

Phase 8 的素材接入、四场景自动播放、指挥台读模型与浏览器验收已完成。未进入 Phase 9。

## 验证

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -v
cd frontend && npm run build
```
