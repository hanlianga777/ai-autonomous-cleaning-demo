# AI 自主清洁 Demo｜真实任务清单

> **状态：LOCKED · 2026-08-29**
> 此清单只描述当前代码与已确认需求的差距。`IMPLEMENTED` 不等于用户最终验收；`PARTIAL` 不得在任何文档写成完成。

## 已实现（IMPLEMENTED，仍需后续回归）

- 工程基础：FastAPI、SQLite、React/Vite、Tailwind/shadcn、ECharts、CORS、离线页面 fallback、一键启动/停止。
- Phase 2：6 图 SLAM、Global Spatial Graph、Dijkstra/A*、Camera Coverage、CAM-A1-01 四点映射。
- Phase 3：CleaningEvent、TaskProfile、Capability Engine、Scheduler、SQLite transition audit、Mock Robot/Verification。
- Phase 4/5：统一结构化感知 schema、可选云端 Qwen 传输、Multi-view Agent 的工具与次数边界。
- 受控 Demo01–04 bbox 素材、Demo04 after 图、Demo04 人工完成后云端验收 API。
- `demo_v1` 运行写入 SQLite；Analytics 把持久化运行作为 30 天基线增量。
- 四页客户壳、右侧证据图 Esc/空白/关闭按钮放大、前端生产构建和基础浏览器 Console 检查。

## P0｜业务真实性修复（代码与技术回归已完成，待用户最终验收）

- [x] **真实串行执行**：已由阶段 REST 状态推进替代“单次完整结果 + 前端播放”；云端、定位、能力匹配、派单、路线、清洁、验收分别持久化。
- [x] **真实 assignment projection**：地图和机器人动作只读取真实 `assignment_decision`，不再以 `scenario.robot` 预设实际执行对象。
- [x] **空间拓扑与路线**：已建立可复用 `campusTopology`，包含待机点、道路、电梯、连廊和事件锚点；Robot C 使用完整锁定序列。
- [x] **首轮 Demo02 Prompt**：三图同地点/同时间/同一区域和反光、空间一致性联合判断已加入首轮 Prompt。
- [x] **真实 E2E 回归**：Demo01、Demo02 三次、Demo03、Demo04 人工闭环及云端不可用均已在 2026-08-29 真实运行；完整数据见 `AI_INTEGRATION_TEST.md`。
- [x] **文档一致性持续守护**：本轮六份事实源已同步；下一轮仍必须更新。

> P0 不自动进入 P1。Demo03 本次云端验收为 `retry` 并转人工复核，是已记录的真实结果，不得表述为自动闭环成功。

## P1｜已确认但产品实现不完整

- [ ] **工作台视觉/交互复验**：验证并修复“演示场景”弹层 z-index、穿模/灰线、Demo04 点击可达性；删除客户页面无价值文案；菜单仅四个 1/2/3/4 快捷入口。
- [ ] **监控动态与恢复**：逐场景浏览器验证双监控切换、验收后恢复默认 after 图、图片完整比例和不变形。
- [ ] **事件详情去重与跟随**：Multi-view 阶段仅显示三路图；云端阶段仅显示结论/原始置信度/因素/依据/融合分；验收仅 after 图；验证手动滚动暂停自动跟随和“回到当前进度”。
- [ ] **资产栏与 hover**：显示完整中文机器人名称、缩略图、状态；hover 补全名称、电量、位置、服务区域和能力边界。B/C 维持室内半透明，A/D 正常显示。
- [ ] **路线视觉**：未走浅灰虚线、已走更粗实线、少量箭头；移除地图技术说明和“清洁目标”文字。
- [ ] **EventCenter 完整化**：实现全部/处理中/已自主闭环/待人工处理/异常筛选，补齐来源摄像头、时间、处置方式、机器人、闭环耗时，并复用工作台同一 `EventDetailPanel`，而非独立简化 Drawer。
- [ ] **运营分析完整化**：补充高频事件类型、区域、任务量和完整 KPI；热力图继续复用同一园区白模并以程序计算数据展示。
- [ ] **真实运营建议**：将“重新分析”的前端固定文案改为以预计算 KPI/热力/利用率/任务量为输入的真实云端大模型只读建议。
- [ ] **统一只读 AI Assistant**：实现工作台浮动入口与运营页聊天入口共用同一后端云端 Assistant；加 5 个事实性问答与禁止执行操作的测试。

## P2｜演示质量与长期演进

- [ ] 收敛企业 SaaS 设计 token、响应式细节、Figma/视觉设计升级；不引入第二套 UI 系统。
- [ ] 增加 Demo03 清洁后真实验收样本，分析历史未闭环原因。
- [ ] 补充足够标注数据后再评估真实 YOLO 权重；当前小数据 Custom YOLO 不可接入。
- [ ] 真实生产 Camera→SLAM 数学、近同步多摄像头、真实设备遥测、电梯接口、阈值与 Scheduler 权重标定。

## 不在当前范围（BLOCKED / 未授权）

- ROS 2、Nav2 runtime、Open-RMF runtime、Docker/Kubernetes、Kafka/Redis/PostgreSQL、真实机器人/电梯/门禁、RAG、Planner Agent、VLA、预测模型、RL。

## 验收规则

任何项只有在代码实现、相应 API/浏览器验证完成并由用户确认后，才能从 TODO/PARTIAL 改为 IMPLEMENTED；仅有视觉占位、固定字符串或旧历史测试均不能升级状态。
