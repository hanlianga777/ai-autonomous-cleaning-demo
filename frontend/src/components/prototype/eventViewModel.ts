/** Read-only projection of durable backend events. Never runs business logic. */
import { cameras, scenarios } from "./data";
import type { ActiveEvent, Camera, PrototypeState } from "./types";

export type RecordValue = Record<string, any>;
export type TimelineEntry = { state: string; label: string; timestamp?: string; detail: RecordValue; pending?: boolean };

export const stateLabels: Record<string, string> = {
  SINGLE_VIEW_REVIEW: "单视角语义与证据充分性",
  DETECTED: "发现现场事件", EDGE_DETECTED: "边缘目标识别", MULTI_VIEW: "多视角证据研判",
  CLOUD_REVIEW: "云端综合研判", LOCATED: "空间定位", ASSIGNED: "能力匹配与机器人派单",
  NAVIGATING: "机器人前往现场", ARRIVED: "机器人到达现场", CLEANING_COMPLETED: "清洁动作完成",
  VERIFYING: "固定摄像头验收", CLOSED: "事件已闭环", HUMAN_FALLBACK: "零候选 · 人工兜底",
  HUMAN_REVIEW: "待人工复核",
};
export const displayStates: Record<string, PrototypeState> = {
  SINGLE_VIEW_REVIEW: "CLOUD_REVIEW",
  DETECTED: "DISCOVERED", EDGE_DETECTED: "EDGE_DETECTED", MULTI_VIEW: "MULTI_VIEW",
  CLOUD_REVIEW: "CLOUD_REVIEW", LOCATED: "LOCATING", ASSIGNED: "ROBOT_ASSIGNED",
  NAVIGATING: "NAVIGATING", ARRIVED: "NAVIGATING", CLEANING_COMPLETED: "CLEANING",
  VERIFYING: "VERIFYING", CLOSED: "CLOSED", HUMAN_FALLBACK: "HUMAN_FALLBACK", HUMAN_REVIEW: "HUMAN_REVIEW",
};
const inflightStates: Record<string, string> = { EDGE_DETECTED: "EDGE_DETECTED", MULTI_VIEW: "MULTI_VIEW", CLOUD_REVIEW: "CLOUD_REVIEW", LOCATING: "LOCATED", ROBOT_ASSIGNED: "ASSIGNED", NAVIGATING: "NAVIGATING", CLEANING: "CLEANING_COMPLETED", VERIFYING: "VERIFYING" };

export function timelineFor(event: ActiveEvent, mode: "live" | "history" = "live"): TimelineEntry[] {
  const transitions = event.liveResult?.transitions;
  const rows: TimelineEntry[] = Array.isArray(transitions) ? transitions.map((item: RecordValue) => ({ state: String(item.state), label: stateLabels[item.state] ?? "已记录的处理阶段", timestamp: item.created_at, detail: item.detail ?? {} })) : [];
  const pending = event.inFlightState && inflightStates[event.inFlightState];
  if (mode === "live" && event.processing && pending && rows[rows.length - 1]?.state !== pending) rows.push({ state: pending, label: stateLabels[pending], detail: {}, pending: true });
  return rows;
}

export function fromStoredEvent(stored: RecordValue): ActiveEvent {
  const snapshot = stored.demo_v1 ?? stored;
  const runtime = { ...snapshot, ...stored, demo_v1: undefined };
  const scene = scenarios.find((s) => s.cameraId === snapshot.asset_manifest?.assets?.find((a: RecordValue) => a.role === "before")?.camera_id);
  const cameraId = snapshot.asset_manifest?.assets?.find((a: RecordValue) => a.role === "before")?.camera_id ?? "未记录摄像头";
  const base = scene ?? { id: "outdoor" as const, triggerLabel: "历史事件", cameraId, eventTitle: "历史清洁事件", category: customerTerm(stored.task_profile?.object_type), confidence: 0, qwenConfidence: 0, qwenSummary: "", steps: [] };
  const steps = Array.isArray(stored.transitions) ? stored.transitions.map((t: RecordValue) => displayStates[t.state]).filter(Boolean) : [displayStates[stored.state] ?? "HUMAN_REVIEW"];
  return { scenario: { ...base, steps }, stageIndex: Math.max(0, steps.length - 1), startedAt: stored.created_at ?? "", backendState: stored.state, liveResult: runtime };
}

