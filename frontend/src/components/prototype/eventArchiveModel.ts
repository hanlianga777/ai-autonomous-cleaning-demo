/** Pure API and URL helpers for the read-only Event Center. */

export type ArchiveCategory = "all" | "in_progress" | "autonomous_closed" | "human_pending" | "exception";
/** Backend items may retain terminal subclasses; tabs intentionally remain the five categories above. */
export type ArchiveItemCategory = ArchiveCategory | "human_closed" | "other_closed";
export type HandlingMode = "" | "robot" | "human_fallback" | "human_review" | "system_error";

export type ArchiveItem = {
  event_id: string;
  event_type: string;
  camera_id: string;
  location: { building?: string; floor?: string; zone?: string; map_id?: string; x?: number; y?: number };
  discovered_at: string;
  updated_at: string;
  status: string;
  status_label: string;
  category: ArchiveItemCategory;
  handling_mode: HandlingMode;
  executor?: string | null;
  duration_seconds?: number | null;
  mode?: string;
};

export type ArchiveCounts = Record<ArchiveCategory, number>;
export type ArchiveResponse = { items: ArchiveItem[]; total: number; counts: ArchiveCounts; generated_at: string };

export type ArchiveFilters = {
  category: ArchiveCategory;
  q: string;
  eventType: string;
  handlingMode: HandlingMode;
  since: string;
  until: string;
  mapId: string;
  offset: number;
  limit: number;
};

export const ARCHIVE_CATEGORIES: Array<{ id: ArchiveCategory; label: string }> = [
  { id: "all", label: "全部" },
  { id: "in_progress", label: "处理中" },
  { id: "autonomous_closed", label: "已自主闭环" },
  { id: "human_pending", label: "待人工处理" },
  { id: "exception", label: "异常" },
];

export const EMPTY_COUNTS: ArchiveCounts = { all: 0, in_progress: 0, autonomous_closed: 0, human_pending: 0, exception: 0 };
export const DEFAULT_ARCHIVE_FILTERS: ArchiveFilters = { category: "all", q: "", eventType: "", handlingMode: "", since: "", until: "", mapId: "", offset: 0, limit: 50 };

export function eventTypeLabel(value: string): string {
  return ({ small_litter: "其他小型垃圾", liquid: "液体污渍", can: "易拉罐", large_object: "大件物品", leaf: "树叶", unknown: "待复核" } as Record<string, string>)[value] ?? (value || "待复核");
}

/** Structural location identifiers are not semantic enum values and must stay legible. */
export function structuralLocationLabel(value: string | undefined, part: "building" | "floor"): string {
  const text = value?.trim() ?? "";
  if (!text) return "";
  if (/^outdoor$/i.test(text)) return "室外";
  if (part === "building" && /^[A-Z]$/.test(text)) return `${text}栋`;
  return text;
}

export function durationLabel(value?: number | null): string {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) return "进行中";
  if (value < 60) return `${Math.round(value)} 秒`;
  const minutes = Math.floor(value / 60);
  const seconds = Math.round(value % 60);
  return seconds ? `${minutes} 分 ${seconds} 秒` : `${minutes} 分`;
}

/** SQLite CURRENT_TIMESTAMP has no offset; archive timestamps are persisted UTC. */
export function archiveTimestampMs(value?: string): number {
  if (!value) return Number.NaN;
  const normalized = value.replace(" ", "T");
  return Date.parse(/Z$|[+-]\d\d:\d\d$/.test(normalized) ? normalized : `${normalized}Z`);
}

/** `datetime-local` has no offset. Convert the operator's local wall time before requesting UTC SQLite records. */
export function localDateTimeToUtcIso(value: string): string {
  if (!value) return "";
  const timestamp = new Date(value).getTime();
  return Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : "";
}

export function archiveQuery(filters: ArchiveFilters): URLSearchParams {
  const query = new URLSearchParams();
  query.set("category", filters.category);
  query.set("offset", String(Math.max(0, filters.offset)));
  query.set("limit", String(filters.limit));
  const values: Array<[string, string]> = [
    ["q", filters.q.trim()], ["event_type", filters.eventType], ["handling_mode", filters.handlingMode],
    ["since", localDateTimeToUtcIso(filters.since)], ["until", localDateTimeToUtcIso(filters.until)], ["map_id", filters.mapId],
  ];
  values.forEach(([key, value]) => { if (value) query.set(key, value); });
  return query;
}

export function parseArchiveSelection(url: string): string | null {
  try {
    const event = new URL(url, "http://event-center.local").searchParams.get("event");
    return event?.trim() || null;
  } catch { return null; }
}

/** Preserve any future location/time query while updating only the selected event. */
export function archiveUrlWithSelection(url: string, eventId: string | null): string {
  const parsed = new URL(url, "http://event-center.local");
  if (eventId) parsed.searchParams.set("event", eventId);
  else parsed.searchParams.delete("event");
  return `${parsed.pathname}${parsed.search}${parsed.hash}`;
}

export function archiveFilterKey(filters: ArchiveFilters): string {
  return archiveQuery({ ...filters, offset: 0 }).toString();
}

/** Pagination has its own visible slice, so it must not inherit a "new" banner from another page. */
export function archivePageKey(filters: ArchiveFilters): string {
  return archiveQuery(filters).toString();
}

/** A stale detail response may remain in memory, but it must never render for a newer selection. */
export function canRenderArchiveDetail(selectedEventId: string | null, detailEventId: string | null): boolean {
  return Boolean(selectedEventId && detailEventId && selectedEventId === detailEventId);
}

export function countNewEvents(previousIds: Set<string>, next: ArchiveItem[]): number {
  return next.reduce((count, item) => count + (previousIds.has(item.event_id) ? 0 : 1), 0);
}

/** Produce the poll result before React schedules any state updater. */
export function nextKnownEventBatch(previousIds: Set<string>, next: ArchiveItem[]): { added: number; knownIds: Set<string> } {
  return { added: countNewEvents(previousIds, next), knownIds: new Set([...previousIds, ...next.map((item) => item.event_id)]) };
}
