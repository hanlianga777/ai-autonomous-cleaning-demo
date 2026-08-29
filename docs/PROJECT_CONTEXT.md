# AI 自主清洁 Demo｜项目事实源

> **状态：IMPLEMENTED 基线 + LOCKED/TODO · 2026-08-30**
> 本文件与 `DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、`CODEX_HANDOFF.md`、`AI_INTEGRATION_TEST.md` 是后续 Session 的唯一外部事实源。必须先读完六份文件，再读代码、`git status`、`git log`；聊天记录和旧 Prompt 不可替代事实源。

## 1. 产品目标与当前授权边界

这是面向 AI 解决方案专家岗位面试的园区自主清洁 PoC：固定摄像头发现地面事件，受控边缘证据提供候选，云端模型做语义理解，确定性空间/能力/调度系统决定处置，固定摄像头 + 云端验收形成可解释闭环。

产品由同一套 `CleaningEvent`、SQLite transition 与 Fleet / route snapshot 支撑三类页面：

- **自主清洁工作台（Workbench）**：回答“现在正在发生什么”。
- **AI 事件处置档案中心（Event Center）**：回答“一个事件如何发生、为何这样处置、如何闭环”。
- **AI 自主清洁运营分析中心（Analytics）**：回答“历史事件整体说明什么、下一步应如何优化”。

本轮是 **SOURCE-OF-TRUTH DOCS ONLY**。下列产品与架构均已讨论并锁定，但除明确标为 IMPLEMENTED 的基线外均是未来统一 implementation batch 的 `LOCKED/TODO`；本轮不授权任何前端、后端、模型、Runtime、素材或数据库改动。**Batch C / Part 3 仍待讨论，禁止自行脑补。**

真实生产机器人、电梯、近同步多摄像头、RTSP/VMS/NVR、平台授权、动态避障和生产阈值均未部署；A/B 楼、电梯、Skybridge 与机器人执行是 PoC 模拟。受控 bbox 不是本地真实 YOLO 权重推理，禁止对外声称 REAL YOLO 已通过。

## 2. 机器人命名、产品能力与 Demo 配置

内部技术 ID 固定为 `robot-a`、`robot-b`、`robot-c`、`robot-d`，客户名称不得改变内部 ID。

| 内部 ID | 客户名称 | Product Capability（公开资料可合理验证的产品定位） | Deployment Policy / Demo Configuration Capability（本 PoC 人为配置） |
|---|---|---|---|
| `robot-a` | 赛特净界 S5 | 室外道路 / 广场类清扫产品定位。 | 仅处理室外道路、广场、其他小型干垃圾和树叶。 |
| `robot-b` | 高仙 Omnie | 高能力洗扫 / 室内重清洁产品定位。 | 优先处理液体污渍、较重室内清洁；Demo02 液体污渍优先匹配。 |
| `robot-c` | 蜗小白 SC50 | 楼宇室内清洁产品定位。 | 楼栋室内轻量清洁；支持瓷砖，**本 Demo 配置为支持地毯区域轻量垃圾清洁**，处理纸屑、杯子、易拉罐、小瓶等；弱化重液体处理；允许经楼内跨层与 A2F–B2F Skybridge 执行。 |
| `robot-d` | 普渡 FlashBot Max（闪电匣 · 楼宇配送机器人） | 楼宇配送产品定位。 | 未来配送资产，`cleaning capability = none`，不参与 Cleaning Scheduler。 |

“地毯区域轻量垃圾清洁”是 Demo Configuration，不是对蜗小白 SC50 厂商原生能力的公开宣称。Product Capability 与 Deployment Policy 必须始终分开表述。

## 3. 当前已实现事实（IMPLEMENTED）

- React/Vite/Tailwind/shadcn、FastAPI/SQLite、6 张模拟 SLAM map、Global Spatial Graph、Camera Coverage、四点标定、Dijkstra global topology planner / `plan_route()`、Phase 3 Capability Engine + Scheduler 均存在。
- `demo_v1` 是阶段 REST Runtime：create → edge → conditional multi-view → cloud → locate → assign → navigation → cleaning → verify；每步写入 SQLite `CleaningEvent` transition。旧 `/runs/*` 一次性入口为 410。
- 云端调用统一经 `perception.qwen._request_qwen`；已有一次 Cloud 与独立 targeted second review/Fusion 的代码边界。`confidence >= 0.85` 不独立二审；`0.50 <= confidence < 0.85` 独立二审；`confidence < 0.50` 转 `HUMAN_REVIEW`。
- 当前 Multi-view 是受限 LangGraph 流程：仅灰区触发、受控 evidence、固定 coverage / frame / VLM 工具顺序。它不是本轮锁定的“Single-view VLM evidence sufficiency 驱动的自主工具调用”实现。
- 当前存在基础 Event Center、Analytics、Optimization、Advanced 页面/API：Event Center 是基础列表 + 独立简版详情；Analytics 使用结构化 Demo history + persisted event increment；Optimization 是确定性 mock recommendation；均不等于本文件锁定的目标产品。
- 当前地图只会在 `assignment_decision` 后激活相应机器人；现有 `campusTopology` 与 `navigation_plan` 可投影蜗小白 SC50 的演示路线。
- Demo01、Demo02 三次、Demo04 人工完成后曾真实 CLOSED；Demo03 曾真实选中 `robot-c`，但验收为 `retry → HUMAN_REVIEW`。完整原始记录见测试事实源。

## 4. 四个 Demo 的锁定故事

| Demo | 锁定业务事实 | 正常目标 |
|---|---|---|
| 01 | 室外、**其他小型垃圾**、赛特净界 S5、before/after | 自动闭环 |
| 02 | A栋 1F 高反光地面疑似液体污渍；主摄像头 `CAM-A1-01` 的受控 YOLO 58%；`CAM-A1-02` / `CAM-A1-04` 是受控补充证据资产（63% / 61%） | Single-view Cloud 判断证据是否不足；只有模型自主请求补证后才进入 Multi-view，最终由高仙 Omnie 自动闭环 |
| 03 | A栋 2F 地毯易拉罐；蜗小白 SC50 从 B1F 经电梯、B2F、Skybridge 至 A2F；after 有约 3m 外机器人 | 目标 ROI 验收后闭环 |
| 04 | A栋 2F 逃生/通道附近两纸箱、**大件物品**；A/B/C 无搬运能力 | Cloud → Locate → Capability Engine 零候选 → `HUMAN_FALLBACK` → 人工搬运 → after → AI 验收 → CLOSED |

客户业务名称固定：`small_litter → 其他小型垃圾`、`liquid → 液体污渍`、`can → 易拉罐`、`large_object → 大件物品`、`leaf → 树叶`。旧“地面纸巾”“大型纸箱”等过度具体面客类目已废弃。Demo01 的 LIVE confidence 不是锁定业务事实；历史 `.81 → .95 → Fusion .89` 仅能在 `AI_INTEGRATION_TEST.md` 中作为历史记录出现。

## 5. LOCKED 产品结构（尚未实现，必须进入 TODO）

### Workbench 与统一 Event Detail

- 左主区约 72%、右事件详情约 28%；左上双固定摄像头约 31%、SLAM/空间调度地图约 69%。地图是视觉主角，摄像头是感知入口；右详情从全局 Header 下沿开始、顶部贴齐、独立滚动。
- 白模、Topology Anchor、机器人、路线、事件 marker 必须共享唯一 **MapCanvas** 坐标系，基于 `object-contain` 内层真实画布；不能以外层 container 百分比独立定位。
- `EventDetailPanel` 是全产品唯一事件详情标准：`mode="live"` 动态跟随 Runtime，`mode="history"` 只读展示事件发生当时 snapshot，绝不重跑模型、Scheduler 或机器人；字段、卡片、图片、顺序、颜色和 stage hierarchy 一致。

### Event Center

定位为 **AI Event Handling Archive Center / AI 事件处置档案中心**，不是普通告警列表。复用同一 `CleaningEvent` / SQLite，不得维护独立 Mock 数据。主状态固定为：全部、处理中、已自主闭环、待人工处理、异常；正常 `HUMAN_FALLBACK` 是合理业务兜底，绝不是异常。详情从紧凑两级 Event List 右侧以约 42–46% 宽历史 `EventDetailPanel` 打开；`/events?event=EVT-xxxx` 保存选中状态，刷新可恢复，首次进入不自动打开第一条。

### Analytics

定位为 **AI Autonomous Cleaning Operations Analysis Center / AI 自主清洁运营分析中心**，而非传统物业驾驶舱。三层是 Autonomy Outcome、Operational Efficiency、Optimization Advice；顶部 5 KPI 固定为自主闭环率、人工介入率、首次处置成功率、平均响应时间、平均闭环时间，均由后端 `CleaningEvent` / transition 真实计算。主视觉是复用园区/SLAM white model 的 30 天空间事件热力图，数据源为明确标识的“30 天结构化 Demo Historical Baseline + 当前 Runtime CleaningEvent Increment”，不能冒充客户真实历史。

### Robot Operations Agent

唯一的运营与自然语言任务编排层：Workbench / Event Center 使用同一个可拖动 Floating Window；Analytics 改用右侧固定 Agent Panel；三页共享 `AgentSession`、Action Audit、Task context，只随 Page Context 改变呈现。它有任务级自主权，不具有基础设施级配置权；具体界限见 `DECISIONS.md` 与 `ARCHITECTURE.md`。

## 6. CURRENT IMPLEMENTATION vs LOCKED TARGET

| 范畴 | 当前实现事实 | 锁定目标 / 差距 |
|---|---|---|
| 定位 | `locate` 主要保存模板 location | bbox 地面接触点调用 `map_pixel_to_slam()`，保存 map/x/y 并驱动 marker、Scheduler、Route |
| 路径 | `navigation_plan` 当前按 Demo 演示锚点生成 | 共享机器人当前 map + Camera→SLAM target map 调 Dijkstra global topology planner / `plan_route()` |
| Multi-view | YOLO/受控置信度灰区会进入固定工具流程，初轮可使用三图上下文 | Single-view Cloud VLM 先判断 `evidence_sufficient` / `ambiguity_type`；模型以 `tool_choice=auto` 自主选择 1–2 路补证，最多 2 轮 |
| Demo04 | cloud 阶段有大件直接人工分支 | Cloud → Locate → Capability Engine 零候选 → `HUMAN_FALLBACK` |
| Event Center | 基础列表与独立简版 detail | 紧凑 archive list + 同一 `EventDetailPanel(mode="history")` + URL state + 正确状态分类 |
| Analytics | 存在演示历史聚合、固定利用率/建议和基础图 | 可追溯的 KPI、Heatmap、drill-down、真实 increment、无虚构 trend / utilization |
| Optimization / Agent | 现有 Optimization 是确定性 mock recommendation；无 Robot Operations Agent | 一个具白名单工具、Policy Guard、Action Audit、Observe/Replan/Close 的 Agent |
| MapCanvas / Fleet | 有拓扑数据、SVG 路线和 presentation-only playback | 所有动态物件统一 MapCanvas；共享 Fleet 终态、真实 transition 时间、连续路线 |
| Stable Replay | 旧 replay 路径存在，不满足新定义 | 仅回放真实 AI structured evidence；其余空间、调度、路线、执行、SQLite 仍真实运行 |

## 7. 不可违反边界

- Robot-first + Human Fallback；人工不是 Scheduler 候选。LLM 只理解事件/能力建议/验收，不能选 `robot-a` / `robot-b` / `robot-c` 或控制路线。
- LIVE 失败必须 `HUMAN_REVIEW`，绝不 silent fallback；Stable Replay 只能由用户在现有 Advanced shell 的最小 AI Runtime 控制区主动选择且透明标识。该控制区仅包含 LIVE / Stable Replay 主动选择、云端模型可用状态、最近请求状态和最近 latency；Advanced 完整产品化仍属于后续 Batch。
- Event Center、Analytics、Workbench 必须使用同一 CleaningEvent / SQLite；历史详情必须读取历史 snapshot，不能被当前 Fleet 覆盖。
- 不引入第二 UI System、Three.js、ROS/RMF runtime、Docker/K8s、大型本地模型。不得修改 `robot-a` / `robot-b` / `robot-c` 的内部 ID、Phase 2 空间基础、Phase 3 调度规则。
