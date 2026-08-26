# AI 自主清洁 V2 Demo

面向 AI 解决方案专家岗位展示的园区自主清洁闭环 PoC。目前已完成 **Phase 1｜工程骨架** 与 **Phase 2｜Spatial Engine**；系统仍明确运行在稳定、可复现的本地 Mock 模式。

## 当前实现范围

- React + TypeScript + Vite 前端，基于 Tailwind CSS 与 shadcn/ui 组件约定
- FastAPI REST API 与 SQLite 初始化
- 东港智慧园区基础模型：A 栋、B 栋及室外区域
- Robot A / B / C 的稳定 Mock 状态数据
- 企业级运营总览：园区概览、基础 KPI、三台机器人状态与系统边界
- 6 张二维模拟 SLAM 地图、固定摄像头 Coverage、全园区 Dijkstra 路线与 Camera → SLAM 四点标定映射
- 空间地图、路径规划与标定映射的前端可视化
- `Apache ECharts` 已纳入前端依赖，供后续 Analytics 阶段使用

尚未实现工作流、任务调度、机器人执行、视觉模型、Agent、SSE 或 ECharts 图表；这些属于 Phase 3 及以后阶段。

## 目录

```text
ai-cleaning-v2/
├── backend/
│   ├── api/routes.py             # Phase 1 REST endpoints
│   ├── data/mock_data.py         # 稳定 Mock 园区与机器人数据
│   ├── database/connection.py    # SQLite 初始化与读取
│   ├── spatial/                  # 地图、路径规划、四点标定
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

双击 [start_demo.command](/Users/zhanghaohan/Documents/ChatGPT/Agent项目/ai-cleaning-v2/start_demo.command)。它会自动准备缺失依赖、分别后台启动 FastAPI 与 Vite、避免重复占用 8000 / 5173 端口，并打开 Dashboard。终端会显示每项服务是已启动还是复用了既有服务。

双击 [stop_demo.command](/Users/zhanghaohan/Documents/ChatGPT/Agent项目/ai-cleaning-v2/stop_demo.command) 可停止由启动脚本创建的进程；它不会终止已在端口上运行、但并非本脚本启动的其他服务。

### 手动启动

```bash
cd ai-cleaning-v2/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

另开终端：

```bash
cd ai-cleaning-v2/frontend
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

## 数据与模式说明

应用启动时会创建 `backend/ai_cleaning_v2.db`，并写入园区和机器人快照。该数据库文件是可再生的本地运行数据，不包含真实客户或设备数据。

当前明确运行在 `DEMO MOCK MODE`。后续接入真实 YOLO/Qwen-VL 后，才会实现 REAL / MOCK 两种模式的切换。

## Phase 2｜Spatial Engine

- 6 张二维模拟 SLAM Map：Outdoor、A-B1、A-1F、A-2F、B-1F、B-2F
- `Park → Building → Floor → Zone → (x, y)` 的空间层级与 Zone 属性
- Dijkstra 全园区图：同层、本楼电梯、2F Skybridge 连接器
- 固定摄像头位置、Coverage Polygon、邻接摄像头与四点标定数据
- `CAM-A1-01` 支持可复现的 Pixel → SLAM 单应性映射

Phase 2 不包含机器人调度、任务状态机、YOLO/Qwen-VL、Agent 或 SSE。

## 下一阶段边界

下一阶段为 **Phase 3｜Workflow + Scheduler**。在用户明确授权前，不应开始实现调度、任务状态机或机器人执行逻辑。

## 验证

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -v
cd frontend && npm run build
```
