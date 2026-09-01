# AI 自主清洁与移动巡检一体化系统

> 面试架构设计唯一母文档（Markdown Source of Truth）

## 文档定位

[CONFIRMED] 本文档维护《AI 自主清洁与移动巡检一体化系统》在面试架构设计中的最新有效结论。它服务于 AI 解决方案工程师 / AI 解决方案专家面试展示，证明业务理解、AI 架构能力、机器人系统整合、产品设计、成本意识、工程可落地性与规模化能力。

本文档只管理面试架构设计，不替代 Demo 的实现、验收或运行文档。每次更新必须先完整阅读本文档；新结论应融合到对应章节，失效方案应删除，重复内容应合并。若新结论与本文档的 [LOCKED] 决策冲突，必须先提示并等待确认，不得自行覆盖。

## 1. 行业背景、客户需求与解决方案目标 [LOCKED]

本章先回答项目为何产生、客户的真实问题、传统机器人能力边界、万物云的业务基础、产品为何升级为自主清洁与移动巡检一体化系统，以及该系统最终服务的业务目标。YOLO、VLM、SLAM 等技术细节不作为本章重点。

### 1.1 行业与公司资源基础

项目不是为面试凭空设计的 Demo，而是源自大型物业客户在实际沟通中提出的业务需求。用户所在公司万物云长期服务大型物业，并通过科技能力增强物业服务、项目签约与项目竞争能力；服务场景覆盖大型产业园区、企业园区、商业空间、办公楼宇及其他大型物业项目。

万物云的优势不在于制造清洁机器人，而在于长期处于物业运营一线，同时接触客户、物业管理流程、保洁团队、安保团队、固定摄像头、园区基础设施、机器人厂商与不同机器人的实际应用情况。因此，物业科技企业更容易发现机器人本体能力与物业真实运营需求之间的断层。

万物云与多个机器人厂商存在合作关系。若形成一套可跨品牌机器人复用的 AI 自主清洁与巡检系统，便具备将客户场景、AI 能力、物业业务流程与机器人生态整合为行业解决方案的条件。

> [PUBLIC FACT CHECK REQUIRED] “行业第一”、具体客户案例或排名等对外宣传式表述，必须经万物云官网、公开新闻稿或其他公开资料验证后才能写成正式事实；本母文档不将未经核验的表述作为绝对事实。

### 1.2 客户需求与传统清洁机器人的能力断层

客户多次提出，现有清洁机器人已具备 SLAM、导航、避障、自动清洁与路线执行等成熟能力，但主要仍按固定时间、固定区域、固定路线和预设规则工作，即 Schedule-driven Cleaning。

例如，机器人每天上午 10 点清扫大厅；若 10:15 有人将饮料洒在地面，传统规则式机器人不会因为环境刚出现新的清洁需求而主动调整任务优先级。问题不是机器人不会清洁，而是机器人不知道现在什么地方最需要清洁。

传统机器人主要解决 “How to clean?”；本系统进一步解决 “When and where should cleaning happen?”：何时需要清洁、哪里需要清洁、应派哪种机器人，以及清洁是否真正完成。客户真正需要的是 Event-driven Cleaning。

### 1.3 产品创新一：从规则式清洁升级为事件驱动自主清洁

项目第一层产品创新是利用园区既有固定摄像头形成环境感知网络，并建立以下闭环：

Fixed Camera → AI Event Detection → 垃圾、污渍或清洁需求研判 → 必要时 AI Semantic Judgment → Camera-to-SLAM Coordinate Mapping → 结构化 Cleaning Task Profile → Robot Capability Matching → Deterministic Scheduling → Robot Execution → Fixed Camera After-clean Evidence → AI Verification → Closed Loop。

机器人不再只是按照既定计划执行的独立设备，而是由环境事件动态驱动的执行终端。面试核心表达为：**传统机器人重点解决“怎么扫”，本系统进一步解决“什么时候、去哪里扫”。**

### 1.4 产品创新二：机器人升级为移动视觉感知节点

在与客户及机器人厂商的进一步沟通中，机器人不再只被视为 Cleaning Robot。机器人已有 RGB Camera，且每天都会沿机器人厂商原生规则清洁路线、AI 动态清洁任务路线、正常导航路径和跨区域任务路径真实移动。

系统复用这些既有移动行为与 RGB Camera，使机器人在完成原本任务时进行 **Opportunistic Mobile Inspection（伴随式移动视觉巡检）**。这不是为了巡检再专门跑一遍路线，而是在本来就会发生的机器人移动过程中顺路完成视觉巡检，提高单位机器人资产利用率。

机器人因此具有双重身份：

- Cleaning Actuator：清洁执行终端。
- Mobile Perception Node：移动视觉感知节点。

### 1.5 Robot Edge AI Box

为实现统一接入与移动 AI 感知，机器人侧增加 **Robot Edge AI Box（机器人边缘 AI 终端）**。它不是机器人导航主控，不替代机器人厂商既有的 SLAM、底盘控制、避障、运动控制或清洁控制。

