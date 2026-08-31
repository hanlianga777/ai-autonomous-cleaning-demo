import type { Camera, DemoScenario, PrototypeState } from "./types";

const asset = (camera: string, event: string, file: string) => `/demo-assets/${camera}/${event}/${file}`;

export const cameras: Record<string, Camera> = {
  "CAM-OUT-01": {
    id: "CAM-OUT-01", location: "园区东侧道路",
    image: asset("CAM-OUT-01", "event-outdoor-tissue-001", "primary.png"),
    afterImage: asset("CAM-OUT-01", "event-outdoor-tissue-001", "after.png"),
  },
  "CAM-A1-01": {
    id: "CAM-A1-01", location: "A栋1F大堂",
    image: asset("CAM-A1-01", "event-beverage-spill-002", "primary-ambiguous-v2.png"),
    afterImage: asset("CAM-A1-01", "event-beverage-spill-002", "after.png"),
  },
  "CAM-A1-02": {
    id: "CAM-A1-02", location: "A栋1F入口补充视角",
    image: asset("CAM-A1-02", "event-beverage-spill-002", "secondary.png"),
    temporary: true,
  },
  "CAM-A1-04": {
    id: "CAM-A1-04", location: "A栋1F休息区补充视角",
    image: asset("CAM-A1-04", "event-beverage-spill-002", "secondary.png"),
    temporary: true,
  },
  "CAM-A2-08": {
    id: "CAM-A2-08", location: "A栋2F连廊区域",
    image: asset("CAM-A2-08", "event-indoor-can-003", "primary.png"),
    afterImage: asset("CAM-A2-08", "event-indoor-can-003", "after.png"),
  },
  "CAM-A2-11": {
    id: "CAM-A2-11", location: "A栋2F公共区域",
    image: asset("CAM-A2-11", "event-oversized-box-004", "primary.png"),
    afterImage: asset("CAM-A2-11", "event-oversized-box-004", "after.png"),
  },
};

export const defaultCameraIds = ["CAM-OUT-01", "CAM-A2-08"];

const standard: PrototypeState[] = ["DISCOVERED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATING", "ROBOT_ASSIGNED", "NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"];

export const scenarios: DemoScenario[] = [
  {
    id: "outdoor", demoCode: "Demo01", triggerLabel: "园区道路 · 小型垃圾", presentationFocus: "室外小型垃圾的自动闭环", cameraId: "CAM-OUT-01", eventTitle: "园区东侧道路发现小型垃圾", category: "其他小型垃圾", confidence: 81, qwenConfidence: 0,
    qwenSummary: "多为轻质纸屑，室外清扫能力可覆盖。", afterImage: asset("CAM-OUT-01", "event-outdoor-tissue-001", "after.png"), steps: standard,
  },
  {
    id: "liquid", demoCode: "Demo02", triggerLabel: "A栋1F大堂 · 液体污渍", presentationFocus: "多视角取证排除反光歧义", cameraId: "CAM-A1-01", eventTitle: "A栋1F大堂发现液体污渍", category: "液体污渍", confidence: 58, qwenConfidence: 0,
    qwenSummary: "跨视角证据排除了反光、镜头污渍与光照干扰，确认为需立即处理的液体污渍。", afterImage: asset("CAM-A1-01", "event-beverage-spill-002", "after.png"), steps: ["DISCOVERED", "EDGE_DETECTED", "MULTI_VIEW", "CLOUD_REVIEW", "LOCATING", "ROBOT_ASSIGNED", "NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"],
  },
  {
    id: "can", demoCode: "Demo03", triggerLabel: "A栋2F连廊区域 · 易拉罐", presentationFocus: "跨楼、电梯与连廊的路线调度", cameraId: "CAM-A2-08", eventTitle: "A栋2F连廊区域发现易拉罐", category: "易拉罐", confidence: 84, qwenConfidence: 0,
    qwenSummary: "室内小型固体垃圾，蜗小白 SC50 的拾取与地面清洁能力满足要求。", afterImage: asset("CAM-A2-08", "event-indoor-can-003", "after.png"), steps: ["DISCOVERED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATING", "ROBOT_ASSIGNED", "NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"],
  },
  {
    id: "oversized", demoCode: "Demo04", triggerLabel: "A栋公共区域 · 大件物品", presentationFocus: "能力不足时转人工，仍保留验收闭环", cameraId: "CAM-A2-11", eventTitle: "A栋2F公共区域发现大件物品", category: "大件物品", confidence: 82, qwenConfidence: 0,
    qwenSummary: "废弃待清运的大件物品；由云端判断处置需求。", afterImage: asset("CAM-A2-11", "event-oversized-box-004", "after.png"), steps: ["DISCOVERED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATING", "HUMAN_FALLBACK", "VERIFYING", "CLOSED"],
  },
];

export const stageCopy: Record<PrototypeState, { title: string; detail: string }> = {
  IDLE: { title: "园区持续监测中", detail: "等待摄像头发现新的清洁事件" },
  DISCOVERED: { title: "摄像头发现异常", detail: "固定摄像头已上报疑似现场问题" },
  EDGE_DETECTED: { title: "边缘识别完成", detail: "已生成单视角目标位置与类别置信度" },
  MULTI_VIEW: { title: "多视角研判", detail: "展示本事件实际取得的补充证据与研判记录" },
  CLOUD_REVIEW: { title: "云端综合研判", detail: "结合现场语义确认清洁必要性及处置建议" },
  LOCATING: { title: "空间定位完成", detail: "已映射至园区二维空间坐标与可达路径" },
  ROBOT_ASSIGNED: { title: "已生成机器人任务", detail: "根据能力、电量与位置选择最合适的机器人" },
  NAVIGATING: { title: "机器人正在前往", detail: "按规划路线驶向目标区域" },
  ELEVATOR_TRANSFER: { title: "机器人正在乘坐电梯", detail: "蜗小白 SC50 从 B栋1F 转移至 B栋2F" },
  SKYBRIDGE_TRANSFER: { title: "机器人正在通过空中连廊", detail: "蜗小白 SC50 由 B栋2F 前往 A栋2F" },
  CLEANING: { title: "机器人正在清洁", detail: "现场清洁动作执行中" },
  VERIFYING: { title: "固定摄像头验收中", detail: "比对清洁前后画面，并由 AI 判断是否通过" },
  CLOSED: { title: "事件已闭环", detail: "清洁验收通过，完整事件记录已保留" },
  HUMAN_FALLBACK: { title: "已转人工处置", detail: "大件物品超出 现有清洁机器人 能力边界，机器人未移动" },
  HUMAN_REVIEW: { title: "建议人工复核", detail: "自动流程已停止，保留已发生的完整处置记录" },
  CANCELLED: { title: "事件已取消", detail: "任务已停止，保留已发生的处置记录" },
  PAUSED: { title: "任务已暂停", detail: "通过共享任务卡继续或取消任务" },
};
