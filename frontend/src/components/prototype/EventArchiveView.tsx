import { AlertCircle, ChevronLeft, ChevronRight, History, Search } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { EventDetailPanel } from "./EventDetailPanel";
import { customerTerm, fromStoredEvent } from "./eventViewModel";
import {
  ARCHIVE_CATEGORIES, EMPTY_COUNTS, archivePageKey, archiveQuery,
  archiveDateTimeInputValue, archiveTimestampMs, archiveUrlWithSelection, canRenderArchiveDetail, eventTypeLabel, isDemoEntry, nextKnownEventBatch, parseArchiveFilters, parseArchiveSelection, structuralLocationLabel,
  type ArchiveCounts, type ArchiveFilters, type ArchiveItem, type ArchiveResponse, type HandlingMode,
} from "./eventArchiveModel";
import type { ActiveEvent } from "./types";
import { archivePageContext } from "@/components/robot-operations/robotOperationsModel";

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
  const rawZone = item.location.zone ? (zoneAliases[item.location.zone] ?? (translatedZone === "未归类 / 待复核" ? item.location.zone : translatedZone)) : "";
  const building = structuralLocationLabel(item.location.building, "building");
  const floor = structuralLocationLabel(item.location.floor, "floor");
  // Persisted zone labels may already carry their structural prefix (for
  // example “A 栋 1F · 东入口”). Keep the business location once, not twice.
  const zone = rawZone
    .replace(/^(?:园区室外\s*[·-]?\s*)/u, "")
    .replace(/^[AB]\s*栋\s*[12]F\s*[·-]?\s*/u, "");
  const parts = [
    building,
    floor,
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
  return <button type="button" onClick={() => onSelect(item.event_id)} className={`grid w-full grid-cols-[1.2fr_.9fr_1.2fr_1fr_.9fr] items-center gap-3 border-b border-slate-100 px-4 py-3 text-left text-[12px] transition-colors ${selected ? "bg-slate-100/90 shadow-[inset_2px_0_0_#334155]" : "bg-white hover:bg-slate-50"}`}>
    <p className="truncate font-semibold text-slate-800">{eventTypeLabel(item.event_type)}</p><time className="truncate text-slate-500">{formatTime(item.discovered_at)}</time><p className="truncate text-slate-600">{locationLabel(item)}</p><p className="truncate text-slate-600">{item.executor || "系统处理中"}</p><span className={`justify-self-start border px-1.5 py-0.5 font-medium ${statusTone(item)}`}>{item.status_label || item.status}</span>
  </button>;
}

function EmptyDetail({ loading, error }: { loading: boolean; error: string | null }) {
  return <aside className="flex h-full min-h-[460px] flex-col items-center justify-center border border-slate-200 bg-white px-10 text-center"><History size={20} className="text-slate-300" /><p className="mt-3 text-sm font-medium text-slate-700">{loading ? "正在读取事件快照" : error ? "事件快照暂不可读取" : "选择一条事件查看处置档案"}</p><p className={`mt-1.5 text-xs leading-5 ${error ? "text-amber-700" : "text-slate-500"}`}>{error ?? "详情只读取事件发生时的 AI、调度、路线、机器人与验收快照，不会触发重跑。"}</p></aside>;
}

