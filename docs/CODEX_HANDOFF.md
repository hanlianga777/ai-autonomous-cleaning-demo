# Codex 交接｜从这里开始

> **状态：LOCKED · 2026-08-29**
> 新会话必须先完整阅读以下六份文件：
>
> 1. `docs/PROJECT_CONTEXT.md`
> 2. `docs/DECISIONS.md`
> 3. `docs/TODO.md`
> 4. `docs/ARCHITECTURE.md`
> 5. 本文件
> 6. `docs/AI_INTEGRATION_TEST.md`
>
> 随后再查看代码、`git status` 和 `git log`。不得依赖聊天上下文猜测项目状态。

## 当前仓库基线

- 项目：`ai-autonomous-cleaning-demo`
- 分支：`main`
- 本轮 Context Governance 前基线：`3b886e7 feat: complete integrated cleaning demo v1`
- 客户入口：`/` 与 `/prototype`，均为四页 CleanOps 壳
- 未进入新的功能 Phase；当前应该先处理 `TODO.md` 的 P0，而不是继续扩展功能。

## 不可违反的规则

1. 客户一级导航固定为：自主清洁工作台、事件中心、运营分析、高级模式。
2. 客户层不用 YOLO/Qwen/DashScope/Scheduler/Raw JSON 术语；高级模式才可以。
3. 受控 bbox 是 `CONTROLLED_EDGE_DEMO`，不是当地 YOLO 推理；失败的 Custom YOLO 权重不得接入。
4. 云端大模型只输出语义和验收；Capability Engine + Scheduler 唯一选择机器人；保持 Robot-first + Human Fallback。
5. 灰区二次复核必须独立，不能带首轮答案；模型 veto 不得被融合分数覆盖。
6. Demo04 after 图仅代表人工移除纸箱后的验收，不代表机器人搬运。
7. 不擅自修改 Phase 2 映射、Phase 3 Scheduler、Robot A/B/C 定义或扩展 Robot D 业务。
8. 不引入第二 UI 系统、ROS/RMF runtime、Docker/K8s、大型本地模型。

## 代码定位

- 客户壳：`frontend/src/components/prototype/PrototypeWorkbench.tsx`
- 监控/bbox：`CameraMonitorGrid.tsx`、`CameraViewport.tsx`、`data.ts`
- 右侧详情：`EventDetailPanel.tsx`
- 客户地图：`SpatialDispatchView.tsx`
- 组合层：`backend/demo_v1/service.py`
- 云端 transport/prompt：`backend/perception/qwen.py`
- 空间单一实现：`backend/spatial/`
- 调度单一实现：`backend/scheduling/`
- 事件持久化：`backend/database/connection.py`

## 下一步

只在用户授权实现后，先完成 `TODO.md` 的 P0：真实逐阶段状态、真实 assignment 驱动、拓扑路由投影、Demo02 首轮 Prompt、真实重新回归。实现前先提出或更新计划；完成后必须同步六份事实源并 commit/push。

## 已知真实测试结论

历史测试和当前实现状态必须阅读 `AI_INTEGRATION_TEST.md`。2026-08-28 的单次门控测试已经过期为 **Historical Result**；其数值不能当作二次复核/融合逻辑的当前验收。2026-08-29 有真实 run 记录，但仍不是完整新的四场景正式回归；细节同样见测试文档。
