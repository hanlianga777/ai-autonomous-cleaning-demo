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
export const FLOATING_POSITION_KEY = "cleanops.robot-operations.position.v2";
export const FLOATING_EXPANDED_KEY = "cleanops.robot-operations.expanded.v2";
export const FLOATING_CHAT_SIZE = { width: 420, height: 560, edge: 16 };
export const FLOATING_BALL_SIZE = { width: 56, height: 56, edge: 16 };
/** Backward-compatible export used by geometry tests: the expanded chat size. */
export const FLOATING_SIZE = FLOATING_CHAT_SIZE;

export function clampFloatingPosition(position: FloatingPosition, viewport: { width: number; height: number }, size = FLOATING_BALL_SIZE): FloatingPosition {
  const x = Number.isFinite(position.x) ? position.x : size.edge;
  const y = Number.isFinite(position.y) ? position.y : size.edge;
  return {
    x: Math.min(Math.max(size.edge, x), Math.max(size.edge, viewport.width - size.width - size.edge)),
    y: Math.min(Math.max(size.edge, y), Math.max(size.edge, viewport.height - size.height - size.edge)),
  };
}

export function defaultFloatingPosition(viewport: { width: number; height: number }): FloatingPosition {
  return clampFloatingPosition({ x: FLOATING_BALL_SIZE.edge, y: viewport.height - FLOATING_BALL_SIZE.height - FLOATING_BALL_SIZE.edge }, viewport);
}

export function parseStoredPosition(value: string | null, viewport: { width: number; height: number }): FloatingPosition | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value) as Partial<FloatingPosition>;
    return typeof parsed.x === "number" && typeof parsed.y === "number" && Number.isFinite(parsed.x) && Number.isFinite(parsed.y) ? clampFloatingPosition(parsed as FloatingPosition, viewport) : null;
  } catch { return null; }
}

export function taskStatusLabel(status: string): string {
  return ({ CREATED: "已创建", ASSIGNED: "已分配", DETECTED: "已发现", EDGE_DETECTED: "边缘识别完成", CLOUD_REVIEW: "云端AI研判", LOCATED: "已定位", NAVIGATING: "机器人前往现场", ARRIVED: "已到达", CLEANING_COMPLETED: "清洁完成", VERIFYING: "验收中", HUMAN_FALLBACK: "人工处置", HUMAN_REVIEW: "待人工复核", PAUSED: "已暂停", CANCELLED: "已取消", CLOSED: "已完成", FAILED: "处理未完成", TO_PICKUP: "前往取件", ARRIVED_PICKUP: "已到取件点", PICKED_UP: "已取件", ELEVATOR_TRANSIT: "电梯通行", TO_DESTINATION: "前往目的地", DELIVERED: "已送达" } as Record<string, string>)[status] ?? "状态待确认";
}

export function taskKindLabel(kind: string): string {
  return ({ cleaning: "清洁任务", delivery: "配送任务", relocation: "待命调度" } as Record<string, string>)[kind] ?? kind;
}

/** Customer-name projection only; selection remains the backend Task's robot_id. */
export function taskRobotLabel(robotId?: string | null): string {
  if (!robotId) return "人工处置";
  return ({ "robot-a": "赛特净界 S5", "robot-b": "高仙 Omnie", "robot-c": "蜗小白 SC50", "robot-d": "普渡 FlashBot Max" } as Record<string, string>)[robotId] ?? "未分配机器人";
}

/** A null cleaning assignee is a human disposition, never a pending robot. */
export function taskExecutorLabel(task: OperationsTask): string {
  if (!task.robot_id) {
    if (task.kind === "cleaning" && ["HUMAN_FALLBACK", "CLOSED"].includes(task.status)) return "处置方式：人工搬运";
    return "执行对象：待调度";
  }
  return `机器人：${taskRobotLabel(task.robot_id)}`;
}

export function taskLocationLabel(value?: string | null): string {
  return ({ "East Corridor": "东侧走廊", "West Lobby": "西侧大堂", "Main Lobby": "主大堂", "Skybridge Entrance": "连廊入口", "Outdoor East Road": "园区东侧道路" } as Record<string, string>)[value ?? ""] ?? value ?? "未提供目的地";
}

