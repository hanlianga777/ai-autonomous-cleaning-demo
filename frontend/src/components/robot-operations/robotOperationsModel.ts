/** Pure state helpers for the single Robot Operations Agent UI. */

export type AgentMessage = { id: string; role: "user" | "assistant" | "system"; content: string; created_at: string };
export type OperationsTask = {
  task_id: string;
  kind: string;
  status: string;
  robot_id?: string | null;
  origin?: { label?: string; map_id?: string; x?: number; y?: number } | null;
  destination?: { label?: string; map_id?: string; x?: number; y?: number } | null;
  source: string;
  event_id?: string | null;
};
export type AgentAudit = { id?: number; created_at?: string; phase?: string; tool?: string; policy?: string; final_status?: string; error?: string | { message?: string }; result?: { ok?: boolean }; task_id?: string; robot?: string };
export type AgentSessionSnapshot = { id: string; messages: AgentMessage[]; tasks: OperationsTask[]; audits: AgentAudit[]; busy?: boolean; error?: { code?: string; message?: string } | null };
export type AdviceItem = { finding: string; evidence: string; recommendation: string; related_events: string[] };
export type AdviceSnapshot = { generated_at: string; data_window: { start: string; end: string; days: number }; items: AdviceItem[] };
export type FloatingPosition = { x: number; y: number };

export const SESSION_STORAGE_KEY = "cleanops.robot-operations.session.v1";
export const FLOATING_POSITION_KEY = "cleanops.robot-operations.position.v1";
export const FLOATING_EXPANDED_KEY = "cleanops.robot-operations.expanded.v1";
export const FLOATING_SIZE = { width: 352, height: 454, edge: 12 };

export function clampFloatingPosition(position: FloatingPosition, viewport: { width: number; height: number }, size = FLOATING_SIZE): FloatingPosition {
  const x = Number.isFinite(position.x) ? position.x : size.edge;
  const y = Number.isFinite(position.y) ? position.y : size.edge;
  return {
    x: Math.min(Math.max(size.edge, x), Math.max(size.edge, viewport.width - size.width - size.edge)),
    y: Math.min(Math.max(size.edge, y), Math.max(size.edge, viewport.height - size.height - size.edge)),
  };
}

export function defaultFloatingPosition(viewport: { width: number; height: number }): FloatingPosition {
  return clampFloatingPosition({ x: FLOATING_SIZE.edge, y: viewport.height - FLOATING_SIZE.height - FLOATING_SIZE.edge }, viewport);
}

export function parseStoredPosition(value: string | null, viewport: { width: number; height: number }): FloatingPosition | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value) as Partial<FloatingPosition>;
    return typeof parsed.x === "number" && typeof parsed.y === "number" && Number.isFinite(parsed.x) && Number.isFinite(parsed.y) ? clampFloatingPosition(parsed as FloatingPosition, viewport) : null;
  } catch { return null; }
}

export function taskStatusLabel(status: string): string {
  return ({ CREATED: "已创建", ASSIGNED: "已分配", DETECTED: "已发现", EDGE_DETECTED: "边缘识别完成", CLOUD_REVIEW: "云端研判", LOCATED: "已定位", NAVIGATING: "行驶中", ARRIVED: "已到达", CLEANING_COMPLETED: "清洁完成", VERIFYING: "验收中", HUMAN_FALLBACK: "人工兜底", HUMAN_REVIEW: "人工复核", PAUSED: "已暂停", CANCELLED: "已取消", CLOSED: "已完成", FAILED: "失败", TO_PICKUP: "前往取件", ARRIVED_PICKUP: "已到取件点", PICKED_UP: "已取件", ELEVATOR_TRANSIT: "电梯通行", TO_DESTINATION: "前往目的地", DELIVERED: "已送达" } as Record<string, string>)[status] ?? status;
}

