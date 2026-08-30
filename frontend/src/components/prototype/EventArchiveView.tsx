import { AlertCircle, ChevronLeft, ChevronRight, Clock3, Filter, History, Search } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { EventDetailPanel } from "./EventDetailPanel";
import { customerTerm, fromStoredEvent } from "./eventViewModel";
import {
  ARCHIVE_CATEGORIES, DEFAULT_ARCHIVE_FILTERS, EMPTY_COUNTS, archivePageKey, archiveQuery,
  archiveTimestampMs, archiveUrlWithSelection, canRenderArchiveDetail, durationLabel, eventTypeLabel, nextKnownEventBatch, parseArchiveSelection, structuralLocationLabel,
  type ArchiveCounts, type ArchiveFilters, type ArchiveItem, type ArchiveResponse, type HandlingMode,
} from "./eventArchiveModel";
import type { ActiveEvent } from "./types";

const POLL_INTERVAL_MS = 1500;
const EVENT_TYPES = ["", "small_litter", "liquid", "can", "large_object"];
const HANDLING_MODES: Array<{ id: HandlingMode; label: string }> = [
  { id: "", label: "全部处置方式" }, { id: "robot", label: "机器人自主处置" },
  { id: "human_fallback", label: "人工兜底" }, { id: "human_review", label: "人工复核" }, { id: "system_error", label: "系统异常" },
];

