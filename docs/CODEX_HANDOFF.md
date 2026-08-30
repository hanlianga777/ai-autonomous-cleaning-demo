# Codex 交接｜Post-merge Interview Freeze

> **Post-merge Interview Freeze · 2026-08-30**
> Unified Implementation merge baseline: `8341eb079fe5a700b4931e0112fdbe5552297785`
> Current main HEAD: 以 GitHub main / `git rev-parse HEAD` 为准
> 历史实施分支：`codex/unified-implementation`，最终提交 `bdd08e02e0e4fc96d9ad6229949f2c8bf3812136`。它不是当前开发分支。

新 Session 必须依次完整阅读 `PROJECT_CONTEXT.md`、`DECISIONS.md`、`TODO.md`、`ARCHITECTURE.md`、本文件、`AI_INTEGRATION_TEST.md`，然后检查 `git status`、`git log` 和代码。不要用聊天上下文或旧阶段 Prompt 补全事实。

## 当前实现

- 四个一级页面：Workbench、Event Center、Analytics、Advanced Technical Observability。
- 主 Runtime 为阶段式 `demo_v1`：创建事件 → edge → cloud/evidence gate → optional Multi-view → locate → Capability → Scheduler → Dijkstra → 执行模拟 → verification。旧 one-shot `/api/demo-v1/runs/*` 已 RETIRED（410）。
- 两个 Agent：Multi-view Perception Agent 与 Robot Operations Agent。前者只使用 Coverage / Evidence Fetch / VLM；后者有受限任务工具，不能修改基础设施或决定清洁机器人。
- `HUMAN_FALLBACK` 只能由 Capability Engine 的 zero candidate 产生；LLM 不选择机器人、不直接决定找人工。
- Analytics 与 Advanced 都是同一 SQLite/Runtime 的读取投影；Advanced 不能重跑模型、Scheduler 或 route。
- P1-A/B/C/D/E/F/H/G 工程、自动化、浏览器验收均 IMPLEMENTED；正式 LIVE 为 Demo01 5/5、Demo02 5/5、Demo03 5/5、Demo04 3/3；四个 Stable Replay 各 3/3、无新 Cloud request。

## Batch 2 当前 LOCKED TARGET（未实施）

- OPS-AUTO-01：完整合法 Agent 指令应自动进入真实后端 Show Runtime，不再让客户反复 Advance；这不授权前端假动画、POI 猜测或绕过 Guard。
- AGENT-SESSION-01：新 Show = 新 Agent Chat Session；同场跨页仍共享一条对话，合法业务历史/Advice 不随 Chat 清空。
- AGENT-AUTHORITY-01：清洁选择继续只由 Capability/Scheduler/Deployment Policy；FlashBot 不清洁，Demo04 人工完成仍须明确用户/操作员 Action。
- OPS-CONTINUITY-01：任务/Demo 不能因切页、收起 Chat、重挂载中断；唯一真相在后端 Runtime，前端 timer 只做投影。
- AI-RESILIENCE-01：仅瞬时技术 provider 错误可自动重试一次；业务失败不刷答案，LIVE 永不隐藏切 Stable Replay。

完整子项、当前偏差、Affected Active Code 与未来 Matrix 合同仅以 `INTERVIEW_DEMO_RECONCILIATION.md` 为准。本轮仍为 Docs-only；必须等待用户明确授权 `UNIFIED INTERVIEW DEMO RECOVERY` 才可修改代码。

## Batch 3 Final LOCKED TARGET / REQUIREMENT FREEZE（未实施）

- EVIDENCE-INTEGRITY-01：asset file 存在不等于当前事件证据可用。After、未实际获取的 Demo02 Supporting 和 Demo04 人工完成前 After 不得泄漏给客户页面、Agent、业务 API、Cloud 或 Replay；Terminal history 保留完整实际证据链。
- RUNTIME-SINGLE-PATH-01：正式客户 Runtime 仅有一个 CleaningEvent mutation authority。所有 legacy/helper API/service 必须在未来实施前审计为 authoritative、engineering/test-only 或 retired；正式 Frontend/Agent 不得使用替代 mutation path。
- **REQUIREMENT FREEZE**：除用户明确提出新的业务/UI问题外，不扩张需求。下一项可授权工作只有 `UNIFIED INTERVIEW DEMO RECOVERY`；开始前先建立全量逐子项 Matrix，且必须包含 Evidence Availability / Temporal Gate 和 Runtime Mutation Path Audit。

## 当前模型与真实边界

- 云端语义/验单：`qwen-vl-max`；多视角工具调用：`qwen3-vl-plus`。
- Controlled bbox/图片证据不是本地 REAL YOLO；不得声称本地 YOLO 已实跑。
- 机器人移动、电梯/连廊、配送均为 PoC simulation，不是 telemetry 或外部平台连接。
- ASR 未配置；麦克风必须保持 disabled/明确提示，禁止 mock transcript。
- 未实现：生产身份权限、真实设备/RTSP/VMS、外部配送平台、分布式 queue、ROS/Nav2、生产审计留存与分布式 tracing。

## 当前 P2

- 生产身份与权限、分布式任务恢复/审计/可观测性、真实硬件与外部平台接入。
- 原生 Delivery/Relocation Task 的独立 Trace 查询入口。
- Advanced 的非必要体验增强、构建包拆分。
- 真实 availability/uptime 数据源与历史数据保留策略。

除非用户重新授权，不进入新产品阶段；**Next authorized work = none**。用户主观展示验收仍 pending，不能由上述工程证据替代。

## 启动与防回归

在项目根目录先执行/双击 `stop_demo.command`，再执行/双击 `start_demo.command`；访问 <http://localhost:5173/prototype>。启动脚本验证 `operations.v1`，避免复用旧服务导致空白页。

不可回退规则：

1. Robot-first + Human Fallback；Capability Engine + Scheduler 是唯一清洁机器人选择器。
2. Evidence Sufficiency Gate 优先于最终 confidence disposition；可恢复的证据不足先由模型自主补证。
3. Camera→SLAM、Fleet、Dijkstra `plan_route()` 共用同一空间事实，不能用 demo ID 或前端动画伪造路线。
4. LIVE failure 不得 silent fallback；Stable Replay 必须标记 REPLAY，且仅复用已保存真实 structured record。
5. 前端只投影后端事实；不得伪造模型调用、Agent Trace、latency、设备遥测或 Chain-of-Thought。

历史阶段过程、旧失败与逐次测试证据在 `AI_INTEGRATION_TEST.md` 和 Git history，不在本交接文件重复。
