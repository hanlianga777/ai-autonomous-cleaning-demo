# CODEX_HANDOFF.md

# Codex 项目交接说明

> 如果你第一次进入本项目，请先完整阅读：
>
> 1. `CODEX_HANDOFF.md`
> 2. `PROJECT_CONTEXT.md`
> 3. `DECISIONS.md`
> 4. `TODO.md`
> 5. `ARCHITECTURE.md`
>
> 然后再阅读当前代码和 README。
>
> 不要在不了解上述文档的情况下重新设计项目架构。

---

# 1. 这个项目是什么

这是一个面向 **AI 解决方案专家岗位面试** 的 AI 自主清洁 V2 PoC。

核心场景：

固定摄像头发现地面清洁事件

↓

边缘视觉模型初筛

↓

云端多模态模型研判

↓

必要时多视角 Agent 获取其他摄像头证据

↓

将 Camera 空间位置映射到机器人 SLAM 二维坐标

↓

生成 Cleaning Task Profile

↓

根据机器人能力进行约束过滤和调度

↓

机器人导航到目标位置

↓

执行清洁

↓

固定摄像头重新验收

↓

事件闭环

↓

长期数据形成运营优化。

---

# 2. 真实项目与 PoC 必须严格区分

## Real Project Baseline

真实业务基础包括：

- 固定摄像头；
- 边缘视觉算法；
- 云端二次识别；
- SLAM 建图；
- 摄像头与 SLAM 地图的四点标定；
- 机器人任务调用；
- 固摄验收闭环。

## V2 PoC Enhancements

包括：

- 完整园区空间图；
- A/B 栋；
- 电梯；
- Skybridge；
- 多机器人统一 Capability Model；
- Scheduler；
- Multi-view Perception Agent；
- Analytics；
- Optimization Agent；
- 固定 Scenario；
- AI Lab。

不要把 PoC 增强能力写成真实客户项目已经全部部署。

---

# 3. 当前代码状态

当前 V2 目录：

`ai-cleaning-v2`

Phase 1 已完成。

主要已有内容：

- FastAPI
- SQLite
- React
- TypeScript
- Vite
- Tailwind
- shadcn/ui
- ECharts dependency
- Dashboard
- Park basic data
- Robot A/B/C basic status
- DEMO MOCK MODE
- API fallback
- `/api/health`
- `/api/dashboard`

Phase 1 已通过人工页面验收。

---

# 4. 已解决 Bug

曾出现前端白屏。

原因：

`127.0.0.1:5173`

与

`localhost:5173`

CORS 配置不一致。

现已：

- 同时允许两种地址；
- Vite `/api` proxy；
- frontend relative `/api`；
- offline Mock fallback；
- API失败不再整页白屏。

不要删除这些兜底逻辑。

---

# 5. 当前最高优先级

已完成：

# Phase 2｜Spatial Engine

- 一键启动 / 停止脚本；
- 6 张 2D SLAM Map；
- Spatial Data Model；
- Global Spatial Graph；
- Elevator Connector；
- Skybridge Connector；
- Camera Coverage；
- Camera 4-point Mapping；
- Dijkstra；
- 跨楼层和跨楼栋路线测试；
- 空间运营地图与标定映射前端展示。

验证已通过：3 个 Python 空间单元测试，以及前端 TypeScript / Vite 生产构建。

当前下一阶段为 **Phase 3｜Workflow + Scheduler**。未经用户明确授权，不得开始。

---

# 6. 当前园区结构不可随意修改

## A栋

```text
B1
1F
2F
```

## B栋

```text
1F
2F
```

A / B 栋：

2F Skybridge 连接。

各自具有 Elevator。

## Outdoor

独立地图。

地图总计：

```text
OUTDOOR
A_B1
A_1F
A_2F
B_1F
B_2F
```

---

# 7. Camera → SLAM 逻辑不可改成简单 ROI

真实业务：

一个 Camera 绑定 4 个固定点。

这些点同时对应 SLAM 地图坐标。

基于四点建立：

```text
Camera Image Space
→
SLAM Map Space
```

因此垃圾应能够获得具体：

