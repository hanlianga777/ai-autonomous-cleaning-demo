# AI 自主清洁与移动巡检一体化系统

> 面试架构设计唯一母文档（Markdown Source of Truth）

## 文档定位

[CONFIRMED] 本文档维护《AI 自主清洁与移动巡检一体化系统》在面试架构设计中的最新有效结论。它服务于 AI 解决方案工程师 / AI 解决方案专家面试展示，证明业务理解、AI 架构能力、机器人系统整合、产品设计、成本意识、工程可落地性与规模化能力。

本文档只管理面试架构设计，不替代 Demo 的实现、验收或运行文档。每次更新必须先完整阅读本文档；新结论应融合到对应章节，失效方案应删除，重复内容应合并。若新结论与本文档的 [LOCKED] 决策冲突，必须先提示并等待确认，不得自行覆盖。

## 1. 行业背景、客户需求与解决方案目标

[DRAFT] 本章整体框架已确认，待逐段正式定稿。

### 1.1 行业背景

[CONFIRMED] 项目源自大型物业客户的真实需求。传统清洁机器人通常按照固定区域、固定路线与固定时间执行，属于 Schedule-driven Cleaning；客户需要通过环境感知主动发现需要清洁的位置，并动态调度机器人处理，即 Event-driven Cleaning。

### 1.2 解决方案目标

[CONFIRMED] 系统将自主清洁与移动巡检整合为一套行业 AI 解决方案，而非单一 AI Demo。机器人在执行厂商既有规则清洁、AI 动态清洁任务和导航任务时，复用 RGB Camera 与 Robot Edge AI Box 开展伴随式视觉巡检。

### 1.3 双重机器人角色

[CONFIRMED] 机器人同时承担两种角色：

- Cleaning Actuator：执行确定性的清洁任务。
- Mobile Perception Node：在既有移动路径上补充视觉巡检能力。

### 1.4 固定与移动协同感知

[CONFIRMED] Fixed Camera 提供广域、稳定、持续的事件发现与清洁结果验收；Robot RGB 提供移动补盲与路径复用。两类感知统一汇入 Unified AI Event Layer，再分别进入清洁或巡检 / 安保工作流。

### 1.5 Robot Edge AI Box

[CONFIRMED] Robot Edge AI Box 包含两类职责：

- Robot Interface：接入机器人调度、状态、电量、位置、任务与执行结果等接口。
- Mobile AI Perception：接入机器人 RGB Camera，运行 YOLO、专项 CV 与规则，识别非机动车违停、垃圾桶周边散落垃圾、公共区域垃圾及后续适合 CV 的巡检事件。

机器人发现事件后进入统一 AI Event Layer；事件由对应业务工作流处理，而非默认由发现事件的机器人自行处理。

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

[CONFIRMED] 整体产品架构方向已确认。第一章的框架与关键结论已入库，下一步是逐段正式定稿；第二章及以后目前仅保留目录。

## 已锁定决策

- [LOCKED] 确定性问题使用 Workflow、Rule 或 Algorithm；仅在存在不确定性与自主工具选择时使用 Agent。
- [LOCKED] 系统仅保留 Multi-view Perception Agent 与 Robot Operations Agent；不新增 Patrol Agent。
- [LOCKED] 机器人调度采用 Task Profile → Capability Engine → Hard Constraint Filter → Eligible Robots → Deterministic Scoring → Route Planning → Robot Assignment；LLM / VLM 不选择机器人。
- [LOCKED] Cloud VLM 的 Teacher Signal 不等于 Ground Truth；不采用自动无监督在线学习叙事。
- [LOCKED] 客户 Raw Data 默认隔离；只有经授权、脱敏、治理与标签统一后，才能进入 Authorized Common Dataset。

## 当前开放问题

暂无已识别的未决架构问题。

## 下一步行动

逐段正式定稿第一章《行业背景、客户需求与解决方案目标》。

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

2026-09-01 23:05 CST
