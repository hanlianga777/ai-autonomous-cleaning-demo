import { fromStoredEvent, type RecordValue } from "./eventViewModel";
import type { ActiveEvent } from "./types";

/** Reloads are GET-only. The browser stores IDs/request guards, not business facts. */
export async function loadEventSnapshot(eventId: string, signal?: AbortSignal, request: typeof fetch = fetch): Promise<ActiveEvent> {
  const response = await request(`/api/events/${encodeURIComponent(eventId)}`, { signal });
  if (!response.ok) throw new Error("无法恢复已保存事件；服务或事件记录暂不可用。");
  return fromStoredEvent(await response.json());
}

export function canApplySnapshot(current: ActiveEvent, result: RecordValue): boolean {
  if (current.liveResult?.event_id && result.event_id !== current.liveResult.event_id) return false;
  const currentCount = Array.isArray(current.liveResult?.transitions) ? current.liveResult.transitions.length : 0;
  return !Array.isArray(result.transitions) || result.transitions.length >= currentCount;
}

export function readRequestKeys(serialized: string | null): Set<string> {
  try { const value = JSON.parse(serialized ?? "[]"); return new Set(Array.isArray(value) ? value.filter((item) => typeof item === "string") : []); }
  catch { return new Set(); }
}

export function claimStage(keys: Set<string>, eventId: string, action: string): boolean {
  const key = `${eventId}:${action}`;
  if (keys.has(key)) return false;
  keys.add(key);
  return true;
}