```text
Building
Floor
Zone
x
y
```

不要退化成：

```text
Camera 03
→
固定 Cleaning Point 03
```

---

# 8. 机器人设定不可随意修改

## Robot A

Outdoor。

不乘电梯。

## Robot B

Heavy Scrubber。

主要负责：

- 液体；
- 水渍；
- 奶茶；
- 重污；
- 环氧；
- 强刷洗。

可乘电梯。

## Robot C

Indoor Light Cleaner。

主要负责：

- 小型干垃圾；
- 纸屑；
- 杯子；
- 瓶子；
- 瓷砖；
- 地毯。

低噪、小体积。

可乘电梯。

可经 2F Skybridge 跨楼栋。

## Robot D

Delivery Robot。

只作为未来类型预留。

当前：

**不要实现配送业务。**

不要加入 Scenario。

不要加入 Cleaning Scheduler。

---

# 9. Human Fallback 规则不可改成 Human vs Robot 调度

最终已确认：

```text
Robot-first
+
Human Fallback
```

人工不进入正常 Scheduler Pool。

只有：

- Robot 不支持；
- 大型纸箱；
- 大垃圾袋；
- 大件杂物；
- Robot 不可达；
- 重复失败；

才进入：

`HUMAN_FALLBACK`

---

# 10. 不允许随意增加 Agent

当前 MVP Agent 只有：

## Multi-view Perception Agent

处理低置信度视觉信息。

## Optimization Agent

解释长期运营数据。

正常 Scheduler：

不是 Agent。

Route Planner：

不是 Agent。

Spatial：

不是 Agent。

Elevator：

不是 Agent。

Robot Adapter：

不是 Agent。

Verification：

不是 Agent。

如果需要新增 Agent：

必须先说明：

1. 为什么普通 Workflow 不够；
2. Agent 解决什么不确定性；
3. 会调用什么 Tools；
4. Token 和延迟成本；
5. 为什么值得增加。

未经用户确认不要实现。

---

# 11. Scheduler 必须确定性和可解释

采用：

```text
Hard Constraints
→
Candidate Robots
→
Soft Score
→
Assignment Decision
```

不要让 LLM 直接决定 Robot。

每次选择必须保留：

- candidates；
- reject reason；
- score components；
- final score；
- selected robot。

前端后续需要：

`Why Robot X?`

---

# 12. LLM 不直接控制机器人

正确架构：

```text
Agent / LLM
→
Decision / Structured Output
→
Workflow Validation
→
Scheduler / Adapter
→
Robot
```

禁止：

```text
LLM
→
直接生成 Robot Command 并发送设备
```

---

# 13. 前端设计要求

目前前端只是 Phase 1 工程页。

不要在 Phase 2–6 过度精修。

Phase 7 再集中做 Interview UX。

统一使用：

```text
shadcn/ui
TailwindCSS
ECharts
```

禁止擅自混入：

- MUI
- Mantine

Ant Design Pro：

只作为后台 IA 参考。

React Flow：

只有业务确实需要时使用。

视觉要求：

- 简约；
- 克制；
- 企业级；
- 专业；
- 少 AI 味；
- 不做传统蓝色大屏；
- 不做过度 Glow；
- 不做大量 Gradient；
- 不做无意义动画。

地图是未来主 Dashboard 的主要视觉区域。

---

# 14. AI Lab 与 Scenario 必须分开

固定 Scenario：

必须稳定。

不依赖真实云 API。

AI Lab：

允许现场调用真实：

- YOLO；
- Qwen-VL。

必须显示：

```text
REAL AI MODE
```

或：

```text
DEMO MOCK MODE
```

不得伪装。

---

# 15. V1 代码

用户此前已经有 V1：

- YOLO26n；
- Qwen-VL；
- robot_dispatch；
- video_pipeline；
- Streamlit；
- post-clean verification。

当前 V2 Workspace 尚未自动找到该代码。

Phase 4 再处理迁移。

不要因为暂时找不到 V1 阻塞 Phase 2 / 3。

---

# 16. 开源项目参考

后续可以参考：

