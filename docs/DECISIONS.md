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

---

## 决策 21：缺少 V1 时保留可替换的 REAL / MOCK 感知适配器

**最终决定：**

Phase 4 不因 V1 源码缺失而阻塞。以独立 `perception` 模块重建本地 Ultralytics YOLO、DashScope Qwen-VL 与关键帧边界，同时保留稳定 Mock 实现。

**原因：**

AI Lab 需要证明真实能力可接入，但固定 Scenario 必须可在无权重、无 API Key、无网络的现场稳定演示。

**对后续开发的影响：**

- 仅当本地模型权重与 DashScope Key 均存在时显示 `REAL AI MODE`；
- REAL 推理错误必须显式返回，禁止伪装为成功或 Mock；
- AI Lab 输出只返回结构化感知与 Task Profile，不得自动创建事件、调度或控制机器人；
- REAL / MOCK 必须经过同一 `ai-lab.v1` 输出契约，并由同一 Phase 3 Capability Engine / Scheduler 仅做非持久化预检；
- Camera → SLAM 必须调用 Phase 2 `map_pixel_to_slam`，不得在 AI Lab 复制第二套坐标换算；
- 日后找到 V1，只能替换适配器内部实现或提供权重 / Prompt 参考，不得改变 API 与模式边界。

---

## 决策 22：客户工作台只编排既有引擎，真实场景素材不得伪造

**最终决定：**

Phase 8 默认进入中文业务工作台。它通过产品化适配层编排 `ai-lab.v1`、Multi-view Agent、Camera → SLAM、Scheduler、Robot Adapter 与 Verification，不增加第二套 AI、坐标映射或调度逻辑。

摄像头素材采用 `Camera + Event + View` 目录契约。四组经授权受控图片已入库；在 `DEMO MOCK MODE`，只有与清洁前资产 SHA-256 完全一致的上传才可自动匹配固定场景。未知图片不得伪造成已识别场景。Scenario 04 的大型纸箱属于 Human Fallback，未提供清洁后图时只显示待人工回传验收，禁止生成 AI 图片、渐变占位“照片”或误导性 stock 图。

**原因：**

客户第一屏首先需要理解业务闭环，但演示不能靠伪造视觉证据建立信任。

**对后续开发的影响：**

- 客户默认只看现场、AI 判断、位置、机器人、执行、验收；技术 JSON 与工具调用进入详情层；
- `map_pixel_to_slam`、Capability Engine、Scheduler、Robot-first + Human Fallback 保持唯一实现；
- 补齐素材只可添加文件，不得改写 metadata 为完整 AI 结果；
- 已完成四场景素材与浏览器验收；仍不得自行开始未定义的后续 Phase。

---

## 决策 23（SUPERSEDED）：客户首屏采用服务端指挥台读模型，不把上传入口当作产品本体

**最终决定：**

客户默认首屏必须先呈现可理解的运营全貌：Robot A/B/C 的模拟位置、状态、电量与活动，工单队列，SLAM 空间与 Camera Coverage，以及选中工单的 AI、调度、路线、验收和审计。场景选择和上传受控图片只用于创建一张新的演示工单。

新增 `operations.v1` 服务端读模型，将既有 Phase 2 空间数据和 Phase 3 审计结果投影为 `DEMO_PLAYBACK`；它不实现第二套 Scheduler、Route Planner、Camera → SLAM 或状态机。前端只能轮询该读模型，不能用本地 `setTimeout` 伪造业务推进。

**原因：**

客户需要先理解“谁在运行、有什么任务、在哪里执行、为什么这样派单”，单一上传页不能表达已完成的园区级产品能力。服务端投影同时保持演示稳定、可审计和清晰的真实 / 模拟边界。

**对后续开发的影响：**

- 所有位置、电量和状态必须标记为 `DEMO_PLAYBACK`，直到未来接入真实设备遥测；
- 真实机器人遥测可替换投影输入，但不得改变前端读模型边界；
- `start_demo.command` 必须验证 `operations.v1`，禁止复用会使前端 API 404 的旧后端；
- 未知上传图片仍然明确失败，不得伪造成识别成功。

---

## 决策 24（SUPERSEDED）：Phase 8R 以工单为核心，先只产品化 Scenario 02

**最终决定：**

客户一级导航收敛为“自主清洁工作台、工单中心、运营分析”；Phase 1–7 的技术页面保留在高级模式。`CleaningEvent / Work Order` 是系统主对象，Scenario 只用于快速创建工单。本轮仅产品化 Scenario 02，Scenario 01 / 03 / 04 不删除但等待 Scenario 02 验收后再处理。

默认客户界面只使用业务语言和七步时间线；Capability、路线、原始 JSON、Agent 工具调用、标定与 Scheduler 权重只在二级技术详情出现。

**REAL / MOCK 边界：**

