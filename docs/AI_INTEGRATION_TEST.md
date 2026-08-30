# Integrated Demo｜AI 集成与回归事实记录

> **状态：IMPLEMENTED 基线 + LOCKED/TODO 验收计划 · 2026-08-30**
> 本文区分已发生的真实调用、当前代码边界和未来必须达到的验收标准。固定 bbox 仍是 `CONTROLLED_EDGE_DEMO`，不是本地 REAL YOLO。

## P1-D 档案验收（IMPLEMENTED · A/E PASS · 2026-08-30）

- Backend `tests.test_event_archive` 7/7：正常 Human Fallback、人工闭环非自主闭环、语义复核/系统错误区分、自主闭环要求 robot+verification、发现时间/分页/搜索/UTC/分类计数、非法筛选、历史不读当前 Fleet 且不写 event/transitions。
- 完整后端 96 项：93 PASS + 3 paid opt-in skipped。本阶段不改变 P1-C 模型算法或重跑付费测试；保留之前真实 LIVE 证据。
- 浏览器使用隔离 QA SQLite 中真实 P1-C LIVE `integrated-demo02-16d3080c0e` 与 Replay `integrated-demo02-dbe74999b0`：档案首访未选中、点击/刷新 URL 恢复同一事件、完整 history 时间线、无自动滚动/模型 POST、当前 Fleet 不覆盖历史。缺失 ID 明确报错；错误日期 API 返回 422；右详情固定44%并内部滚动。
- 浏览器新增 `integrated-demo03-545dc25681`（仅 DETECTED）后出现“有1条新事件”，已选LIVE详情/URL不变，未运行新模型或调度。
- 额外接口诊断事件 `integrated-demo01-3c39fda3b8` 显式 simulate_unavailable，验证系统异常分类，不宣称真实云端成功。待处理诊断 `integrated-demo04-6154b901d7` 仅创建 DETECTED，未冒充 Human Fallback 或 CLOSED。
- A 的事件切换 ID 错配 P1 已用 identity guard 修复；列表 in-flight guard、UTC筛选、分页新条目计数、可访问标签纳入回归。前端档案7/7、全量24/24、production build与diff check PASS。Reviewer A/E 最终PASS，P0/P1=0；D审查P2类型/分页/可访问标签也已修复，不新增未解决D核心问题。

## P1-C 实跑与对抗验收（2026-08-30，IMPLEMENTED · Reviewer A/E PASS）

