# Codex 交接｜从这里开始

> **状态：LOCKED · 2026-08-29**
> 新 Session 必须依次完整阅读：`PROJECT_CONTEXT.md`、`DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、本文件、`AI_INTEGRATION_TEST.md`；随后检查代码、`git status`、`git log`。不要用聊天记忆补全事实。

## 当前基线与本批状态

- 仓库：`ai-autonomous-cleaning-demo`；分支：`main`。
- P0 阶段 Runtime 已实现并做过技术回归：`e6b1eb9 feat: make integrated demo stage-driven`。它不能被回退为一次性 `/runs` + 前端播放。
- 本轮仅完成 docs-only Source-of-Truth 同步；本轮新产品决策大多为 **LOCKED/TODO**，尚未修改代码。
- 下一代码工作应从 `TODO.md` 的 **P1-A 真实数据闭环** 开始，不要扩展 Event Center、Analytics、AI Assistant，也不要重做完整 Advanced。唯一允许的 Advanced 工作是在现有 shell 增加最小 AI Runtime 控制区：LIVE / Stable Replay 主动选择、云端模型可用状态、最近请求状态、最近 latency。

## 先理解的不可违反规则

1. LLM 不能选机器人；Capability Engine + Scheduler 是唯一 Robot A/B/C 选择器，人工不是候选。
2. LIVE 无云端可用时必须 Human Review，绝不 silent fallback；Replay 必须透明且不能变成固定动画。
3. 受控 bbox 不是 REAL YOLO；Demo04 after 仅表示人工清除纸箱。
4. 阶段边界：Cloud 只在 cloud-review，Scheduler 只在 assign，Verification 只在 verify/人工完成后；SQLite 记录真实状态历史。
5. 新路线必须来自 Camera→SLAM + Dijkstra global topology planner / `plan_route()`，不得以 demo_id 固定；Demo04 必须走 zero-candidate Human Fallback，不得 cloud 特判。
6. 客户地图要走唯一 MapCanvas；终态机器人不自动回出生点；历史时间轴不因 Human Review 被截断。
7. 不引入第二 UI System、Three.js、ROS/RMF、Docker/K8s、真实设备运行时或大模型权重。

## 下一实现顺序

1. `backend/demo_v1/service.py`：将 locate 接入 `spatial.calibration.map_pixel_to_slam()`；将坐标写回 CleaningEvent。
2. 同模块及共享 Fleet 读模型：用 scheduler 当前位置 + target map 调 `spatial.route_planner.plan_route()`，生成真实前端 anchor projection；将 Demo04 转为 capability 零候选。
3. `frontend/src/components/prototype/`：先做 MapCanvas 和共享 Fleet state，再做连续路线/电梯停顿/终态保留。
4. 再重构监控矩阵、真实 transition 时间轴、Multi-view 叙事和客户中文化。
5. 最后做 Demo03 ROI 验收、Replay、完整 5/5/3 回归。

## 代码定位

- Runtime：`backend/demo_v1/service.py`；API：`backend/api/routes.py`；SQLite：`backend/database/connection.py`。
- 云端：`backend/perception/qwen.py`；Multi-view：`backend/perception/multiview/`。
- 空间：`backend/spatial/calibration.py`、`backend/spatial/route_planner.py`。
- 调度：`backend/scheduling/`；前端工作台：`frontend/src/components/prototype/`。
- 当前拓扑投影：`frontend/src/components/prototype/topology.ts`，它不是最终 MapCanvas/Dijkstra Runtime。

## 验收与文档纪律

完成 P1 前须跑 `AI_INTEGRATION_TEST.md` 的 LOCKED 回归次数，记录 raw cloud、二审、Fusion、系统决策、Robot、route、验收、终态、latency。每次代码改动更新六份事实源并 commit/push；只在代码、测试、浏览器证据和用户验收都存在时，才把 TODO 变 IMPLEMENTED。
