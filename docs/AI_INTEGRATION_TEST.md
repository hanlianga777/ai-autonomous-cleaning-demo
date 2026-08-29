# Integrated Demo｜AI 集成与回归事实记录

> **状态：IMPLEMENTED 基线 + LOCKED/TODO 验收计划 · 2026-08-29**
> 本文区分已发生的真实调用、当前已实现边界和下一轮必须达到的验收标准。固定 bbox 仍是 `CONTROLLED_EDGE_DEMO`，不是本地 REAL YOLO。

## 1. 当前 AI / Runtime 事实（IMPLEMENTED）

- 云端 transport 唯一入口为 `perception.qwen._request_qwen`；密钥只在本地环境变量。
- 首轮 `run_event_qwen_vl`：`confidence >= 0.85` 时不触发独立二审，进入系统 Fusion / 业务判断；`0.50 <= confidence < 0.85` 时调用 `run_targeted_event_qwen_vl` 独立二审，二审不接收首轮答案；`confidence < 0.50` 时进入 `HUMAN_REVIEW`。
- Fusion 公式为 `0.60 raw cloud + 0.20 category + 0.12 camera/location/time + 0.08 multiview`；明确 veto 不被融合覆盖；通用 raw next_action 不负责系统派单。
- Cloud 只在 cloud-review，Scheduler 只在 assign，Verification 只在 verify/人工完成后。LIVE 不可用时停止在 Human Review，无 silent replay。
- Demo02 初轮三图 Prompt 已明确：同一物理地面、同一时间窗、三个固定摄像头、一个事件；联合判断对齐、反光、污染真实性、是否需清洁。

## 2. 真实历史记录（不可当作未来成功保证）

| 日期 / 代码 | Case | 结论 |
|---|---|---|
| 2026-08-28，旧单次门控 | Demo01–04 | 历史结果，不适用于独立二审/Fusion/阶段 Runtime 验收 |
| 2026-08-29，`e6b1eb9` | Demo01 | 首轮 `.81`、二审 `.95`、Fusion `.89`、Robot A、验收 `.95`，CLOSED |
| 同上 | Demo02 #1/#2/#3 | 真实执行 Multi-view Agent workflow（使用受控多视角证据资产）；均 Robot B + CLOSED；首轮 `.85/.75/.85`，仅 #2 二审 `.95`，Fusion `.91/.97/.91` |
| 同上 | Demo03 | Robot C 被选、完整演示锚点路径；验收 `retry`，HUMAN_REVIEW |
| 同上 | Demo04 | cloud large_object 后人工完成、验收 `.98`，CLOSED；但其 cloud 直接人工分支已被新 LOCKED 目标替代 |
| 同上 | cloud unavailable | `HUMAN_REVIEW`，无 assignment/verification |

这些结果证明 transport、阶段边界和部分真实调用存在；不证明本地 YOLO、真实生产设备、MapCanvas、Camera→SLAM Runtime、Dijkstra Runtime、Demo03 ROI 验收或 Stable Replay 已完成。

## 3. LOCKED 测试语义

- **LIVE**：真实云端模型请求；失败必须可见并停在 `HUMAN_REVIEW`，不得自动切换 replay。
- **Stable Replay（TODO）**：只允许使用过去真实成功调用保存的结构化 AI 响应；Camera→SLAM、Scheduler、Dijkstra、机器人移动、SQLite transitions、验收流程仍需现场运行。
- **Demo03 verification（TODO）**：是目标 ROI 任务，不是整图找不同。输入原类别、bbox/ROI、before/after 全图和 ROI；机器人、人员、阴影、光照、无关变化不能单独导致失败。因非目标干扰失败时独立 ROI 二审，不读取第一次答案。
- **Demo04（TODO）**：必须验证 Cloud → Locate → Capability Engine zero candidate → HUMAN_FALLBACK → 人工完成 → after → 云端验收，不允许按 Demo ID 或 cloud 直接跳人工。

## 4. 下一代码阶段强制回归标准（LOCKED / TODO）

| 模式 | 场景 | 次数与通过条件 |
|---|---|---|
| LIVE | Demo01 | 连续 5 次，至少 4 次 Robot A → verify → CLOSED |
| LIVE | Demo02 | 连续 5 次，至少 4 次真实执行 Multi-view Agent workflow（使用受控多视角证据资产）→ Cloud → Robot B → verify → CLOSED |
| LIVE | Demo03 | 连续 5 次，至少 4 次 Robot C → Dijkstra global topology planner / `plan_route()` 跨楼/电梯/连廊 → ROI verify → CLOSED |
| LIVE | Demo04 | 连续 3 次，全部 Cloud → Locate → zero candidate → Human → verify → CLOSED |
| Stable Replay | 四个 Demo | 每个连续 3 次，100% 正确流程；不得跳过非 AI Runtime |

每次必须记录：run id / commit、模式、时间；raw cloud confidence；是否二审及二审 confidence；Fusion/composite score；系统决策；selected robot；Dijkstra global topology planner / `plan_route()` route；verification raw result；最终状态；每个云端请求 latency。主场景合理业务成功率低于约 80% 时，先调查 Prompt、ROI、ontology、输入上下文、parser、模型/系统决策分离，而不是仅称“随机”。

## 5. 当前限制与禁止性结论

- 当前不宣称 REAL YOLO、生产多机位同步、真实机器人遥测、真实电梯或生产阈值。
- 旧 Stable Replay 不能被叫作完整稳定回归，直到满足本文件第 3 节定义。
- Demo03 目前的 `retry` 必须如实保留；不能通过 Demo ID 特判或写死 PASS 修复。
- 本轮是 docs-only；没有运行新的代码、模型、浏览器或 API 测试。