/** Render persisted Agent copy safely in the customer shell. Internal IDs and
 * lightweight Markdown tokens can be useful to audits, never to a customer. */
export function customerAgentMessage(value: string): string {
  return value
    .replace(/\*{1,3}|`/g, "")
    .replace(/\brobot-a\b/gi, "赛特净界 S5")
    .replace(/\brobot-b\b/gi, "高仙 Omnie")
    .replace(/\brobot-c\b/gi, "蜗小白 SC50")
    .replace(/\brobot-d\b/gi, "普渡 FlashBot Max")
    .replace(/\bRobot\s*A\b/gi, "赛特净界 S5")
    .replace(/\bRobot\s*B\b/gi, "高仙 Omnie")
    .replace(/\bRobot\s*C\b/gi, "蜗小白 SC50")
    .replace(/\bRobot\s*D\b/gi, "普渡 FlashBot Max")
    .replace(/\b(?:integrated-demo|p\d+e-history)[a-z0-9_-]*\b/gi, "相关业务记录")
    .replace(/\b(?:event|task|session|camera|zone|map)-[a-z0-9_-]+\b/gi, "相关业务记录")
    .replace(/\b[ab]\d-(?:lobby|delivery|corridor|entrance|road|bridge|elevator)[a-z0-9_-]*\b/gi, "对应点位")
    .replace(/\boutdoor-standby\b/gi, "园区室外道路待命点")
    .replace(/\bTask\s*ID\s*:\s*[^\n]*/gi, "本次任务")
    .replace(/\b(?:delivery|cleaning|relocation)\b/gi, (kind) => taskKindLabel(kind.toLowerCase()))
    .replace(/\b(?:CREATED|ASSIGNED|DETECTED|CLOUD_REVIEW|LOCATED|NAVIGATING|ARRIVED|CLEANING_COMPLETED|VERIFYING|PAUSED|CANCELLED|CLOSED|FAILED|TO_PICKUP|ARRIVED_PICKUP|PICKED_UP|ELEVATOR_TRANSIT|TO_DESTINATION|DELIVERED)\b/g, (status) => taskStatusLabel(status))
    .replace(/\b(?:LIVE|MOCK|REPLAY|DEBUG|POC[_\s-]*SIMULATION|HUMAN_FALLBACK|HUMAN_REVIEW|EDGE_DETECTED|MULTI_VIEW|large_object|unknown)\b/gi, "")
    .replace(/\bPOI\b/gi, "点位")
    .replace(/\b(?:zone_id|event_id|camera_id|duration_seconds|average_closure_time_minutes|count)\s*[=:][^；，,\n)]+/gi, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export type OperationsTaskAction = "dispatch" | "pause" | "resume" | "cancel" | "advance" | "manual_complete";

export function actionLabel(action: OperationsTaskAction): string {
  return ({ dispatch: "开始执行", pause: "暂停", resume: "继续", cancel: "取消", advance: "继续任务", manual_complete: "确认人工处置完成" })[action];
}

export function taskActions(task: OperationsTask): OperationsTaskAction[] {
  if (task.kind === "cleaning" && task.status === "HUMAN_FALLBACK") return ["manual_complete"];
  if (["CLOSED", "CANCELLED", "FAILED", "HUMAN_REVIEW", "HUMAN_FALLBACK"].includes(task.status)) return [];
  // Customer tasks are dispatched and progressed by the backend.  Explicit
  // controls intentionally exclude engineering-style Start/Advance actions.
  if (task.status === "CREATED") return ["cancel"];
  if (task.status === "PAUSED") return ["resume", "cancel"];
  if (["ASSIGNED", "DETECTED", "EDGE_DETECTED", "CLOUD_REVIEW", "LOCATED", "NAVIGATING", "ARRIVED", "CLEANING_COMPLETED", "TO_PICKUP", "ARRIVED_PICKUP", "PICKED_UP", "ELEVATOR_TRANSIT", "TO_DESTINATION", "DELIVERED"].includes(task.status)) return ["pause", "cancel"];
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
