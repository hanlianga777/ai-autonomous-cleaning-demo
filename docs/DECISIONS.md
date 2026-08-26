# DECISIONS.md

# 项目关键决策记录

本文档只记录已经经过讨论并明确确认的重要决策。

---

## 决策 1：定位为真实项目基础上的升级 PoC

**最终决定：**

真实项目能力与 新增能力必须明确区分。

真实项目是项目基础。

Multi-view Agent、完整园区级异构调度、Optimization Agent 等部分属于基于真实业务进一步设计的升级 PoC。

**原因：**

既保持项目真实性，又体现 AI 解决方案专家对现有方案进行产品演进设计的能力。

**曾考虑方案：**

- 把全部 能力都包装成真实项目已落地。
- 只展示真实项目现有功能。

**为什么没有采用：**

前者存在真实性风险。

后者技术深度不足。

**对后续开发的影响：**

README、面试介绍和文档必须标明：

`Real Project Baseline`

与

`PoC Enhancements`

---

## 决策 2：采用 A + C 的机器人 Demo 路线

**最终决定：**

- 前端使用 2D 园区 / SLAM 仿真；
- 后端按照真实 Robot API + Adapter 架构设计。

**原因：**

无需真实机器人和 ROS，也能展示真实工程架构。

**曾考虑方案：**

- 纯软件模拟；
- ROS / Nav2 仿真；
- 直接接真实机器人。

**为什么没有采用：**

ROS / 真实机器人开发成本过高，不符合面试 Demo 成本收益。

**对后续开发的影响：**

使用 Mock Robot Adapter。

不默认引入 ROS/Nav2。

---

## 决策 3：园区采用多楼栋、多楼层结构

**最终决定：**

A栋：

- B1
- 1F
- 2F

B栋：

- 1F
- 2F

两栋 2F 通过空中连廊连接。

另有 Outdoor Map。

**原因：**

形成：

- 跨楼层；
- 电梯；
- 跨楼栋；
- 多地图；

真实调度问题。

**曾考虑方案：**

- 单楼层；
- 只有多楼层；
- 两栋建筑通过室外移动。

**为什么没有采用：**

单楼层过于简单。

真实项目存在空中连廊，所以最终使用 Skybridge。

**对后续开发的影响：**

需要 Global Spatial Graph 和 Map Connector。

---

## 决策 4：SLAM 地图采用人工手持设备扫图

**最终决定：**

通过手持 SLAM 建图设备人工扫描园区，生成地图文件。

**原因：**

符合真实项目业务流程。

**曾考虑方案：**

未采用完全虚构地图来源。

**对后续开发的影响：**

前端地图是 SLAM 地图模拟，不应描述成 AI 自动生成地图。

---

## 决策 5：摄像头采用四点标定映射 SLAM 坐标

**最终决定：**

一个固定摄像头绑定 4 个固定关键点，建立摄像头视觉空间与 SLAM 二维空间的映射。

**原因：**

符合真实项目方式。

**曾考虑方案：**

- ROI → 固定清扫点；
- 直接使用摄像头所在 Zone；
- 四个预定义目标点。

**为什么没有采用：**

真实逻辑是通过空间映射推算具体二维坐标，不是简单固定点位。

**对后续开发的影响：**

Phase 2 必须实现稳定可复现的 Camera → SLAM Mapping。

真实底层具体数学实现方式仍不得擅自声称。

---

## 决策 6：Multi-view Perception 是真正需要保留的 Agent

**最终决定：**

低置信度事件才触发 Multi-view Perception Agent。

**原因：**

单摄像头存在：

- 遮挡；
- 光照；
- 反光；
- 小目标；
- 角度不足。

Agent 需要根据空间覆盖关系自主选择其他摄像头作为工具。

**曾考虑方案：**

给每个 AI 模块都包装 Agent。

**为什么没有采用：**

普通 Workflow 改名 Agent 属于 Agent Washing。

**对后续开发的影响：**

Agent 只能调用有限工具：

- Camera Coverage Tool
- Frame Fetch Tool
- VLM Tool

---

## 决策 7：正常机器人调度不是 Agent

**最终决定：**

机器人选择使用：

`Hard Constraint + Soft Score + Workflow`

**原因：**

机器人能力、电量、距离、ETA、楼层等属于确定性问题。

**曾考虑方案：**

Cleaning Planner Agent / Robot Scheduling Agent。

**为什么没有采用：**

LLM 不适合替代确定性调度算法。

会增加：

- Token；
- 延迟；
- 成本；
- 不确定性。

**对后续开发的影响：**

Scheduler 必须可解释。

Planner Agent 仅预留给未来复杂冲突场景。

---

## 决策 8：Agent 只处理不确定性问题

**最终决定：**

MVP 仅保留：

1. Multi-view Perception Agent
2. Optimization Agent

Planner Agent 暂不实现。

**原因：**

减少 Agent 数量，提高可信度和稳定性。

**曾考虑方案：**

- Vision Agent
- Spatial Agent
- Robot Agent
- Elevator Agent
- Verification Agent
- Planner Agent
- Exception Agent

**为什么没有采用：**

大部分本质是普通服务或 Workflow。

**对后续开发的影响：**

禁止 Codex 擅自新增大量 Agent。

---

## 决策 9：增加热力分析，但热力图本身不是 Agent

**最终决定：**

Analytics Engine 生成：

- 热力图；
- 时段分布；
- Robot Utilization；
- KPI。

Optimization Agent 再解释数据并提出运营策略。

**原因：**

热力图具有真实物业运营价值，但数据计算无需 LLM。