```text
https://github.com/ros-navigation/navigation2
https://github.com/open-rmf/rmf
https://github.com/open-rmf/rmf_demos
```

主要学习：

- Navigation；
- Fleet；
- Task；
- Lift；
- Map；
- Multi-floor；
- Multi-robot；
- Infrastructure Integration。

当前：

**参考优先于集成。**

不要直接安装完整 ROS 2 / RMF。

如果认为 Fork 有明显价值：

先提交：

```text
1. 想 Fork 哪个 Repo
2. 具体复用什么
3. 替代当前什么模块
4. 新增多少依赖
5. 对 Mac M1 / 8GB 的影响
6. 为什么值得
```

获得确认后再操作。

---

# 17. 当前设备约束

开发设备：

MacBook Air M1 2020。

RAM：

8GB。

ARM64。

剩余磁盘空间历史约：

20GB。

因此：

禁止默认增加：

- Docker Desktop；
- Kubernetes；
- 大型本地模型；
- ROS 2；
- 多个重量级服务。

优先：

本地轻量工程

+

云端 AI API。

---

# 18. 开发 Phase

严格顺序：

```text
Phase 1
Engineering Skeleton
DONE

Phase 2
Spatial Engine
DONE

Phase 3
Workflow + Scheduler
NEXT

Phase 4
YOLO + Qwen-VL + AI Lab

Phase 5
Multi-view Agent

Phase 6
Analytics + Optimization

Phase 7
Interview UX
```

每完成一个 Phase：

**必须停止。**

不要自行进入下一 Phase。

---

# 19. 每个 Phase 完成后必须更新的文档

至少检查并更新：

## PROJECT_CONTEXT.md

如果：

- 架构变化；
- 新模块完成；
- 技术栈改变；
- 新功能上线。

## DECISIONS.md

只有：

发生新的重要正式决策时更新。

不要把普通代码修改写进去。

## TODO.md

必须更新：

- 已完成；
- 当前进行；
- 下一阶段；
- 待确认。

## ARCHITECTURE.md

如：

- 新增模块；
- API变化；
- 数据流变化；
- Agent变化；
- Spatial Graph变化；

必须更新。

## CODEX_HANDOFF.md

每一个 Phase 完成后都应该更新：

```text
目前做到哪里
当前最高优先级
下一步是什么
```

---

# 20. 每次开发前的行为规则

开始工作前：

1. 阅读项目 Markdown；
2. 查看当前代码；
3. 查看 README；
4. 判断当前 Phase；
5. 不重复已完成工作；
6. 不擅自改变已确认产品设定。

---

# 21. 每次开发后的汇报格式

请统一输出：

## 本阶段完成内容

## 修改文件

## 新增 API / Data Model

## 测试结果

## 如何运行

## 当前限制

## 下一阶段建议

然后：

**停止。**

等待用户确认。

---

# 22. 项目最终技术故事

整个项目最终必须可以用：

```text
SEE
↓
JUDGE
↓
LOCATE
↓
PLAN
↓
ACT
↓
OPTIMIZE
```

解释。

SEE：

Camera + YOLO

JUDGE：

Qwen-VL + Multi-view Agent

LOCATE：

Camera → SLAM

PLAN：

Capability + Scheduler

ACT：

Robot Adapter + Navigation + Verification

OPTIMIZE：

Heatmap + Optimization Agent

---

# 23. 最终成功标准

本项目不是以：

- Agent 数；
- 代码量；
- 框架数量；

判断成功。

最终必须满足：

1. 一个完全陌生的面试官 5 分钟可以理解业务。
2. 清楚知道为什么选择 Robot A/B/C。
3. Camera → SLAM 可以可视化。
4. Multi-view Agent 有真实 Tool Selection。
5. 可以展示跨楼栋、电梯、Skybridge。
6. 系统知道 Robot 能力边界。
7. Human Fallback 合理。
8. 自动验收闭环。
9. 历史数据可以产生运营优化。
10. 无真实 AI API 时 Demo 仍能稳定展示。
11. 所有关键决策可以解释。
12. 整体像一个可落地 AI 解决方案，而不是 AI API 拼装 Demo。
