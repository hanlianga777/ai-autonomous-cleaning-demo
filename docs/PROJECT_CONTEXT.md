# AI 自主清洁 Demo｜项目事实源

> **状态：LOCKED · 2026-08-29**
> 本文件与 `DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、`CODEX_HANDOFF.md`、`AI_INTEGRATION_TEST.md` 是后续 Session 的唯一外部事实源。必须先读完六份文件，再读代码、`git status`、`git log`；聊天记录和旧 Prompt 不可替代事实源。

## 1. 产品与本批范围

这是面向 AI 解决方案专家岗位面试的园区自主清洁 PoC：固定摄像头发现地面事件，受控边缘证据提供候选，云端模型做语义理解，确定性空间/能力/调度系统决定处置，固摄 + 云端验收形成可解释闭环。

**本批（第一部分）只聚焦自主清洁工作台和 Demo01–04**：双固定摄像头、事件详情、边缘证据、Multi-view Agent、云端研判、Camera→SLAM、Capability Engine、Scheduler、Dijkstra、机器人可视化、验收、Human Fallback、LIVE / Stable Replay。Event Center、Analytics、AI Assistant、Advanced 的完整产品化属于后续 Batch。

真实生产机器人、电梯、近同步多摄像头和生产阈值均未部署；A/B 楼、电梯、连廊与机器人执行是 PoC 模拟。受控 bbox 不是本地真实 YOLO 权重推理，禁止对外声称 REAL YOLO 已通过。

## 2. 当前已实现事实（IMPLEMENTED）

- React/Vite/Tailwind/shadcn、FastAPI/SQLite、6 张模拟 SLAM map、Global Spatial Graph、Camera Coverage、四点标定、Dijkstra/A*、Phase 3 Capability Engine + Scheduler 均存在。
- `demo_v1` 已是阶段 REST Runtime：create → edge → conditional multi-view → cloud → locate → assign → navigation → cleaning → verify；每步写入 SQLite event transition。旧 `/runs/*` 一次性入口为 410。
- 云端调用统一经 `perception.qwen._request_qwen`；灰区独立二审、Fusion、模型 veto、Demo02 首轮三图同地/同时间 Prompt 已实现。
- 当前地图只会在 `assignment_decision` 后激活相应机器人；现有 `campusTopology` 与 `navigation_plan` 可投影 Robot C 的演示路线。
- Demo01、Demo02 三次、Demo04 人工完成后曾真实 CLOSED；Demo03 曾真实选中 Robot C，但本轮验收为 `retry → HUMAN_REVIEW`。完整原始记录见测试事实源。

## 3. LOCKED 目标产品形态（尚未实现，必须进入 TODO）

### 工作台

- 横向：左侧业务主区约 72%，右侧事件详情约 28%；右侧自全局 Header 下沿开始、顶部贴齐、独立滚动。
- 左侧纵向：双固定摄像头约 31%，SLAM/空间调度地图约 69%；地图是视觉主角，摄像头是感知入口。
- 浅色企业 SaaS、低饱和蓝；删除“系统在线”和无意义装饰状态，仅保留轻量当前阶段。
- 摄像头图使用可用宽度约 90–92%、居中、`object-contain`，不拉伸/随意裁切。资产栏约 145–155px，显示透明图、中文全名、状态、电量；hover 显示坐标/楼层、服务区域、能力边界。

### 单一空间坐标与执行体验

- 白模、Topology Anchor、机器人、路线、事件 marker 必须共用唯一 **MapCanvas** 坐标系，不能相对外层 container 百分比独立定位；当前 object-contain letterbox 漂移问题尚未修复。
- Robot A 在室外道路且 100% opacity；B 在 A 栋、C 在 B 栋且约 75–85%；D 室外 100%，只作未来配送资产，不进清洁 Scheduler。
- marker 小型低饱和红色轻 pulse；路线未经过为浅灰蓝虚线 2.5–3px，已经过为低饱和蓝实线约 4px、全程 2–3 箭头；机器人必须连续插值，不能节点瞬移。
- 任务结束机器人停在终点并保留低透明路线；Demo03 即使 `HUMAN_REVIEW` 也留在 A2F。只有新 Demo 或显式“重置演示”才统一复位共享 Fleet 状态。

## 4. 四个 Demo 的锁定故事

| Demo | 锁定业务事实 | 正常目标 |
|---|---|---|
| 01 | 室外、**其他小型垃圾**、81%、Robot A、before/after | 自动闭环 |
| 02 | A1F 液体污渍；CAM-A1-01 58%、A1-02 63%、A1-04 61%；仅灰区触发 Multi-view | 联合研判后 Robot B 自动闭环 |
| 03 | A2F 地毯易拉罐；Robot C 从 B1F 经电梯、B2F、连廊至 A2F；after 有约 3m 外 Robot C | 目标 ROI 验收后闭环 |
| 04 | A2F 逃生/通道附近两纸箱、**大件物品**；A/B/C 无搬运能力 | Cloud → Locate → zero candidate → 人工 → after → AI 验收 → 闭环 |

客户业务名称固定：`small_litter → 其他小型垃圾`、`liquid → 液体污渍`、`can → 易拉罐`、`large_object → 大件物品`、`leaf → 树叶`。旧“地面纸巾”“大型纸箱”等过度具体面客类目已废弃。

## 5. CURRENT IMPLEMENTATION vs LOCKED TARGET

| 范畴 | 当前实现事实 | 锁定目标 / 差距 |
|---|---|---|
| 定位 | `locate` 当前仍主要保存模板 location | 用 bbox 地面接触点调用 `map_pixel_to_slam()`，保存 map/x/y 并驱动 marker、Scheduler、Route |
| 路径 | `navigation_plan` 当前按 Demo 演示锚点生成 | 从共享机器人当前 map + Camera→SLAM target map 调 `plan_route()`，再投影为前端 anchor path |
| Demo04 | cloud 阶段有大件直接人工分支 | 必须完成 Cloud → Locate → Capability Engine 零候选 → HUMAN_FALLBACK |
| MapCanvas | 当前有拓扑数据与 SVG 路线 | 所有动态物件必须以真实 object-contain 内层 MapCanvas 统一定位 |
| 时间轴 | 状态真实持久化已存在，但客户时间显示仍有前端假时间逻辑 | 读取 SQLite transition timestamp、真实 duration、一次平滑自动跟随 |
| Demo03 验收 | 当前整图 before/after 验收会被机器人等变化干扰 | 原目标 bbox/ROI 优先验收，必要时独立 ROI 二审 |
| Stable Replay | 旧 replay 路径存在，但不满足新定义 | 仅回放此前真实 AI 结构化证据；其余空间、调度、路线、执行、SQLite 仍真实运行 |

## 6. 不可违反边界

- Robot-first + Human Fallback；人工不是 Scheduler 候选。LLM 只理解事件/能力建议/验收，不能选 Robot A/B/C 或控制路线。
- LIVE 失败必须 `HUMAN_REVIEW`，绝不 silent fallback；Stable Replay 只能由用户在 Advanced 主动选择且要透明标识。
- 不引入第二 UI System、Three.js、ROS/RMF runtime、Docker/K8s、大型本地模型。不得修改 Robot A/B/C 定义、Phase 2 空间基础、Phase 3 调度规则。