- YOLO 与 Qwen-VL 只有真实配置且成功返回时才标记 `REAL`；失败必须报错，禁止降级伪装；
- 机器人、电梯、Skybridge 明确为后端驱动的 `SIMULATION`；
- Multi-view 是保留的唯一感知 Agent，Scheduler、Camera → SLAM、Heatmap 均不是 Agent；
- post-clean 不能因图片文件存在自动 PASS，必须由视觉 AI 再判断后才允许 `VERIFYING → CLOSED`；
- `.env` 与模型权重不进入 Git。`/api/system/ai-status` 只报告无密钥的配置真相。

**业务类决策：**

客户统一使用 `liquid / can / leaf / large_object / small_litter`。它们不是 stock YOLO 的原生类别承诺；`BusinessDetection` 必须同时保留 raw YOLO、VLM 与置信度来源，禁止为液体、树叶或大件伪造 YOLO bbox / confidence。

**受控回放证据：**

对经 SHA-256 匹配的四组授权图片，可以返回审阅过的框坐标以支持离线、可复现的工作台回放；其 API `source` 与 `confidence_source` 必须为 `CONTROLLED_REPLAY`，不得写成 REAL YOLO。该回放只复用既有 Camera → SLAM、Capability Engine、Scheduler 与 Verification，不创建第二套业务规则。云端 VLM 只有在本地 Key 存在时才能调用。

Qwen-VL Key 的可用性独立于本地 YOLO 权重：Key 存在时，匹配的受控主图可额外请求一次真实 Qwen-VL 作为 `cloud_review`；该复核只能补充证据，不能在没有独立验收的情况下覆盖固定场景的 Workflow、坐标映射或调度结论。

本机已用 Scenario 02 主图实际验证该边界：Qwen-VL 返回 `liquid`、0.95、`need_clean=true`。该验证不改变“检测框来源为 `CONTROLLED_REPLAY`”和“REAL YOLO 尚未验收”的既有决策。

---

## 决策 25：Custom YOLO 作为本地、独立的 Demo 数据实验，不提前接入主流程

**最终决定：**

暂停 Phase 8R REAL E2E 后，只使用用户授权的 9 张 Demo 图片训练固定五类的 nano YOLO PoC。原图、review 图和权重只保留本地；Git 只保存训练工具、配置、标注清单和报告。未经用户确认与独立验收前，不替换 Phase 8R YOLO，也不修改 UI、Scheduler、SLAM 或 Multi-view Agent。

**原因：**

当前只有 8 个正样本实例，`leaf` 为 0；这只能验证数据管线和场景可行性，不能支撑生产或 REAL E2E 成功声明。

**对后续开发的影响：**

- 必须先阅读 `docs/YOLO_DATASET_REPORT.md`；
- 只有用户明确确认结果后，才可讨论将本地 `best.pt` 配置进 REAL YOLO adapter；
- 接入后仍须单独完成 Qwen-VL、Multi-view、post-clean verification 和浏览器 REAL E2E 验收；
- 不得用低阈值或 MOCK 输出掩盖本轮 liquid/can/small_litter 漏检。

---

## 决策 26：自主清洁工作台以事件为核心的独立交互原型

**最终决定：**

新增独立路由 `/prototype`，作为面试演示前的低保真产品原型；不替换既有正式工作台，也不接入、修改或调用后端、Qwen API、Scheduler、SQLite 与现有 Agent。它以 `CleaningEvent` 为核心对象：摄像头发现的问题先形成事件；AI 确认后才形成 `RobotTask`；只有能力边界异常才形成 `Human Work Order`。

**原型交互边界：**

- 原型状态机只在前端内部推进，用来验证信息架构与演示节奏，不能被表述为正式业务执行；
- 固定摄像头、2.5D 园区调度和最近事件详情必须同屏常驻；右侧详情只保留当前或最近闭环事件；
- 单视角框及置信度来自经审核的受控演示坐标；云端综合研判为不调用 API 的原型桩，必须与框证据区分；
- 置信度门控为：YOLO ≥85 单视角复核、55–85 多视角、<55 不自动派机器人；云端综合 ≥85 自动任务、60–85 人工复核、<60 不派机器人；
- Scenario 02 必须显示 CAM-A1-01 / CAM-A1-02 / CAM-A1-04 三路低置信度证据后，由综合研判给出 91% 的非算术聚合结论；
- Scenario 04 必须进入 Human Fallback，Robot A/B/C 不移动；Robot D 仅为园区资产，不参加清洁候选；
- 现有仓库没有可用机器人实拍素材，原型必须明确显示“图片素材待补充”，不得用生成图、网络图或表情替代。

**对既有决策的影响：**

决策 23、24 的“正式客户首页读模型”“仅产品化 Scenario 02”“以 Work Order 为主对象”的产品方向已由本决策 **SUPERSEDED**。正式产品实现仍保留，待原型经人工验收后另行授权整合；本轮不回改它。