export function eventCamera(event: ActiveEvent, role: "before" | "after" = "before", cameraId = event.scenario.cameraId): Camera | null {
  const assets = (event.liveResult?.asset_manifest as RecordValue | undefined)?.assets;
  if (!Array.isArray(assets)) return null; // Do not invent evidence for old archives.
  const asset = assets.find((a: RecordValue) => a.camera_id === cameraId && (role === "after" ? a.role === "after" : ["before", "evidence"].includes(a.role)));
  if (!asset?.available || !asset.url) return null;
  return { id: cameraId, location: cameras[cameraId]?.location ?? "事件存档画面", image: asset.url,
    overlay: (asset.detection_overlays ?? []).map((o: RecordValue) => ({ label: customerTerm(o.label), confidence: o.confidence, bbox: [o.bbox.x1, o.bbox.y1, o.bbox.x2, o.bbox.y2] })) };
}

/** Primary event slot + clean idle slot. Supporting cameras never enter this grid. */
export function monitorViews(event: ActiveEvent | null): Array<{ camera: Camera; available: boolean; eventView: boolean; after: boolean; detections: boolean }> {
  const primary = event?.scenario.cameraId;
  const ids = !primary || primary === "CAM-OUT-01" ? ["CAM-OUT-01", "CAM-A2-08"] : primary === "CAM-A1-01" ? [primary, "CAM-A2-08"] : ["CAM-OUT-01", primary];
  const transitions = event?.liveResult?.transitions;
  const stateSet = new Set(Array.isArray(transitions) ? transitions.map((t: RecordValue) => t.state) : []);
  const hasAfter = stateSet.has("VERIFYING"); // after exists even when verification subsequently fails.
  const detected = stateSet.has("EDGE_DETECTED");
  return ids.map((id) => {
    const active = Boolean(event && id === primary);
    const after = active ? hasAfter : true;
    const source = active ? eventCamera(event!, after ? "after" : "before", id) : null;
    const camera = source ?? { ...cameras[id], image: active ? "" : cameras[id].afterImage ?? cameras[id].image };
    return { camera, available: Boolean(camera.image), eventView: active, after, detections: active && !after && detected };
  });
}

const terms: Record<string, string> = { small_litter: "其他小型垃圾", "地面纸巾": "其他小型垃圾", "大型纸箱": "大件物品", liquid: "液体污渍", can: "易拉罐", large_object: "大件物品", leaf: "树叶", unknown: "尚未明确", low: "轻度", medium: "中度", high: "重度", tile: "瓷砖", polished_tile: "抛光瓷砖", ceramic_tile: "瓷砖", granite: "花岗岩", asphalt: "沥青", carpet: "地毯", epoxy: "环氧地坪", reflection: "反光", floor_reflection: "地面反光", glare: "眩光", low_lighting: "光照较弱", none: "无", indoor: "室内", outdoor: "室外" };
export function customerTerm(value: unknown): string {
  const text = String(value ?? "");
  const aliases: Record<string, string> = { carpeted_floor: "地毯", tiled_floor: "瓷砖", tile_floor: "瓷砖", concrete: "混凝土", concrete_floor: "混凝土", wet_floor: "湿润地面", smooth_floor: "光滑地面", proximity_to_recycling_bin: "靠近回收箱", potential_obstruction_in_corridor: "可能阻挡通道", occlusion: "局部遮挡", perspective: "视角偏差", insufficient_view: "视野不足", lens_contamination: "镜头污染", "East Corridor": "东侧走廊", "West Lobby": "西侧大堂", "Main Lobby": "主大堂", "Skybridge Entrance": "连廊入口", "Outdoor East Road": "园区东侧道路", "No robot passes hard constraints; create manual work order.": "没有机器人满足处置硬约束，已创建人工工单。" };
  return terms[text] ?? aliases[text] ?? (/^[\x00-\x7F]*$/.test(text) ? "未归类 / 待复核" : text);
}
export function timestampMs(value: unknown): number {
  if (typeof value !== "string" || !value) return NaN;
  const iso = value.replace(" ", "T");
  return Date.parse(/Z$|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
}
export function clockLabel(value: unknown): string { const ms = timestampMs(value); return Number.isFinite(ms) ? new Date(ms).toLocaleTimeString("zh-CN", { hour12: false }) : "—"; }