/** Read-only P1-D archive. Runtime mutation and model calls remain outside this view. */
export function EventArchiveView({ onAgentContextChange }: { onAgentContextChange?: (context: Record<string, unknown>) => void }) {
  const [filters, setFilters] = useState<ArchiveFilters>(() => parseArchiveFilters(urlHere()));
  const [items, setItems] = useState<ArchiveItem[]>([]);
  const [counts, setCounts] = useState<ArchiveCounts>(EMPTY_COUNTS);
  const [total, setTotal] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(() => parseArchiveSelection(urlHere()));
  const [demoEntry, setDemoEntry] = useState(() => isDemoEntry(urlHere()));
  const [detail, setDetail] = useState<ActiveEvent | null>(null);
  const [detailEventId, setDetailEventId] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(Boolean(selectedId));
  const [detailError, setDetailError] = useState<string | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [newCount, setNewCount] = useState(0);
  const knownIds = useRef<Set<string>>(new Set());
  const selectedIdRef = useRef(selectedId);
  const didLoadForKey = useRef<string | null>(null);
  const listRequest = useRef(0);
  const detailRequest = useRef(0);
  const pageKey = useMemo(() => archivePageKey(filters), [filters]);

  const selectEvent = useCallback((eventId: string | null, historyMode: "push" | "replace" = "push") => {
    selectedIdRef.current = eventId;
    setSelectedId(eventId);
    const parsed = new URL(archiveUrlWithSelection(urlHere(), eventId), window.location.origin);
    parsed.searchParams.delete("entry");
    const url = `${parsed.pathname}${parsed.search}${parsed.hash}`;
    setDemoEntry(false);
    window.history[historyMode === "push" ? "pushState" : "replaceState"]({}, "", url);
  }, []);

  useEffect(() => {
    const onPopState = () => { const nextSelection = parseArchiveSelection(urlHere()); selectedIdRef.current = nextSelection; setSelectedId(nextSelection); setFilters(parseArchiveFilters(urlHere())); setDemoEntry(isDemoEntry(urlHere())); };
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
        if (!selectedIdRef.current && incoming[0]) selectEvent(incoming[0].event_id, "replace");
      } catch (error) {
        if (active && !controller.signal.aborted) setListError("事件列表暂时无法刷新；当前档案选择未改变。");
      } finally {
        inFlight = false;
      }
    };
    void load();
    const timer = window.setInterval(() => void load(), POLL_INTERVAL_MS);
    return () => { active = false; controller.abort(); window.clearInterval(timer); };
  }, [pageKey, filters, selectEvent]);

  useEffect(() => {
    if (!selectedId) { setDetail(null); setDetailEventId(null); setDetailError(null); setDetailLoading(false); return; }
    let active = true;
    const requestId = ++detailRequest.current;
    const controller = new AbortController();
    setDetailLoading(true);
    setDetailError(null);
    void fetch(`/api/event-archive/${encodeURIComponent(selectedId)}`, { signal: controller.signal })
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

  useEffect(() => {
    onAgentContextChange?.(archivePageContext(
      selectedId,
      detailEventId === selectedId ? detail?.liveResult ?? null : null,
      filters as unknown as Record<string, unknown>,
    ));
  }, [detail?.liveResult, detailEventId, filters, onAgentContextChange, selectedId]);

  return <main className="min-h-full bg-[#f6f7f8] px-5 py-5 text-slate-800" aria-label="事件中心">
    <div className="mx-auto max-w-[1540px]"><header className="mb-4"><h1 className="text-xl font-semibold tracking-tight text-slate-900">事件中心</h1></header>
      <section className="surface-card overflow-hidden border border-slate-200 bg-white"><div className="flex flex-wrap items-center gap-2 border-b border-slate-100 px-3 py-2"><label className="surface-control flex min-w-[230px] flex-1 items-center gap-2 border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-slate-500"><Search size={14} /><input aria-label="搜索事件" value={filters.q} onChange={(event) => updateFilters({ q: event.target.value })} placeholder="搜索事件类型或发生位置" className="min-w-0 flex-1 bg-transparent text-xs text-slate-700 outline-none placeholder:text-slate-400" /></label><label className="text-[12px] text-slate-500">事件类型 <select aria-label="事件类型" value={filters.eventType} onChange={(event) => updateFilters({ eventType: event.target.value })} className="ml-1 border border-slate-200 bg-white px-2 py-1.5 text-[12px] text-slate-700 outline-none">{EVENT_TYPES.map((type) => <option key={type || "all"} value={type}>{type ? eventTypeLabel(type) : "全部"}</option>)}</select></label><label className="text-[12px] text-slate-500">处置方式 <select aria-label="处置方式" value={filters.handlingMode} onChange={(event) => updateFilters({ handlingMode: event.target.value as HandlingMode })} className="ml-1 border border-slate-200 bg-white px-2 py-1.5 text-[12px] text-slate-700 outline-none">{HANDLING_MODES.map((mode) => <option key={mode.id || "all"} value={mode.id}>{mode.label}</option>)}</select></label></div>
        {demoEntry && selectedId && <div data-testid="demo-archive-handoff" className="border-b border-emerald-100 bg-emerald-50 px-4 py-2 text-xs leading-5 text-emerald-800">刚完成的演示事件已进入只读档案。这里展示事件发生时保存的 AI、调度、路线与验收快照，不会触发重跑。</div>}
        {newCount > 0 && <div className="flex items-center justify-between border-b border-sky-100 bg-sky-50 px-4 py-2 text-xs text-sky-800"><span>有 {newCount} 条新事件已进入档案列表；当前查看的历史详情未改变。</span><button type="button" onClick={() => setNewCount(0)} className="font-medium underline underline-offset-2">已查看</button></div>}
        {listError && <div className="flex items-center gap-2 border-b border-amber-100 bg-amber-50 px-4 py-2 text-xs text-amber-800"><AlertCircle size={14} />{listError}</div>}
        <div className="grid h-[calc(100vh-180px)] min-h-[460px] grid-cols-[minmax(0,72fr)_minmax(320px,28fr)] overflow-hidden"><section className="flex min-h-0 min-w-0 flex-col border-r border-slate-200"><div className="grid grid-cols-[1.2fr_.9fr_1.2fr_1fr_.9fr] gap-3 border-b border-slate-100 px-4 py-2 text-[12px] font-medium text-slate-400"><span>事件</span><span>发现时间</span><span>地点</span><span>机器人</span><span>工单状态</span></div><div className="min-h-0 flex-1 overflow-y-auto">{items.length ? items.map((item) => <EventRow key={item.event_id} item={item} selected={item.event_id === selectedId} onSelect={selectEvent} />) : <div className="flex min-h-[400px] flex-col items-center justify-center px-8 text-center"><History size={20} className="text-slate-300" /><p className="mt-3 text-sm text-slate-600">当前筛选下没有事件</p></div>}</div><div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-[12px] text-slate-500"><span>{total ? `${filters.offset + 1}–${offsetEnd} / ${total}` : "0 / 0"}</span><div className="flex gap-1"><button type="button" aria-label="上一页事件" disabled={filters.offset === 0} onClick={() => updateFilters({ offset: Math.max(0, filters.offset - filters.limit) })} className="border border-slate-200 p-1 disabled:cursor-not-allowed disabled:opacity-40"><ChevronLeft size={14} /></button><button type="button" aria-label="下一页事件" disabled={offsetEnd >= total} onClick={() => updateFilters({ offset: filters.offset + filters.limit })} className="border border-slate-200 p-1 disabled:cursor-not-allowed disabled:opacity-40"><ChevronRight size={14} /></button></div></div></section>
          <section className="min-h-0 min-w-0 overflow-hidden bg-slate-50/60">{detail && hasMatchingDetail ? <div className="relative h-full overflow-hidden"><EventDetailPanel event={detail} mode="history" />{detailLoading && <div className="absolute right-3 top-3 border border-slate-200 bg-white px-2 py-1 text-[12px] text-slate-500 shadow-sm">正在更新快照…</div>}{detailError && <div role="alert" className="absolute bottom-3 left-3 right-3 border border-amber-200 bg-amber-50 px-2.5 py-2 text-[12px] leading-5 text-amber-800 shadow-sm">{detailError}</div>}</div> : <EmptyDetail loading={detailLoading} error={detailError} />}</section></div>
      </section></div>
  </main>;
}