- 自动化：`python -m unittest tests.test_autonomous_multiview tests.test_perception_records tests.test_p1c_pipeline -v`：22 PASS；严格 provider schema/内部 projection、低 confidence不足优先补证、最终不足/低 confidence失败、合法二审输入隔离、两camera/两round、坏tool、Replay重跑 Coverage/Fetch、安全失败均覆盖；修改 Agent system prompt、tool schema/description 或 budget 后，旧记录不可重用。
- 完整后端 `python -m unittest discover -s tests -q`：89 tests，86 PASS + 3 paid opt-in skipped；前端 `npm test` 17 PASS、`npm run build` PASS；`git diff --check` PASS。
- 实际型号检查：单视角现配 `qwen-vl-max`；图像+function calling 使用 `DASHSCOPE_AGENT_MODEL=qwen3-vl-plus`。真实 image + auto-tool probe 返回工具调用，耗时 3081ms。依据[阿里云 Function Calling 官方说明](https://help.aliyun.com/zh/model-studio/qwen-function-calling)，未创建第二 provider/SDK，也未写入或暴露 API Key。
- 旧主图真实尝试：`fc8bc25eb3` 与 `9818e95f7f` 均 single .85 / sufficient=true，未触发 Agent，Fusion .83→HUMAN_REVIEW；试 `qwen3-vl-plus` 的 `6b33734fbf` 为 .75/sufficient=true，独立二审 .75，Fusion .77→HUMAN_REVIEW。该图液体边缘清晰，不能为了 demo 强迫不足。
- 新受控模糊版首次 `5008bfedef`：single .30/insufficient/reflection→真实 find→自选CAM-A1-02 fetch→final .85/sufficient。旧代码仍按“2额外摄像头”才计 multiview consistency，Fusion .83→HUMAN_REVIEW；随后修复为“主图+≥1合法成功fetch”，没有改权重、阈值或模型输出。
- opt-in `RUN_P1C_LIVE_ACCEPTANCE=1 python -m unittest tests.test_p1c_live_acceptance -v`：1 PASS，23.311s。LIVE `integrated-demo02-43d9d933e5`：single .30、insufficient/reflection→find(2240ms)→模型自选CAM-A1-02 fetch(2570ms)→finish(7735ms)，1 round、final .85、Fusion .91、robot-b、verification .95→CLOSED。Replay `integrated-demo02-a53f4b66dd` 禁止 `_request_qwen` transport 仍 CLOSED，工具重新执行/新审计时间、历史 model latency、本次 model elapsed=null；不是整段录像。
- 实际浏览器 localhost:5174→隔离后端8001：LIVE `integrated-demo02-16d3080c0e` single .30/insufficient→auto find(1912ms)/fetch CAM-A1-02(2077ms)/finish(7349ms)→final .92/Fusion .952→Omnie→verification .95→CLOSED。显式点 Advanced Stable Replay 后 `integrated-demo02-dbe74999b0` 亦 CLOSED；页面明确 REPLAY/工具重新执行、仍显示单视角/完整工具与能力派单/路线/after/Fleet终点。顶部仍主相机+空闲相机，不被补图替换。02:00 UTC 后 Console error=[]。
- Reviewers：A Architecture/Runtime PASS（P0=0/P1=0），E Adversarial QA PASS（P0=0/P1=0）；文档复核在提交前完成。P2：模型turn保护上限与acquisitionround口径须保持清晰。上述数字都是历史真实测试结果，不是未来 Runtime 固定值。
- 提交前 Replay key 补齐 Agent system prompt/tool schema-description/budget 后，再次实际执行 opt-in：1 PASS / 21.138s；LIVE `integrated-demo02-e5c21bbe3f` .30 insufficient→find 1930ms→fetch CAM-A1-02 2015ms→finish 7122ms→.85/Fusion .91/robot-b/verification .95/CLOSED；禁 transport Replay `integrated-demo02-df41e9b856` 亦 CLOSED。

### Demo02 evidence variant 来源与编辑提示

新增 `sample_data/camera_events/CAM-A1-01/event-beverage-spill-002/primary-ambiguous-v2.png`；原 `primary.png`、两张 supporting/after 保留。built-in image_gen 在原构图上增加局部半透明镜头模糊/反光，保留归一化 ROI/机位；删除原图不一致的内嵌 camera 字样，camera identity 仍来自 metadata。源码 metadata 明确 CONTROLLED EVIDENCE/生成方式/日期；不是生产摄像头故障数据、不是模型响应或检测框。仅当真实模型判不足才补证。完整编辑提示如下（此提示只用于生成受控测试图，**不传给运行中的 VLM**）：

> Use case: lighting-weather / precise camera imaging edit. Image 1 is the edit target, a CONTROLLED SYNTHETIC CCTV test asset for a transparently labeled multi-view perception demo. Create ONE version of exactly this camera frame, same 4:3 aspect ratio, identical viewpoint, room geometry, floor tile lines, glass entrance, and location of the tiny yellowish patch near normalized x=.50,y=.52. Change ONLY camera optical visibility: a localized soft translucent lens smear / diffuse reflected glare across the central region makes the patch and its boundaries genuinely indistinct. It should no longer be visually possible to confidently distinguish actual liquid on the floor from a reflection or lens contamination using this single frame alone. Keep a faint ambiguous patch in its current spot, do NOT draw a clearly outlined puddle, cup, boxes or extra objects. The surrounding room and floor outside this localized hazy glare remain naturally sharp. This is an optical ambiguity TEST INPUT, NOT model output or a fake detection result. No boxes, no confidence numbers, no annotations, no model answers, no new text. Remove the existing small black timestamp/camera text strip and reconstruct background there, because camera identity/timestamp are supplied as separate factual metadata. Do not move, crop, or redesign the scene.

P1-C 并不代替 P1-G：连续5次至少4次成功、四场景Repeat/完整Analytics/Operations/Advanced验收仍待后续。

## 1. 当前 AI / Runtime 事实（IMPLEMENTED）

### 2026-08-30 P1-B 浏览器与前端工程验收（IMPLEMENTED · Reviewer A/E PASS）

P1-A 已提交推送 `fcd01d4`。P1-B 本次仅前端与文档改动，不修改模型返回、Capability/Scheduler、SLAM 或 Cloud gate。测试环境为独立临时 SQLite 后端 `127.0.0.1:8001` 与 Vite `5174`；没有往日常数据库写 fixture。

- 前端 `npm test` **17/17 PASS**：7 空间/路径、6 时间线/监控、4 session 恢复。包含缺/未知 route 不画假线、拐点、电梯入口 1 秒停留、terminal 精确终点、history 不补 pending、四 Demo 主相机 before/after、Demo02 supporting 不进入顶栏、缺资产不捏造、GET 404、同会话防重复与倒退/外来快照拒绝。
- `npm run build` PASS；完整 backend `unittest discover -s tests -q` **Ran 66 / 64 PASS + 2 opt-in skipped**；P1-A 真实 opt-in 已在上一阶段另行跑过。`git diff --check` PASS。
- 主代理使用 Codex in-app 实际浏览器，不以 build 代替浏览器：1440×900 的主区/详情约 72/28、相机/地图约 31/69，资产栏 152px；1024×768、1920×1080 无水平溢出。1920 视口下白模和内层 overlay DOM 矩形完全相同（1058.48×595.70），letterbox 未改变坐标系统。
- Demo04 `integrated-demo04-acebb0e0c9`：LIVE 首轮 .95、Fusion 89分、Locate→zero candidates→HUMAN_FALLBACK→用户人工完成→真实 verification .98→CLOSED。history 保留 7 条阶段（含 LOCATED/HUMAN_FALLBACK/VERIFYING），scrollTop=0，无人工完成按钮；打开档案只有 GET，没有模型/调度 POST。
- Demo03 `integrated-demo03-ec4c7f8201`：LIVE .92、Fusion 87分、候选 robot-c、B1F→电梯→B2F→Skybridge→A2F；导航从 01:22:28 UTC 至 01:22:36 UTC 后才提交到达。真实 verification_pass=false / confidence=.95，正确转 HUMAN_REVIEW，10 条阶段不截断，after 与终态路线保留。**这不是 Demo03 最终闭环通过**，仍待 P1-G 的目标 ROI 验收优化；未改模型回答。
- Demo03 刷新前后机器人视觉落点 `(33.664%,27.8536%)` 与完整 SVG route path 完全一致；Fleet 仍在 A2F、电量 89%，没有回到 B1F 基线。
- Demo04 `integrated-demo04-6b02cb6896`：在真实 cloud-review 处理中刷新；服务访问日志证明该事件 cloud-review 只有 1 次 POST，刷新后 GET 读取 SQLite，再继续 locate/assign 至 zero-candidate HUMAN_FALLBACK。只验证同会话防重复，未声称跨新标签页幂等。
- 浏览器发现并修复过 route Hook 等值数组引发的 maximum update depth、UTC 解析导致瞬间完成、已走路线拐点丢失；最终检查无新运行时错误。空间面板有独立错误边界，故障不清空工作台。

Reviewer A / E 均 PASS，P0/P1=0（限 P1-B）；未知语义中文待复核、网络结果不确定只读同步、session keys 清理/跨页全局幂等为 P2/后续。该段为 P1-B 当时的记录；P1-C 新 Agent 当前已完成（见本文最新记录），P1-D 完整事件列表已实现；P1-E/F/H 与最终多次 LIVE 稳定性仍未实施/验收。

### 2026-08-30 P1-A Closure 最新验收（IMPLEMENTED · Reviewer A/E PASS）

- 用户确认 Demo04 两箱是废弃待清运，不是合法暂存/补货/待使用物资。源 metadata 的 zone_type/storage_policy/object_context/context_scope/context_source/context_confirmed_at 经 Scenario manifest 和匹配 camera 的 operational_context 进入一/二审，cloud_context 写入事件。未向模型传 expected_robot / HUMAN_FALLBACK 预期，也未改变 veto/Scheduler；模型仍可依据图像否决。
- 最新真实 opt-in LIVE suite：**2/2 PASS**。Demo01 cloud `.95` / verify `.95`；Demo04 cloud `.95` / verify `.98`。各自持久化一条 event review、一条 verification record，并完成 Stable Replay CLOSED（Replay 期间阻止全部云端 transport，无新 LIVE call）。Demo04 LIVE/Replay 均经过 Locate→Camera→SLAM→Capability candidate_count=0→HUMAN_FALLBACK→human completion→after evidence→verification→CLOSED。
- 新增 context 回归三项：真实 adapter 构建的一/二审请求包含 scoped context 且无期望人工/先前答案；context 不覆盖 model false/ignore；context 变化拒绝旧 record且不传播至其它场景。
- Targeted：**39/39 PASS**。完整后端、构建与最终 Reviewer A/E 状态见下方收口记录；该 P1-A 记录时 P1-B 尚未开始，最新 P1-B 状态见本节上方。上述模型数值是本次历史输出，不是固定业务值或未来成功保证。

**最新工程收口证据**：cwd=`backend/`，`PYTHONPATH=tests:. .venv/bin/python -m unittest test_demo_v1 test_spatial_engine test_p1a_closure test_fleet_restart -q` → 39/39 PASS；`.venv/bin/python -m unittest discover -s tests -q` → **Ran 66：64 PASS + 2 skipped**（两项 opt-in LIVE 已另行实际执行 2/2 PASS）。`frontend/` 的 `npm run build` PASS；`git diff --check` PASS。Reviewer A/E 最终均 PASS，P0/P1=0；P2 见 TODO。P1-A 标记 IMPLEMENTED；独立提交推送后才开始 P1-B。浏览器交互验收属于后续 P1-B，不能把本次 build 等同浏览器验收。

### 本次修复前的历史 Closure 尝试（保留失败证据，不代表当前阻塞）

- 确定性回归：`test_p1a_closure.py` 验证 LIVE response 持久化、显式 Replay 来源、全确定性 Runtime 重跑、Demo04 zero candidate 人工闭环、失配/畸形/无 record 安全失败、LIVE failure 无自动 Replay、空间失败不派单不移动。这里只替换 provider transport，不代表真实模型效果。
- `test_fleet_restart.py` 两项测试使用多次独立 Python 子进程与临时 SQLite，验证 active map/location/battery/status/active_event_id 及 CLOSED terminal Fleet/event snapshot 重启不丢失；explicit reset 只重置 Fleet、不修改历史 snapshot。
- `test_p1a_live_acceptance.py` 默认跳过（避免普通全量测试产生付费调用）；通过 `RUN_P1A_LIVE_ACCEPTANCE=1` 显式开启。真实 LIVE 调用后在同一临时 SQLite 持久化 record，Replay 期间禁止全部 Qwen transport 调用，重新运行真实 stage functions。临时库清理后不为日常用户预置回放 record。
- 真实结果 #1：Demo01 cloud `.92` / verification `.95`，各保存一条 event/verification record，LIVE CLOSED 且 Replay CLOSED；Demo04 `large_object` / `.92` / Fusion `.872`，但 `need_clean=false / ignore` 导致 HUMAN_REVIEW，未到达人工完成。
- 真实结果 #2（补充通用 need_clean 包含人工清运语义后）：Demo01 cloud `.95` / verification `.95`，各一条 record，LIVE 与 Replay CLOSED；Demo04仍 `.92` / `large_object` / Fusion `.872`，HUMAN_REVIEW。真实 LIVE opt-in suite **1 PASS / 1 FAIL**，不能声称 Demo04真实Replay已通过。模型曾解释“垃圾桶旁、未阻碍通行”，需要澄清废弃/暂存事实，不得伪造正例。
- Reviewer A/E 最终复审：均 BLOCK，P0=0，唯一核心 P1 为真实 Demo04 尚未满足目标。旧合成 replay 与当前事件/验收入口 raw bool/置信度强转的两项代码 P1 已修复并通过独立复核。P1-A 不标 IMPLEMENTED，不 commit/push，不进入 P1-B。
- 最终工程命令（cwd=`backend/`）：`PYTHONPATH=tests:. .venv/bin/python -m unittest test_demo_v1 test_spatial_engine test_p1a_closure test_fleet_restart -q` → **36/36 PASS**；`.venv/bin/python -m unittest discover -s tests -q` → **Ran 63：61 PASS + 2 skipped**。2 个 skipped 是上述真实云端 opt-in 测试，不计为通过；单独实际执行为 1 PASS / 1 FAIL。`frontend/` 下 `npm run build` PASS；仓库 `git diff --check` PASS。本轮未进行浏览器交互验收，不把构建等同浏览器验收。

- 云端 transport 唯一入口为 `perception.qwen._request_qwen`；密钥只在本地环境变量。
- P1-C 已先完成 Evidence Sufficiency Gate，再以最终充分证据执行 confidence disposition：`confidence >= 0.85` 不独立二审、`0.50 <= confidence < 0.85` 独立二审、`confidence < 0.50` 为 HUMAN_REVIEW。首轮不足不能被这个最终门控提前终止。
- Fusion 为 `0.60 raw cloud + 0.20 category + 0.12 camera/location/time + 0.08 multiview`；veto 不被融合覆盖；raw next_action 不负责系统派单。
- Cloud 只在 cloud-review，Scheduler 只在 assign，Verification 只在 verify / Demo04 人工完成后。LIVE 不可用时停止在 Human Review，无 silent replay。
- 历史 Multi-view 的灰区固定 LangGraph 顺序已退出主 Demo 链路；P1-C 主链路为真实自主工具获取受控证据。该历史技术路径仍保留，不代表生产 RTSP 同步。

## 2. 真实历史记录（不可当作未来成功保证）

| 日期 / 代码 | Case | 结论 |
|---|---|---|
| 2026-08-28，旧单次门控 | Demo01–04 | 历史结果，不适用于独立二审/Fusion/阶段 Runtime 验收 |
| 2026-08-29，`e6b1eb9` | Demo01 / 赛特净界 S5 | 首轮 `.81`、二审 `.95`、Fusion `.89`、`robot-a`、验收 `.95`，CLOSED；这是历史真实结果，不是未来 UI/Runtime 固定值 |
| 同上 | Demo02 / 高仙 Omnie | 真实执行 Multi-view Agent workflow（使用受控多视角证据资产）；均 `robot-b` + CLOSED；首轮 `.85/.75/.85`，仅 #2 二审 `.95`，Fusion `.91/.97/.91` |
| 同上 | Demo03 / 蜗小白 SC50 | `robot-c` 被选、完整演示锚点路径；验收 `retry`，`HUMAN_REVIEW` |
| 同上 | Demo04 | cloud large_object 后人工完成、验收 `.98`，CLOSED；但 cloud 直接人工分支已被新的 LOCKED 目标替代 |
| 同上 | cloud unavailable | `HUMAN_REVIEW`，无 assignment/verification |

**本段为 Unified 之前历史证据的范围说明，并非当前实现状态；A/B/C/D 的新增完成证据见本文页首。** 这些历史结果单独只证明 transport、阶段边界和部分真实调用存在；不证明本地 YOLO、生产多机位同步、真实机器人遥测、MapCanvas、Camera→SLAM Runtime、Dijkstra Runtime、Demo03 ROI 验收、Stable Replay、Event Center/Analytics 目标产品或 Robot Operations Agent 已完成。

## 3. LOCKED 模式与安全测试语义

- **LIVE**：真实云端模型请求；失败必须可见并停在 `HUMAN_REVIEW`，不得自动切换 Replay。
- **Stable Replay（本轮 P1-A 路径已验证，四 Demo 连续次数回归仍属 P1-G）**：只允许使用过去真实成功调用保存的 structured AI evidence；Camera→SLAM、Scheduler、Dijkstra global topology planner / `plan_route()`、Fleet、SQLite transitions、Verification 仍需现场运行。UI 明示“稳定回放”。当前 Demo01/Demo04 各一次真实 LIVE→Replay 通过不代表四 Demo 完整多次回归通过。
- **Product capability / deployment policy**：测试客户显示为赛特净界 S5、高仙 Omnie、蜗小白 SC50、普渡 FlashBot Max，同时验证内部 ID 未变；SC50 地毯轻量垃圾仅作为 Demo Configuration；FlashBot Max 不能成为 Cleaning Scheduler 候选。
- **Demo03 verification（TODO）**：目标 ROI，不是整图找不同；输入原类别、bbox/ROI、before/after 全图和 ROI；机器人、人员、阴影、光照、无关变化不能单独导致失败。非目标干扰失败时独立 ROI 二审，不读取第一次答案。
- **Demo04（本轮已真实验证一次，连续 3 次总回归属 P1-G）**：已验证 Cloud → Locate → Capability Engine zero candidate → `HUMAN_FALLBACK` → 人工完成 → after → 云端验收，不允许 Demo ID 或 Cloud 直接跳人工。

## 4. 新 Multi-view Agent 验收（P1-C 核心已通过；P1-G 连续5次仍 TODO）

### 通用不变量

1. 第一轮 Cloud 只获得主视角、YOLO bbox/detection 和必要 Camera Context，并输出 `confidence`、`evidence_sufficient`、`ambiguity_type`；二者不能混为一谈。
2. **Evidence Sufficiency Gate 优先**：当 `evidence_sufficient=false`，且 reflection / occlusion / perspective / lens_contamination / insufficient_view 可通过额外视角缓解，并存在合法 supporting cameras 时，先进行自主 Multi-view acquisition；不可仅因 Single-view `confidence < 0.50` 转 `HUMAN_REVIEW`。
3. Multi-view 只能通过真实模型的 `tool_choice=auto` Tool Call 进入；Agent 可选 1–2 路，最多 2 evidence acquisition rounds。没有合法 camera、Evidence Fetch 失败或最多 2 rounds 后仍 `evidence_sufficient=false` 时必须 `HUMAN_REVIEW`；最终 evidence 不充分即使 raw confidence 高也不得自动处置。
4. final semantic judgment 的最终充分 evidence 才进入 confidence disposition：`confidence >= 0.85` 不独立二审；`0.50 <= confidence < 0.85` 做 independent targeted second review；`confidence < 0.50` 为 `HUMAN_REVIEW`。该二审可读本次合法完整 evidence set，不得读上一轮模型答案或 reasoning。
5. `find_supporting_cameras()` 返回 Coverage Graph 的真实候选；`fetch_camera_evidence()` 返回合法 evidence；`finish_visual_judgment()` 结束。PoC 可以使用 controlled evidence assets，测试报告必须显式写明，不能假称生产 RTSP 同步。
6. 严禁 `if demo_id == "demo02"`、固定 confidence threshold、`tool_choice=required`、初轮三图、前端 `setTimeout` 伪 Trace、静态选择 CAM-A1-02/A1-04。

### Demo02 LIVE

| 场景 | 次数与通过条件 | 必须记录 |
|---|---|---|
| A栋 1F 液体污渍 / 高仙 Omnie | 连续真实运行 5 次，至少 4 次由模型在 recoverable evidence insufficiency 下自主发起 Multi-view Tool Calling，并完成 candidate search → 1–2 路 evidence fetch → final semantic judgment → final confidence disposition → Capability / Scheduler → 高仙 Omnie → verification → CLOSED | single-view result、sufficiency、ambiguity、每次 Tool Call、candidate/selected cameras、evidence、final judgment、是否二审及 evidence-set 来源、final decision、latency、run/commit |

模型不稳定时只允许优化主视角、Prompt、Tool Description、Camera Metadata、Evidence Assets；严禁增加 demo_id 分支或强制前端阶段。客户 UI 步骤必须能回溯 Agent Trace / Tool Audit / Cloud Response / backend transition，且不展示 Chain-of-Thought。

## 5. Workbench / Event Center / Analytics 验收（LOCKED / TODO）

| 范畴 | 验收标准 |
|---|---|
| Workbench | MapCanvas 内白模、anchor、robot、route、marker 共用坐标；真实 SQLite transition timestamp；任务终态保留；统一 `EventDetailPanel(mode="live")` |
| Event Center | 新 CleaningEvent 立即出现、默认倒序；全部/处理中/自主闭环/人工/异常正确分类；正常 `HUMAN_FALLBACK` 不为异常；`?event=` 恢复选择；history detail 不重跑 Runtime 且使用 event-time snapshot |
| Analytics | 明确“近30天 · 演示历史数据”；5 KPI 均可追溯到 event/transition；处理中/异常 denominator 有规则；Heatmap / filters / drill-down 跳 Event Center；不使用 hardcoded KPI、利用率或趋势 |
| Robot utilization | 只统计赛特净界 S5、高仙 Omnie、蜗小白 SC50 的任务状态时间 ÷ 可用时间；FlashBot Max 不进清洁利用率排名 |

## 6. Robot Operations Agent / Delivery 验收（LOCKED / TODO）

- **Read 与 Page Context**：Workbench、Event Center、Analytics 是同一 `AgentSession`；分别自动传入当前 event/fleet/map、selected event/filter、time/type/hotspot/robot/KPI/chart context。
- **Action**：低风险 cleaning / delivery / relocation standby 任务必须经 Policy Guard、生成真实 backend Task 与 Action Card，并与 Fleet / Workbench 共享 Task ID / state。
- **Audit**：每个影响物理世界的 Action 记录原始指令/ASR、intent、tool/args、guard、Task ID、robot、结果、异常、replan、final state。
- **禁止工具测试**：Agent 无法获得或调用改 map、禁行区、范围、capability、Coverage/calibration、Scheduler policy、threshold、速度、门禁、电梯权限的 Write Tool。
- **UI / ASR**：Workbench/Event Center 同一可拖动浮窗；无已保存位置默认左下角，localStorage 位置优先，刷新/跨页/展开/收起保持，拖动不出 viewport。Analytics 仅固定 Panel；不出现第二 Agent。Microphone 只有配置的真实 ASR provider 可调用时才可用；未配置时必须 disabled 或显示“语音服务未配置”，不得使用预设文本、timer、mock transcript 或 fake voice animation。
- **Delivery Adapter**：没有真实平台授权必须是 `ADAPTER READY` / `AUTH REQUIRED`；不得显示 `CONNECTED` 或模拟外部 callback。真实授权后才测试 webhook / 双向状态同步。

## 7. Advanced Technical Observability 验收（LOCKED / TODO）

| 场景 | 必须可审计的 Advanced Trace |
|---|---|
| Demo01 | Edge → Single-view Cloud → `NOT_TRIGGERED / EVIDENCE_ALREADY_SUFFICIENT` Multi-view → Business Decision / Fusion → Verification |
| Demo02 | Edge → Single-view Cloud → Evidence Insufficient → `MODEL_TOOL_CALL` → supporting camera search → evidence fetch → Multi-view Cloud → Decision / Fusion → Verification；不得显示 `SYSTEM_WORKFLOW` 强制进入 |
| Demo03 | Camera→SLAM → Capability → Scheduler → 真实 `plan_route()` → 蜗小白 SC50 → Verification |
| Demo04 | Cloud → Camera→SLAM → Capability Candidate Count 0 → `HUMAN_FALLBACK` → Manual completion → Verification |

- **Reality Badge**：controlled edge 不得显示 `LIVE MODEL`；controlled camera evidence 不得显示 production live camera；PoC robot 不得显示 real telemetry；未授权 Delivery Adapter 不得显示 `CONNECTED`；Reality Matrix 的状态由 Runtime fact / configuration / provider / evidence / authorization 自动决定，用户不可编辑。
- **Runtime / Error**：验证 LIVE success、LIVE model failure、用户手动启用 Replay、`POLICY_REJECTED`、`SPATIAL_ERROR`、`ROUTE_ERROR`、`VERIFICATION_ERROR`；错误层级准确，LIVE failure 无 silent Replay。Tool Trace 必须有 tool、trigger source、start time、duration、status、input/result summary，不能是前端定时器。
- **Sensitive data / CoT**：任何 Advanced UI/API response 不得泄漏 API Key、Secret、Access Token、Authorization Header 或环境变量具体值；不得显示 Chain-of-Thought、scratchpad 或 reasoning tokens。
- **Trace projection**：Advanced 只投影 CleaningEvent transitions、cloud/model request record、Agent Action/Tool Audit、spatial/capability/scheduler/route/verification/provider/reality metadata；不得重跑模型、Scheduler 或 Route Planner。Trace ID 独立于 Event ID，并可串联 Event / AgentTask / Tool / model / task runtime。

## 8. 清洁主场景总体回归（LOCKED / TODO）

| 模式 | 场景 | 次数与通过条件 |
|---|---|---|
| LIVE | Demo01 | 连续 5 次，至少 4 次赛特净界 S5 → verify → CLOSED |
| LIVE | Demo02 | 见第 4 节；至少 4/5 自主 Tool Calling 后高仙 Omnie → verify → CLOSED |
| LIVE | Demo03 | 连续 5 次，至少 4 次蜗小白 SC50 → Dijkstra global topology planner / `plan_route()` 跨楼/电梯/Skybridge → ROI verify → CLOSED |
| LIVE | Demo04 | 连续 3 次，全部 Cloud → Locate → zero candidate → Human → verify → CLOSED |
| Stable Replay | 四个 Demo | 每个连续 3 次，100% 正确流程；不得跳过非 AI Runtime |

每次必须记录 run id / commit、模式、时间、raw cloud confidence、是否二审及 confidence、Fusion/composite score、系统决策、selected robot、route、verification raw result、最终状态、每个云端请求 latency。主场景合理业务成功率低于约 80% 时，先调查 Prompt、ROI、ontology、输入上下文、parser、模型/系统决策分离，而不是仅称“随机”。

## 9. 当前限制与禁止性结论

- 当前不宣称 REAL YOLO、生产多机位同步、真实机器人遥测、真实电梯、真实外卖平台集成或生产阈值。
- 旧 Stable Replay 不能叫完整稳定回归，直到满足本文件第 3 节定义。
- Demo03 目前的 `retry` 必须如实保留；不能通过 Demo ID 特判或写死 PASS 修复。
- 当前 Advanced 仅是基础 shell；不宣称已完成 Trace Inspector、Reality Matrix、结构化 audit、真实 Tool / Error / source projection 或 Trace ID。
- 早前 docs-only 限制已由 Unified Implementation 授权取代；本轮已运行第 1 节所列代码/模型测试，未运行浏览器交互验收；仍无 P1-A 验收完成声明。