function urlHere() { return `${window.location.pathname}${window.location.search}${window.location.hash}`; }
function formatTime(value?: string) { const timestamp = archiveTimestampMs(value); return Number.isFinite(timestamp) ? new Date(timestamp).toLocaleString("zh-CN", { hour12: false, month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—"; }
function locationLabel(item: ArchiveItem) {
  const zoneAliases: Record<string, string> = { "East Road": "东侧道路" };
  const translatedZone = item.location.zone ? customerTerm(item.location.zone) : "";
  const zone = item.location.zone ? (zoneAliases[item.location.zone] ?? (translatedZone === "未归类 / 待复核" ? item.location.zone : translatedZone)) : "";
  const parts = [
    structuralLocationLabel(item.location.building, "building"),
    structuralLocationLabel(item.location.floor, "floor"),
    zone,
  ].filter(Boolean);
  return [...new Set(parts)].join(" · ") || "位置待确认";
}

function statusTone(item: ArchiveItem) {
  if (item.category === "exception") return "border-rose-200 bg-rose-50 text-rose-700";
  if (item.category === "human_pending") return "border-amber-200 bg-amber-50 text-amber-800";
  if (item.category === "autonomous_closed") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

function EventRow({ item, selected, onSelect }: { item: ArchiveItem; selected: boolean; onSelect: (eventId: string) => void }) {
  return <button type="button" onClick={() => onSelect(item.event_id)} className={`w-full border-b border-slate-100 px-4 py-3 text-left transition-colors ${selected ? "bg-slate-100/90 shadow-[inset_2px_0_0_#334155]" : "bg-white hover:bg-slate-50"}`}>
    <div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="truncate text-[13px] font-semibold text-slate-800">{eventTypeLabel(item.event_type)}</p><p className="mt-1 truncate text-[11px] text-slate-500">{locationLabel(item)}</p></div><span className={`shrink-0 border px-1.5 py-0.5 text-[10px] font-medium ${statusTone(item)}`}>{item.status_label || item.status}</span></div>
    <div className="mt-2 flex min-w-0 items-center gap-2 overflow-hidden text-[10px] text-slate-500"><span className="shrink-0 font-mono text-slate-400">{item.camera_id || "CAM —"}</span><span className="h-3 w-px shrink-0 bg-slate-200" /><span className="truncate">发现 {formatTime(item.discovered_at)}</span><span className="h-3 w-px shrink-0 bg-slate-200" /><span className="truncate">{item.executor || "系统处理中"} · {durationLabel(item.duration_seconds)}</span></div>
  </button>;
}

function EmptyDetail({ loading, error }: { loading: boolean; error: string | null }) {
  return <aside className="flex h-full min-h-[460px] flex-col items-center justify-center border border-slate-200 bg-white px-10 text-center"><History size={20} className="text-slate-300" /><p className="mt-3 text-sm font-medium text-slate-700">{loading ? "正在读取事件快照" : error ? "事件快照暂不可读取" : "选择一条事件查看处置档案"}</p><p className={`mt-1.5 text-xs leading-5 ${error ? "text-amber-700" : "text-slate-500"}`}>{error ?? "详情只读取事件发生时的 AI、调度、路线、机器人与验收快照，不会触发重跑。"}</p></aside>;
}

/** Read-only P1-D archive. Runtime mutation and model calls remain outside this view. */
export function EventArchiveView() {
  const [filters, setFilters] = useState<ArchiveFilters>(DEFAULT_ARCHIVE_FILTERS);
  const [items, setItems] = useState<ArchiveItem[]>([]);
  const [counts, setCounts] = useState<ArchiveCounts>(EMPTY_COUNTS);
  const [total, setTotal] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(() => parseArchiveSelection(urlHere()));
  const [detail, setDetail] = useState<ActiveEvent | null>(null);
  const [detailEventId, setDetailEventId] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(Boolean(selectedId));
  const [detailError, setDetailError] = useState<string | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [newCount, setNewCount] = useState(0);
  const knownIds = useRef<Set<string>>(new Set());
  const didLoadForKey = useRef<string | null>(null);
  const listRequest = useRef(0);
  const detailRequest = useRef(0);
  const pageKey = useMemo(() => archivePageKey(filters), [filters]);

  const selectEvent = useCallback((eventId: string | null, historyMode: "push" | "replace" = "push") => {
    setSelectedId(eventId);
    const url = archiveUrlWithSelection(urlHere(), eventId);
    window.history[historyMode === "push" ? "pushState" : "replaceState"]({}, "", url);
  }, []);

  useEffect(() => {
    const onPopState = () => setSelectedId(parseArchiveSelection(urlHere()));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    let active = true;
    const requestId = ++listRequest.current;
    const controller = new AbortController();
    let inFlight = false;
    const load = async () => {
      if (inFlight) return;
      inFlight = true;
      try {
        const response = await fetch(`/api/event-archive?${archiveQuery(filters).toString()}`, { signal: controller.signal });
        if (!response.ok) throw new Error(`archive ${response.status}`);
        const payload = await response.json() as ArchiveResponse;
        if (!active || requestId !== listRequest.current) return;
        const incoming = Array.isArray(payload.items) ? payload.items : [];
        if (didLoadForKey.current === pageKey) {
          const batch = nextKnownEventBatch(knownIds.current, incoming);
          knownIds.current = batch.knownIds;
          setNewCount((previous) => previous + batch.added);
        } else { knownIds.current = new Set(incoming.map((item) => item.event_id)); didLoadForKey.current = pageKey; setNewCount(0); }
        setItems(incoming); setCounts(payload.counts ?? EMPTY_COUNTS); setTotal(payload.total ?? 0); setListError(null);
      } catch (error) {
        if (active && !controller.signal.aborted) setListError("事件列表暂时无法刷新；当前档案选择未改变。");
      } finally {
        inFlight = false;
      }
    };
    void load();
    const timer = window.setInterval(() => void load(), POLL_INTERVAL_MS);
    return () => { active = false; controller.abort(); window.clearInterval(timer); };
  }, [pageKey, filters]);

  useEffect(() => {
    if (!selectedId) { setDetail(null); setDetailEventId(null); setDetailError(null); setDetailLoading(false); return; }
    let active = true;
    const requestId = ++detailRequest.current;
    const controller = new AbortController();
    setDetailLoading(true);
    setDetailError(null);
    void fetch(`/api/events/${encodeURIComponent(selectedId)}`, { signal: controller.signal })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error(`event ${response.status}`)))
      .then((stored) => { if (active && requestId === detailRequest.current) { setDetail(fromStoredEvent(stored)); setDetailEventId(selectedId); setDetailError(null); } })
      .catch(() => {
        if (active && !controller.signal.aborted && requestId === detailRequest.current) {
          setDetailError(detailEventId
            ? `无法读取请求的事件 ${selectedId}；详情区域保持打开，但不会展示其他事件的历史快照。`
            : `无法读取请求的事件 ${selectedId}；该事件可能不存在或暂不可用。`);
        }
      })
      .finally(() => { if (active && requestId === detailRequest.current) setDetailLoading(false); });
    return () => { active = false; controller.abort(); };
  }, [selectedId]);

  const updateFilters = (patch: Partial<ArchiveFilters>) => setFilters((previous) => ({ ...previous, ...patch, offset: patch.offset ?? 0 }));
  const offsetEnd = Math.min(filters.offset + filters.limit, total);
  const hasMatchingDetail = canRenderArchiveDetail(selectedId, detailEventId);

  return <main className="min-h-full bg-[#f6f7f8] px-5 py-5 text-slate-800" aria-label="AI 事件处置档案中心">
    <div className="mx-auto max-w-[1540px]"><header className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><p className="text-[10px] font-semibold tracking-[0.16em] text-slate-400">AI EVENT HANDLING ARCHIVE CENTER</p><h1 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">AI 事件处置档案中心</h1><p className="mt-1 text-xs text-slate-500">只读处置档案 · 同一 CleaningEvent / SQLite 快照 · 不触发模型、调度或机器人重跑</p></div><div className="flex items-center gap-2 text-[11px] text-slate-500"><Clock3 size={14} />默认按发现时间倒序</div></header>
      <section className="border border-slate-200 bg-white"><div className="flex flex-wrap items-center gap-1 border-b border-slate-200 px-3 py-2" role="tablist" aria-label="事件分类">{ARCHIVE_CATEGORIES.map((category) => <button key={category.id} type="button" role="tab" aria-selected={filters.category === category.id} onClick={() => updateFilters({ category: category.id })} className={`px-2.5 py-1.5 text-[11px] font-medium transition-colors ${filters.category === category.id ? "bg-slate-800 text-white" : "text-slate-500 hover:bg-slate-100 hover:text-slate-800"}`}>{category.label}<span className={`ml-1.5 font-mono text-[10px] ${filters.category === category.id ? "text-slate-300" : "text-slate-400"}`}>{counts[category.id] ?? 0}</span></button>)}</div>
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 px-3 py-2"><label className="flex min-w-[230px] flex-1 items-center gap-2 border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-slate-500"><Search size={14} /><input aria-label="搜索事件档案" value={filters.q} onChange={(event) => updateFilters({ q: event.target.value })} placeholder="搜索类型、摄像头、楼栋楼层、机器人或事件 ID" className="min-w-0 flex-1 bg-transparent text-xs text-slate-700 outline-none placeholder:text-slate-400" /></label><label className="flex items-center gap-1.5 text-[11px] text-slate-500"><Filter size={13} /><span className="sr-only">事件类型</span><select aria-label="事件类型" value={filters.eventType} onChange={(event) => updateFilters({ eventType: event.target.value })} className="border border-slate-200 bg-white px-2 py-1.5 text-[11px] text-slate-700 outline-none">{EVENT_TYPES.map((type) => <option key={type || "all"} value={type}>{type ? eventTypeLabel(type) : "全部事件类型"}</option>)}</select></label><label className="flex items-center gap-1.5 text-[11px] text-slate-500"><span>处置方式</span><select aria-label="处置方式" value={filters.handlingMode} onChange={(event) => updateFilters({ handlingMode: event.target.value as HandlingMode })} className="border border-slate-200 bg-white px-2 py-1.5 text-[11px] text-slate-700 outline-none">{HANDLING_MODES.map((mode) => <option key={mode.id || "all"} value={mode.id}>{mode.label}</option>)}</select></label><label className="text-[11px] text-slate-500">起始 <input type="datetime-local" value={filters.since} onChange={(event) => updateFilters({ since: event.target.value })} className="ml-1 border border-slate-200 px-1.5 py-1 text-[11px] text-slate-700" /></label><label className="text-[11px] text-slate-500">结束 <input type="datetime-local" value={filters.until} onChange={(event) => updateFilters({ until: event.target.value })} className="ml-1 border border-slate-200 px-1.5 py-1 text-[11px] text-slate-700" /></label></div>
        {newCount > 0 && <div className="flex items-center justify-between border-b border-sky-100 bg-sky-50 px-4 py-2 text-xs text-sky-800"><span>有 {newCount} 条新事件已进入档案列表；当前查看的历史详情未改变。</span><button type="button" onClick={() => setNewCount(0)} className="font-medium underline underline-offset-2">已查看</button></div>}
        {listError && <div className="flex items-center gap-2 border-b border-amber-100 bg-amber-50 px-4 py-2 text-xs text-amber-800"><AlertCircle size={14} />{listError}</div>}
        <div className="grid h-[calc(100vh-245px)] min-h-[460px] grid-cols-[minmax(0,1fr)_44%] overflow-hidden"><section className="flex min-h-0 min-w-0 flex-col border-r border-slate-200"><div className="flex items-center justify-between border-b border-slate-100 px-4 py-2"><p className="text-[11px] font-medium text-slate-500">事件档案 <span className="font-mono text-slate-400">{total}</span></p><p className="text-[10px] text-slate-400">两级紧凑视图</p></div><div className="min-h-0 flex-1 overflow-y-auto">{items.length ? items.map((item) => <EventRow key={item.event_id} item={item} selected={item.event_id === selectedId} onSelect={selectEvent} />) : <div className="flex min-h-[400px] flex-col items-center justify-center px-8 text-center"><History size={20} className="text-slate-300" /><p className="mt-3 text-sm text-slate-600">当前筛选下没有事件档案</p><p className="mt-1 text-xs text-slate-400">调整筛选条件或等待新的 CleaningEvent 写入。</p></div>}</div><div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-[11px] text-slate-500"><span>{total ? `${filters.offset + 1}–${offsetEnd} / ${total}` : "0 / 0"}</span><div className="flex gap-1"><button type="button" aria-label="上一页事件档案" disabled={filters.offset === 0} onClick={() => updateFilters({ offset: Math.max(0, filters.offset - filters.limit) })} className="border border-slate-200 p-1 disabled:cursor-not-allowed disabled:opacity-40"><ChevronLeft size={14} /></button><button type="button" aria-label="下一页事件档案" disabled={offsetEnd >= total} onClick={() => updateFilters({ offset: filters.offset + filters.limit })} className="border border-slate-200 p-1 disabled:cursor-not-allowed disabled:opacity-40"><ChevronRight size={14} /></button></div></div></section>
          <section className="min-h-0 min-w-0 overflow-hidden bg-slate-50/60">{detail && hasMatchingDetail ? <div className="relative h-full overflow-hidden"><EventDetailPanel event={detail} mode="history" />{detailLoading && <div className="absolute right-3 top-3 border border-slate-200 bg-white px-2 py-1 text-[10px] text-slate-500 shadow-sm">正在更新快照…</div>}{detailError && <div role="alert" className="absolute bottom-3 left-3 right-3 border border-amber-200 bg-amber-50 px-2.5 py-2 text-[11px] leading-5 text-amber-800 shadow-sm">{detailError}</div>}</div> : <EmptyDetail loading={detailLoading} error={detailError} />}</section></div>
      </section></div>
  </main>;
}
