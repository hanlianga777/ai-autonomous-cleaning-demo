# AI 自主清洁 Demo｜项目事实源

> **状态：LOCKED · 2026-08-29**
> 本文件与 `DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、`CODEX_HANDOFF.md`、`AI_INTEGRATION_TEST.md` 是后续 Codex 的唯一外部事实源。聊天记忆、旧 Prompt、旧文档片段均不具有同等优先级。

## 1. 项目定位

这是用于 AI 解决方案专家岗位面试的园区自主清洁 PoC：固定摄像头发现地面事件，边缘识别提供候选证据，云端大模型理解事件，空间映射定位，确定性能力与调度系统选择机器人，固摄验收闭环，并沉淀运营数据。

- **LOCKED**：真实项目基础与 PoC 增强必须区分；A/B 楼、电梯、空中连廊、Multi-view、异构调度与运营优化均为 PoC 设计或模拟。
- **LOCKED**：Robot-first + Human Fallback。人工不是 Scheduler 候选；大件、不可达、能力不匹配或自动处理失败时才进入人工。
- **LOCKED**：LLM/云端大模型只做事件理解、所需能力建议和验收；Robot A/B/C 的选择只来自既有 Capability Engine + Scheduler。

## 2. 当前产品信息架构

**LOCKED 一级导航**：

1. 自主清洁工作台
2. 事件中心
3. 运营分析
4. 高级模式

默认客户层使用中文业务语言：边缘识别、云端大模型、空间定位、机器人能力匹配、固摄验收、事件闭环。`YOLO`、`Qwen-VL`、`DashScope`、Scheduler、JSON、Raw 字段只允许在高级模式/技术详情出现。

当前 `/` 与 `/prototype` 均加载 `PrototypeWorkbench`，包含上述四页。该统一壳已存在，但部分页面仍是面试演示级实现，具体差距见 TODO。

## 3. 当前四组演示素材与业务边界

| Demo | 受控边缘证据 | 业务路径 | 当前真实状态 |
|---|---|---|---|
| 01 | 室外纸巾，81% | Robot A 室外清扫 → 验收 | LIVE 曾真实 CLOSED |
| 02 | CAM-A1-01 58%、02 63%、04 61%，统一“液体污渍” | 灰区多视角 → Robot B 重载清洁 → 验收 | LIVE 曾真实 CLOSED；首轮/独立复核记录见测试文档 |
| 03 | 室内易拉罐，84% | Robot C：B1 → 电梯 → B2 → 连廊 → A2 → 验收 | PARTIAL：曾完成派发，但某次真实验收未闭环 |
| 04 | 两只大型纸箱，82% | 人工工单 → 模拟人工完成 → 同机位后图 → 云端验收 | IMPLEMENTED；首轮 veto 后人工完成的真实验收曾 CLOSED |

**LOCKED**：这些红框和固定置信度是 `CONTROLLED_EDGE_DEMO` 受控边缘证据，**不是**本地真实 YOLO 权重推理。当前 Custom YOLO 数据量不足，禁止接入主流程或对外声称 REAL YOLO 通过。

Demo04 的清洁后图已提交：`sample_data/camera_events/CAM-A2-11/event-oversized-box-004/after.png`。它只移除了原画面地面的两只纸箱，且只可作为“人工完成后”的验收输入，不能表述为机器人完成大件搬运。

## 4. 云端大模型门控

**LOCKED 当前业务规则**：

- 首次云端研判 `>= 0.85`：进入后续业务判断。
- 首次研判 `0.50–0.85`：必须调用一次独立、针对性的二次复核；二次 Prompt 不携带首次答案。
- 首次研判 `< 0.50`：人工复核。
- 系统可计算与模型原始置信度分开的 `Evidence Fusion Composite Disposal Score`：`0.60 × 原始云端置信度 + 0.20 × YOLO 类别一致性 + 0.12 × 摄像头/地点/时间映射一致性 + 0.08 × 多视角一致性`。
- `need_clean=false`、`unknown` 或 `ignore` 是绝对 veto，不能通过融合分数强行派机器人。

**IMPLEMENTED（待用户最终验收）**：二次独立复核和融合分数已实现；Demo02 的首次三图 Prompt 现在明确“三张图为同地点、同一时间段、同一地面区域、三个固定摄像头”，并要求联合判断空间对齐、反光/眩光、污染真实性和清洁必要性。

## 5. 技术实现事实

- **IMPLEMENTED**：FastAPI、SQLite、React/TypeScript/Vite、Tailwind、shadcn/ui、Apache ECharts、`/api/health`、`/api/dashboard`、本地启动/停止脚本、CORS 和前端 fallback。
- **IMPLEMENTED**：6 张模拟 2D SLAM map、Global Spatial Graph、Camera Coverage、CAM-A1-01 四点映射、Dijkstra/A*、Phase 3 CleaningEvent/TaskProfile/Capability/Scheduler/SQLite 审计。
- **IMPLEMENTED**：Phase 5 Multi-view Agent 限定三个工具、最多两个补充摄像头、最多两轮迭代；不展示 Chain-of-Thought。
- **IMPLEMENTED**：每次 `demo_v1` API 运行写入 `cleaning_events` 和 transition audit；Analytics 在 30 天 300 条演示历史基线上读取这些增量。
- **IMPLEMENTED（待用户最终验收）**：客户 Demo 已改为 REST 阶段状态推进。创建、边缘、多视角、云端研判、定位、派单、导航、抵达、清洁完成、验收分别持久化；云端、Scheduler、验收均不能由更早接口提前触发。
- **IMPLEMENTED**：云端调用共用 `perception.qwen._request_qwen`；密钥只在本地环境变量，不进入 Git 或客户 UI。

## 6. 当前明确差距

- **P0 / IMPLEMENTED（待用户最终验收）**：客户工作台在每个真实后端响应后才请求下一阶段；前端短暂停顿只控制展示节奏，不预先获得最终答案。
- **P0 / IMPLEMENTED（待用户最终验收）**：空间图采用 `campusTopology` 锚点与后端 `navigation_plan.anchor_sequence`。Robot C 顺序锁定为 B1 待命→B1 电梯入口→B2 电梯出口→B2 连廊入口→A2 连廊出口→A2 易拉罐目标。
- **P0 / IMPLEMENTED（待用户最终验收）**：地图高亮、路线和移动机器人仅由 `assignment_decision.selected_robot_name` 与已生成的 `navigation_plan` 投影，不再使用 `scenario.robot` 作为实际机器人事实源。
- **P0 / PARTIAL**：Demo03 本轮真实验收返回 `retry`，正确停在 `HUMAN_REVIEW`；需要补充/优化该场景 after 素材后再争取自动闭环。
- **P1 / PARTIAL**：事件中心是独立简化详情 Drawer，不复用工作台 `EventDetailPanel`；筛选、字段和异常视图未满足锁定规格。
- **P1 / TODO**：运营“重新分析”是前端固定建议；工作台浮动助手不存在，运营助手也是前端固定回答，均未共用真实云端 Assistant 后端。
- **P1 / PARTIAL**：菜单、资产栏、地图文案、路线视觉及右侧详情仍需按最新锁定设计逐项浏览器复验；不要把此前 build/初始页检查误写成完整验收。

## 7. 约束

- 不引入 Docker、Kubernetes、ROS 2、Nav2/Open-RMF runtime、大型本地模型或第二套 UI Design System。
- 不改变 Robot A/B/C、Robot-first + Human Fallback、Phase 2 映射和 Phase 3 Scheduler 的业务规则，除非用户明确确认。
- 任何后续实现先读取六份事实源文档，再核对代码；每次做完更新文档与 GitHub。
