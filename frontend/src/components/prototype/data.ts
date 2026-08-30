import type { Camera, DemoScenario, PrototypeState } from "./types";

const asset = (camera: string, event: string, file: string) => `/demo-assets/${camera}/${event}/${file}`;

export const cameras: Record<string, Camera> = {
  "CAM-OUT-01": {
    id: "CAM-OUT-01", location: "园区东侧道路",
    image: asset("CAM-OUT-01", "event-outdoor-tissue-001", "primary.png"),
    afterImage: asset("CAM-OUT-01", "event-outdoor-tissue-001", "after.png"),
    overlay: [{ label: "其他小型垃圾", confidence: 0.81, bbox: [716 / 1448, 675 / 1086, 775 / 1448, 716 / 1086] }],
  },
  "CAM-A1-01": {
    id: "CAM-A1-01", location: "A栋1F大堂",
    image: asset("CAM-A1-01", "event-beverage-spill-002", "primary.png"),
    afterImage: asset("CAM-A1-01", "event-beverage-spill-002", "after.png"),
    overlay: [{ label: "液体污渍", confidence: 0.58, bbox: [643 / 1448, 544 / 1086, 827 / 1448, 641 / 1086] }],
  },
  "CAM-A1-02": {
    id: "CAM-A1-02", location: "A栋1F入口补充视角",
    image: asset("CAM-A1-02", "event-beverage-spill-002", "secondary.png"),
    overlay: [{ label: "液体污渍", confidence: 0.63, bbox: [684 / 1448, 529 / 1086, 802 / 1448, 617 / 1086] }], temporary: true,
  },
  "CAM-A1-04": {
    id: "CAM-A1-04", location: "A栋1F休息区补充视角",
    image: asset("CAM-A1-04", "event-beverage-spill-002", "secondary.png"),
    overlay: [{ label: "液体污渍", confidence: 0.61, bbox: [630 / 1448, 539 / 1086, 817 / 1448, 614 / 1086] }], temporary: true,
  },
  "CAM-A2-08": {
    id: "CAM-A2-08", location: "A栋2F连廊区域",
    image: asset("CAM-A2-08", "event-indoor-can-003", "primary.png"),
    afterImage: asset("CAM-A2-08", "event-indoor-can-003", "after.png"),
    overlay: [{ label: "易拉罐", confidence: 0.84, bbox: [699 / 1448, 695 / 1086, 735 / 1448, 721 / 1086] }],
  },
  "CAM-A2-11": {
    id: "CAM-A2-11", location: "A栋2F公共区域",
    image: asset("CAM-A2-11", "event-oversized-box-004", "primary.png"),
    afterImage: asset("CAM-A2-11", "event-oversized-box-004", "after.png"),
    overlay: [
      { label: "大件物品", confidence: 0.82, bbox: [505 / 1448, 570 / 1086, 627 / 1448, 706 / 1086] },
      { label: "大件物品", confidence: 0.76, bbox: [604 / 1448, 610 / 1086, 723 / 1448, 729 / 1086] },
    ],
  },
};

export const defaultCameraIds = ["CAM-OUT-01", "CAM-A2-08"];

const standard: PrototypeState[] = ["DISCOVERED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATING", "ROBOT_ASSIGNED", "NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"];

export const scenarios: DemoScenario[] = [
  {
    id: "outdoor", triggerLabel: "园区道路 · 小型垃圾", cameraId: "CAM-OUT-01", eventTitle: "园区东侧道路发现小型垃圾", category: "其他小型垃圾", confidence: 81, qwenConfidence: 0,
    qwenSummary: "多为轻质纸屑，室外清扫能力可覆盖。", afterImage: asset("CAM-OUT-01", "event-outdoor-tissue-001", "after.png"), steps: standard,
  },
  {
    id: "liquid", triggerLabel: "A栋1F大堂 · 液体污渍", cameraId: "CAM-A1-01", eventTitle: "A栋1F大堂发现液体污渍", category: "液体污渍", confidence: 58, qwenConfidence: 0,
    qwenSummary: "跨视角证据排除了反光、镜头污渍与光照干扰，确认为需立即处理的液体污渍。", afterImage: asset("CAM-A1-01", "event-beverage-spill-002", "after.png"), steps: ["DISCOVERED", "EDGE_DETECTED", "MULTI_VIEW", "CLOUD_REVIEW", "LOCATING", "ROBOT_ASSIGNED", "NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"],
  },
  {
    id: "can", triggerLabel: "A栋2F连廊区域 · 易拉罐", cameraId: "CAM-A2-08", eventTitle: "A栋2F连廊区域发现易拉罐", category: "易拉罐", confidence: 84, qwenConfidence: 0,
    qwenSummary: "室内小型固体垃圾，蜗小白 SC50 的拾取与地面清洁能力满足要求。", afterImage: asset("CAM-A2-08", "event-indoor-can-003", "after.png"), steps: ["DISCOVERED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATING", "ROBOT_ASSIGNED", "NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"],
  },
  {
    id: "oversized", triggerLabel: "A栋公共区域 · 大件物品", cameraId: "CAM-A2-11", eventTitle: "A栋2F公共区域发现大件物品", category: "大件物品", confidence: 82, qwenConfidence: 0,
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
};
