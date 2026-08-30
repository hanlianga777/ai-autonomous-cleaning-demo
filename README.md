# AI Autonomous Cleaning Demo

面向解决方案与产品面试展示的园区自主清洁闭环 PoC：固定摄像头发现问题，云端视觉模型完成语义判断，确定性空间、能力与调度系统决定处置，并以验单形成可审计闭环。

## 当前产品

当前客户演示由四个一级页面组成，均读取同一套 `CleaningEvent`、SQLite transition 与 Fleet/route snapshot：

1. **自主清洁工作台（Workbench）**：实时事件、监控证据、SLAM 地图、机器人位置/状态/电量、任务与闭环详情。
2. **AI 事件处置档案中心（Event Center）**：只读检索、筛选和还原每一个事件的处置依据与历史快照。
3. **AI 自主清洁运营分析中心（Analytics）**：来自结构化演示历史和当前 Runtime 增量的 KPI、热图、时段与利用率分析。
4. **Advanced Technical Observability（高级模式）**：只读展示 AI、空间、调度、工具、模型请求、错误与 Reality Matrix。

完整业务链路是：

`受控边缘检测 → Single-view Cloud VLM → Evidence Sufficiency Gate →（必要时）Multi-view Agent → 语义/置信度判断 → Camera→SLAM → Capability Engine → Scheduler → Dijkstra plan_route() → 执行模拟 → AI 验单 → CLOSED 或 HUMAN_REVIEW`。

系统只有两个 Agent：

- **Multi-view Perception Agent**：在证据不足且可由合法补充视角缓解时，以真实 model tool calling 取证；最多两路摄像头、两轮取证。
- **Robot Operations Agent**：通过受限任务级工具处理待命、配送、暂停与人工完成等操作；不拥有地图、标定、Scheduler、能力或基础设施配置权。

清洁机器人始终由 Capability Engine + Scheduler 选择；`HUMAN_FALLBACK` 只在 Capability zero candidate 时产生。

## 四个演示场景

| Demo | 业务故事 | 正常处置 |
| --- | --- | --- |
| Demo01 | 室外其他小型垃圾 | 赛特净界 S5 自动闭环 |
| Demo02 | A 栋 1F 液体污渍/反光歧义 | Multi-view 取证后由高仙 Omnie 自动闭环 |
| Demo03 | A 栋 2F 地毯易拉罐 | 蜗小白 SC50 经电梯和 Skybridge 跨楼执行 |
| Demo04 | A 栋 2F 通道附近待清运大件废弃物 | zero candidate → 人工搬运 → 云端验单闭环 |

正式 LIVE 回归：Demo01 **5/5**、Demo02 **5/5**、Demo03 **5/5**、Demo04 **3/3**。Stable Replay 四个 Demo 均为 **3/3**，Replay 没有新增 Cloud request，但空间、调度、路线、Fleet、SQLite transition 与验单会重新运行。历史数值不应被理解为未来固定模型输出。

## 真实性边界

| 类型 | 当前实现 |
| --- | --- |
| 真实调用 | `qwen-vl-max` 用于语义/验单；`qwen3-vl-plus` 用于 Multi-view tool calling；Camera→SLAM、Capability、Scheduler、Dijkstra 和 SQLite 都真实执行。 |
| Controlled Evidence | 清洁前后图片与 bbox 来自受控演示证据。**Controlled bbox 不等于本地 REAL YOLO 推理。** |
| PoC Simulation | 机器人移动、电梯/连廊与配送为明确标识的模拟，不是设备遥测或外部平台连接。 |

ASR 未配置，麦克风会保持禁用/明确提示；不伪造语音识别。真实机器人、RTSP/VMS、生产身份与权限、外部配送平台、分布式队列和 ROS/Nav2 不在当前范围。

## 启动

需要 Python 3.10+ 与 Node.js 20+。

macOS 推荐在项目根目录双击 `start_demo.command`。脚本会准备依赖、启动 FastAPI（8000）和 Vite（5173），并验证 `operations.v1` API 契约。使用 `stop_demo.command` 停止由该脚本启动的服务。

也可手动启动：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

打开 <http://localhost:5173/prototype>；API 文档位于 <http://localhost:8000/docs>。当前主入口是阶段式 `/api/demo-v1/events` 与各 stage endpoint；旧 one-shot `/api/demo-v1/runs/*` 已 RETIRED（410）。

## 验收摘要

- 后端：164 项，161 PASS + 3 付费 opt-in skipped。
- 前端：46 项 PASS，TypeScript/Vite build PASS。
- 五位独立 Reviewer（A/B/C/D/E）：均 PASS，P0/P1 为零。
- 用户主观展示验收仍待，不由工程测试替代。

## Source of Truth

新 Session 请按顺序阅读：

1. [PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)
2. [DECISIONS.md](docs/DECISIONS.md)
3. [TODO.md](docs/TODO.md)
4. [ARCHITECTURE.md](docs/ARCHITECTURE.md)
5. [CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md)
6. [AI_INTEGRATION_TEST.md](docs/AI_INTEGRATION_TEST.md)

它们记录当前架构、不可回退边界、P2、交接与真实验收证据；具体历史提交请查看 Git history。