其职责分为两部分：

1. **Robot Interface Integration**：通过机器人厂商开放接口接入机器人状态、位置、电量、当前任务、任务下发、执行状态、执行结果及必要设备能力，形成跨品牌机器人的统一上层接入。
2. **Mobile Vision AI**：接入机器人自身 RGB Camera，在边缘终端部署 YOLO、专项 CV 模型与规则逻辑等适合本地运行的视觉能力，使机器人在移动途中识别物业巡检事件。

第一阶段典型场景为非机动车违停、垃圾桶周边散落垃圾、公共区域散落垃圾，以及其他适合用专项 CV 稳定识别的物业巡检事件。Robot Edge AI Box 因而同时连接机器人 Action / Status Interface 与 RGB Perception，是 **Robot Integration Gateway + Mobile Edge AI Node**。

### 1.6 Fixed + Mobile Dual Perception

系统不是单一固定摄像头架构，而是由 **Fixed Camera Perception + Robot Mobile Perception** 组成互补的双感知能力。

Fixed Camera 提供 7×24 持续覆盖、固定稳定视角、持续事件发现、清洁前后对比和最终 AI 验收；其边界是固定摄像头盲区、支路或转角等区域覆盖不足，扩大覆盖通常需要新增摄像头与施工成本。

Robot RGB Camera 随机器人持续移动，可覆盖固定摄像头无法持续观察的区域，复用既有路线顺路巡检，无需为简单巡检另增一套移动设备，并提升既有机器人资产的感知价值。

两者汇入统一事件层：

Fixed Camera Perception → Unified AI Event Layer ← Robot Mobile Perception。

正式架构概念为 **Fixed + Mobile Dual Perception**。

### 1.7 清洁事件与巡检事件必须分流

移动机器人发现事件，不等于机器人必须自己处理该事件；机器人既可以是执行器，也可以只是感知节点。**Perception ≠ Execution** 是本项目的重要产品与技术边界。

例如，机器人 RGB 通过 Edge CV 发现垃圾桶周边散落垃圾后，事件作为 Cleaning Event 进入 Capability Engine：若当前机器人具备清洁能力则执行清洁；否则由其他机器人或 Human Work Order 处理。

若发现非机动车违停，则作为 Patrol Event 进入 Property / Security Workflow，由安保或物业人员处置；机器人不负责移动非机动车。Patrol Event 是业务事件分流，不表示新增 Patrol Agent。

### 1.8 产品正式升级定位

原项目为“AI 自主清洁闭环系统”，现正式升级为：**AI 自主清洁与移动巡检一体化系统**。

推荐完整定位如下：面向大型园区物业场景，通过固定摄像头与机器人移动 RGB 视觉组成双感知网络，利用边云协同 AI 完成现场事件发现与研判，通过空间定位、机器人能力模型和确定性调度完成自主处置，并利用机器人既有移动路径进行伴随式巡检，最终形成发现 → 研判 → 定位 → 调度 → 执行 → 验收 → 运营的一体化物业 AI 闭环。

机器人正式定义保持为：**Cleaning Actuator + Mobile Perception Node**。

### 1.9 三方价值模型

本方案形成甲方客户、机器人厂商与万物云的三方价值闭环。

**甲方客户**从 Cleaning Automation 升级为 Cleaning Automation + Patrol Automation，其价值机制包括减少重复人工保洁巡查、降低部分安保人工巡检工作量、提升异常事件发现速度、提高机器人设备利用率，以及从固定计划运营转向事件驱动运营。未经真实项目数据验证，不直接宣称减少具体人数或伪造百分比 ROI。

**机器人厂商**继续提供 Robot Hardware、SLAM、Navigation、Obstacle Avoidance、Cleaning Capability 与 Device Control；本系统提供物业业务场景、AI Event Intelligence、Multi-robot Integration 与 Upper-level Orchestration。双方是 **Robot OEM Capability + Property AI Orchestration** 的协作关系，而非替代关系。潜在价值是扩大机器人项目落地、打开物业应用场景、形成头部客户标杆、增强品牌影响与增加硬件销售机会。

**万物云**不需要成为机器人制造商，其核心价值来自客户场景、物业运营能力、AI 视觉能力、现场数据与多机器人生态整合。最终销售的不是单一 Robot Hardware，而是 AI 自主清洁与移动巡检行业解决方案，形成科技物业产品能力。

### 1.10 六项总体架构目标