export function taskKindLabel(kind: string): string {
  return ({ cleaning: "清洁任务", delivery: "配送任务", relocation: "待命调度" } as Record<string, string>)[kind] ?? kind;
}

/** Customer-name projection only; selection remains the backend Task's robot_id. */
export function taskRobotLabel(robotId?: string | null): string {
  if (!robotId) return "待系统分配";
  return ({ "robot-a": "赛特净界 S5", "robot-b": "高仙 Omnie", "robot-c": "蜗小白 SC50", "robot-d": "普渡 FlashBot Max" } as Record<string, string>)[robotId] ?? robotId;
}

export type OperationsTaskAction = "dispatch" | "pause" | "resume" | "cancel" | "advance" | "manual_complete";

export function actionLabel(action: OperationsTaskAction): string {
  return ({ dispatch: "派发", pause: "暂停", resume: "继续", cancel: "取消", advance: "推进 PoC 模拟", manual_complete: "确认人工完成并验收" })[action];
}

export function taskActions(task: OperationsTask): OperationsTaskAction[] {
  if (task.kind === "cleaning" && task.status === "HUMAN_FALLBACK") return ["manual_complete"];
  if (["CLOSED", "CANCELLED", "FAILED", "HUMAN_REVIEW", "HUMAN_FALLBACK"].includes(task.status)) return [];
  if (task.status === "CREATED") return ["dispatch", "cancel"];
  if (task.status === "PAUSED") return ["resume", "cancel"];
  if (task.status === "ASSIGNED") return ["pause", "cancel", "advance"];
  if (task.kind === "delivery" && ["TO_PICKUP", "ARRIVED_PICKUP", "PICKED_UP", "ELEVATOR_TRANSIT", "TO_DESTINATION", "DELIVERED"].includes(task.status)) return ["pause", "cancel", "advance"];
  if (task.kind === "relocation" && ["NAVIGATING", "ARRIVED"].includes(task.status)) return ["pause", "cancel", "advance"];
  if (task.kind === "cleaning" && ["DETECTED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATED", "NAVIGATING", "ARRIVED", "CLEANING_COMPLETED"].includes(task.status)) return ["pause", "cancel", "advance"];
  return [];
}

/** The task repository returns newest first; never reverse and hide the active work item. */
export function recentTasks(tasks: OperationsTask[], limit = 3): OperationsTask[] {
  return tasks.slice(0, Math.max(0, limit));
}

/**
 * Archive contexts deliberately accept only archive-owned facts. This prevents
 * a previous Workbench event from leaking into an Event Center Agent request.
 */
export function archivePageContext(
  selectedEventId: string | null,
  selectedHistorySnapshot: unknown,
  filters: Record<string, unknown>,
): Record<string, unknown> {
  const raw = selectedHistorySnapshot && typeof selectedHistorySnapshot === "object" ? selectedHistorySnapshot as Record<string, unknown> : null;
  // Full Cloud/tool histories can exceed the request budget. Context carries
  // identity + compact facts; detailed answers must use authoritative read tools.
  const snapshot = raw ? Object.fromEntries(["event_id", "state", "status", "location", "task_profile", "mode", "camera_id", "source"].filter((key) => key in raw).map((key) => [key, raw[key]])) : null;
  return {
    page: "events",
    selected_event_id: selectedEventId,
    selected_history_snapshot: snapshot,
    archive_filters: { ...filters },
  };
}

export function adviceWindowLabel(value: AdviceSnapshot["data_window"]): string {
  return `${value.start} 至 ${value.end} · ${value.days} 天`;
}

/** Task mutations are explicitly scoped to the persisted shared Agent session. */
export function operationSessionHeaders(sessionId: string): Record<string, string> {
  return { "X-Operations-Session": sessionId };
}

export function readStorage(key: string): string | null { try { return localStorage.getItem(key); } catch { return null; } }
export function writeStorage(key: string, value: string): void { try { localStorage.setItem(key, value); } catch { /* UI persistence is optional in private mode. */ } }