**曾考虑方案：**

使用垃圾热力图直接提高视觉置信度。

**为什么没有采用：**

可能形成反馈偏差。

**对后续开发的影响：**

热力数据用于：

- 巡检频率；
- 待机点；
- 资源配置；

而不是直接修改 YOLO / VLM confidence。

---

## 决策 10：Robot-first + Human Fallback

**最终决定：**

正常地面清洁任务优先由机器人完成。

人工只作为能力边界兜底。

**原因：**

更符合项目第一商业价值：

降低保洁人工投入。

**曾考虑方案：**

把保洁人员和机器人作为同等候选资源进行评分。

**为什么没有采用：**

会弱化机器人自主闭环和降本故事，并增加员工定位 / 排班复杂度。

**对后续开发的影响：**

人工不进入普通 Scheduler Pool。

只有：

`Candidate Robot = 0`

或自动处理持续失败时：

`HUMAN_FALLBACK`

---

## 决策 11：Robot B / Robot C 采用差异化能力定位

**最终决定：**

Robot B：

重度洗地 / 液体 / 重污染。

Robot C：

室内轻量、高频、低噪日常清洁。

**原因：**

避免两台机器人能力高度重复。

**曾考虑方案：**

Robot B 为通用机器人、Robot C 仅为较弱版本。

**为什么没有采用：**

缺少合理的 Scheduler 选择逻辑。

**对后续开发的影响：**

Capability Profile 必须体现：

- Task Type；
- Surface；
- Cleaning Capability；
- Noise；
- Size；
- Public-space Fitness。

---

## 决策 12：Robot C 可以跨楼栋

**最终决定：**

Robot C 可以通过 A/B 栋 2F 空中连廊跨楼栋调度。

**原因：**

符合真实项目空间条件，并体现资源共享。

**曾考虑方案：**

- 每栋机器人固定；
- 从室外跨楼栋。

**为什么没有采用：**

实际存在空中连廊。

**对后续开发的影响：**

需要 Skybridge Connector。

---

## 决策 13：新增 Robot D 配送机器人，但当前不演示

**最终决定：**

新增 Robot D / Delivery Robot 作为未来扩展资源。

当前：

- 不定义完整能力；
- 不参加 Scheduler；
- 不参加 Scenario；
- 不开发配送 Workflow。

**原因：**

体现平台未来可以扩展到更多园区机器人，但不能干扰当前清洁主线。

**曾考虑方案：**

当前直接开发配送功能。

**为什么没有采用：**

会扩大 MVP 范围。

**对后续开发的影响：**

仅预留数据模型和未来 Adapter 扩展空间。

---

## 决策 14：前端采用 React 技术栈

**最终决定：**

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- ECharts

**原因：**

V1 Streamlit 前端过于简单，不适合面试产品展示。

**曾考虑方案：**

继续使用 Streamlit。

**为什么没有采用：**

UI 和交互自由度不足。

**对后续开发的影响：**

前后端分离。

---

## 决策 15：不同时引入多个 UI Design System

**最终决定：**

shadcn/ui + Tailwind 为唯一主要 UI 底座。

**原因：**

避免 UI 风格混乱。

**曾考虑方案：**

MUI / Mantine / Ant Design 等同时混用。

**为什么没有采用：**

容易产生明显模板感。

**对后续开发的影响：**

Ant Design Pro 只参考信息架构。

React Flow 只有确实需要时才使用。

---

## 决策 16：Scenario 与真实 AI Lab 分开

**最终决定：**

主 Demo 使用固定 Scenario。

另设 AI Lab。

**原因：**

Scenario 保证面试稳定。

AI Lab 用于证明真实 YOLO + Qwen-VL 能力。

**曾考虑方案：**

面试全部现场调用真实 AI。

**为什么没有采用：**

网络 / API 出错可能导致 Demo 整体失败。

**对后续开发的影响：**

必须支持：

- REAL MODE
- MOCK MODE

并明确显示当前模式。

---

## 决策 17：当前不引入 RAG

**最终决定：**

MVP 暂不增加 RAG。

**原因：**

当前 Agent 暂不需要大量园区文档知识。

**曾考虑方案：**

通过 RAG 注入机器人说明书、SOP、园区规则。

**为什么没有采用：**

当前属于技术堆叠。

**对后续开发的影响：**

未来如 Planner Agent 真需要动态园区知识，再评估。

---

## 决策 18：当前不引入 ROS / Nav2 / Open-RMF Runtime

**最终决定：**

先参考开源架构，不直接运行完整 ROS / RMF 系统。

**原因：**

设备性能有限，且不属于当前 PoC 核心。

**曾考虑方案：**

直接使用 ROS / Nav2 仿真。

**为什么没有采用：**

复杂度和本地资源成本过高。

**对后续开发的影响：**

参考：

- navigation2
- open-rmf/rmf
- open-rmf/rmf_demos

需要 Fork 时必须先说明复用价值。

---

## 决策 19：采用模块化单体，而不是微服务

**最终决定：**

FastAPI 模块化单体 + React。

**原因：**

Demo 不需要生产级分布式系统。

**曾考虑方案：**

微服务、Kafka、Redis、K8s 等。

**为什么没有采用：**

过度工程化。

**对后续开发的影响：**

禁止 Codex 无授权增加复杂基础设施。

---

## 决策 20：Phase-by-Phase 开发

**最终决定：**

每个 Phase 完成后停止，人工确认后再继续。

**原因：**

避免 Codex 一次性生成不可维护的大工程。

**对后续开发的影响：**

未经明确授权不得自动进入下一 Phase。