1. **Event-driven**：从 Schedule-driven Cleaning 升级为 Event-driven Cleaning / Inspection。
2. **Fixed + Mobile**：形成 Fixed Camera + Robot RGB Camera 的双感知网络。
3. **Robot Agnostic**：通过 Robot Adapter + Capability Profile 降低对单一机器人厂商的绑定；不同项目可采用不同数量、品牌和能力的机器人，但共享统一上层架构。
4. **AI + Deterministic**：AI 主要解决 Perception Uncertainty；Spatial、Capability、Scheduling、Route 与 Execution 由确定性算法负责，避免 LLM 控制所有环节。
5. **Cost-aware**：随着数据成熟，将已验证的高频稳定问题从 Cloud 迁移至 Edge，提高 Edge Coverage，降低 Cloud Escalation Rate 与长期 AI TCO。
6. **Scalable**：通过 Tenant Data Isolation + Authorized Capability Reuse 形成 Global Base Capability + Site-specific Adaptation，缩短新项目 Cold Start 与交付适配周期。

### 1.11 第一章最终因果链

大型物业真实场景 → 客户提出创新机器人需求 → 传统机器人仅能 Schedule-driven Cleaning → 缺乏环境事件主动发现能力 → Fixed Camera 促成 Event-driven Cleaning → 机器人从规则设备升级为动态执行终端 → 进一步利用 Robot RGB → Robot Edge AI Box → 机器人升级为 Mobile Perception Node → Fixed + Mobile Dual Perception → Cleaning + Patrol → 甲方 / Robot OEM / 万物云三方价值 → Cost-aware + Scalable AI Architecture。

## 2. 系统整体架构总览

[DRAFT] 待讨论完成后补写。

## 3. 自主清洁与移动巡检业务闭环

[DRAFT] 待讨论完成后补写。

## 4. Event 技术数据流 / 时序

[DRAFT] 待讨论完成后补写。

## 5. Edge / Cloud AI 感知架构

[DRAFT] 待讨论完成后补写。

## 6. Cloud-to-Edge Capability Flywheel

[DRAFT] 待讨论完成后补写。

## 7. Portfolio Flywheel

[DRAFT] 待讨论完成后补写。

## 8. 机器人确定性调度架构

[DRAFT] 待讨论完成后补写。

## 9. Agent 设计与边界

[DRAFT] 待讨论完成后补写。

## 10. 事件状态生命周期

[DRAFT] 待讨论完成后补写。

## 11. GitHub 模块架构与核心模块速审

[DRAFT] 待讨论完成后补写。

## 12. 成本、KPI、架构边界与面试总结

[DRAFT] 待讨论完成后补写。

## 当前进度

- 第一章：[LOCKED] 已完成。
- 第二章：[DRAFT] 系统整体架构总览，是当前唯一下一步。

## 已锁定决策

- [LOCKED] 项目正式升级为“AI 自主清洁与移动巡检一体化系统”。
- [LOCKED] Robot = Cleaning Actuator + Mobile Perception Node。
- [LOCKED] Robot Edge AI Box 是正式产品架构组成，不替代机器人厂商的导航与控制主系统。
- [LOCKED] Fixed + Mobile Dual Perception 是正式架构。
- [LOCKED] Cleaning Event 与 Patrol Event 按业务类型分流；Perception ≠ Execution。
- [LOCKED] 移动巡检不新增第三个 Agent；系统仅保留 Multi-view Perception Agent 与 Robot Operations Agent。
- [LOCKED] 六项总体架构目标已锁定。
- [LOCKED] 确定性问题使用 Workflow、Rule 或 Algorithm；仅在存在不确定性与自主工具选择时使用 Agent。
- [LOCKED] 机器人调度采用 Task Profile → Capability Engine → Hard Constraint Filter → Eligible Robots → Deterministic Scoring → Route Planning → Robot Assignment；LLM / VLM 不选择机器人。
- [LOCKED] Cloud VLM 的 Teacher Signal 不等于 Ground Truth；不采用自动无监督在线学习叙事。
- [LOCKED] 客户 Raw Data 默认隔离；只有经授权、脱敏、治理与标签统一后，才能进入 Authorized Common Dataset。

## 当前开放问题

- [OPEN] Patrol Event 与 CleaningEvent 最终是否采用统一 Event Schema。
- [OPEN] Robot Edge AI Box 的详细软件 / 硬件分层。
- [OPEN] 第二章系统整体架构如何分层。
- [OPEN] Mobile Inspection 第一阶段算法范围最终清单。
- [OPEN] GitHub 当前代码与新增面试架构概念的 Module Mapping。

## 下一步行动

只讨论第二章《系统整体架构总览》；不得自行开始撰写第二章完整内容。

## 已删除方案

- [DROPPED] AI Task Queue
- [DROPPED] Priority AI Scheduler
- [DROPPED] Cloud Burst
- [DROPPED] Cost Agent
- [DROPPED] Token Agent
- [DROPPED] Budget Agent
- [DROPPED] 默认 Local VLM
- [DROPPED] Patrol Agent
- [DROPPED] LLM Robot Scheduler
- [DROPPED] 自动无监督在线自学习
- [DROPPED] 客户 Raw Data 直接互通

## 最近一次更新时间

2026-09-02 00:14 CST
