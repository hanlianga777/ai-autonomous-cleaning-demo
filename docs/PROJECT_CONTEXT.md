# AI 自主清洁 Demo｜项目上下文

> **Post-merge Interview Freeze · 2026-08-30**
> Unified Implementation merge baseline: `8341eb079fe5a700b4931e0112fdbe5552297785`
> Current main HEAD: 以 GitHub main / `git rev-parse HEAD` 为准
> `codex/unified-implementation` / `bdd08e02e0e4fc96d9ad6229949f2c8bf3812136` 是已合并的历史实施线，不是当前基线或工作分支。

## 产品目标

这是一个面向 AI 解决方案专家岗位展示的园区自主清洁 PoC：固定摄像头发现问题，受控边缘证据提供候选，云端视觉模型完成语义与验单，确定性空间/能力/调度系统完成处置，全部过程写入同一 SQLite 并可追溯。

四个一级页面是 Workbench、Event Center、Analytics、Advanced。它们共享 `CleaningEvent`、transition、Fleet、route 和 trace 事实，不维护第二份业务状态。

## 已实现架构

- **阶段 Runtime**：`demo_v1` create → edge → cloud review（single-view → evidence sufficiency → conditional multi-view → final disposition）→ locate → assign → navigation → cleaning/human completion → verify。旧 `/api/demo-v1/runs/*` 为 410。
- **空间/调度**：Camera→SLAM 四点标定、6 张模拟 SLAM Map、Global Spatial Graph、Dijkstra `plan_route()`、Capability Engine 与 Scheduler。机器人选择只由 Capability + Scheduler 完成。
- **两类 Agent**：Multi-view Perception Agent（Coverage、Evidence Fetch、VLM；最多两路/两轮）与 Robot Operations Agent（受限任务工具）。没有第三个独立运营分析 Agent。
- **产品事实**：Demo04 是待清运大件废弃物，Cloud 只判断需处置；Capability zero candidate 才能产生 HUMAN_FALLBACK。task-owned 人工完成受 session + lease 唯一 owner 保护。
- **验单**：同源 target ROI 用于 before/after；primary verifier 失败最多一次独立 ROI review，schema/bbox/raw float/Replay 均 fail closed，Analytics 不把 ROI 二审改写为 primary first-pass。
- **可观测性**：Advanced 只投影保存的 event、request、tool、trace、spatial、capability、assignment、route 和 verification，不运行新的模型或调度。

## 当前客户资产

| Internal ID | 客户名称 | 当前 Demo 定位 |
| --- | --- | --- |
| `robot-a` | 赛特净界 S5 | 室外小型干垃圾/道路清扫 |
| `robot-b` | 高仙 Omnie | 室内液体重污/洗扫 |
| `robot-c` | 蜗小白 SC50 | 室内轻量垃圾；本 PoC 配置允许地毯区域 |
| `robot-d` | 普渡 FlashBot Max | 配送 PoC；不参与 Cleaning Scheduler |

Demo01 为室外其他小型垃圾；Demo02 为液体污渍和多视角证据不足；Demo03 为跨楼地毯易拉罐；Demo04 为人工搬运的大件废弃物。

## 当前工程证据

- Unified Implementation 已 merge 到 main：A/B/C/D/E/F/H/G 均 IMPLEMENTED。
- 正式 LIVE：Demo01 5/5、Demo02 5/5、Demo03 5/5、Demo04 3/3。
- post-review Stable Replay：四个 Demo 各 3/3，统一 fingerprint，Replay 无新 Cloud request，非 AI Runtime 仍重新运行。
- 后端 164：161 PASS + 3 paid opt-in skipped；前端 46 PASS/build PASS；bash-n/diff check PASS；Reviewer A/B/C/D/E 均 PASS，P0/P1=0。
- 用户主观展示验收仍 pending，不能由工程证据替代。

完整安全数值、事件 ID、请求 timing 与历史失败记录见 `AI_INTEGRATION_TEST.md`；不要把历史 confidence 作为未来 Runtime 固定值。

## Reality Boundary

| 类别 | 当前事实 |
| --- | --- |
| LIVE MODEL | `qwen-vl-max` 语义/验单，`qwen3-vl-plus` 多视角 tool calling。 |
| DETERMINISTIC RUNTIME | Camera→SLAM、Capability、Scheduler、Dijkstra、SQLite transition。 |
| CONTROLLED EVIDENCE | Bbox 和图像资产；它们不是本地 REAL YOLO。 |
| POC SIMULATION | 机器人移动、电梯/连廊、配送；不等同真实 telemetry 或平台接入。 |

## P2 / 未实现

真实 ASR、机器人、RTSP/VMS、生产身份和授权、外部配送平台、分布式 queue、ROS/Nav2、生产 availability/uptime、长期审计与跨服务 tracing 尚未实现。构建包拆分不是本轮阻塞项。

## 当前授权

**没有新的授权阶段。** 当前处于 Interview Freeze：只接受用户明确授权的修复或展示调整；不得偷偷扩展 Runtime、Scheduler、Agent 或空间业务规则。
