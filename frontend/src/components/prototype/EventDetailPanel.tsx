import { Clock3, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { EventStageEvidence } from "./EventStageEvidence";
import { clockLabel, customerTerm, timelineFor, timestampMs } from "./eventViewModel";
import type { ActiveEvent } from "./types";

/** One durable-event renderer: history is read-only, live adds follow + actions. */
export function EventDetailPanel({ event, mode = "live", onCompleteManual }: {
  event: ActiveEvent | null; mode?: "live" | "history"; onCompleteManual?: () => void;
}) {
  const [follow, setFollow] = useState(true);
  const [now, setNow] = useState(Date.now());
  const bodyRef = useRef<HTMLDivElement>(null);
  const timeline = event ? timelineFor(event, mode) : [];
  const currentKey = timeline.map((entry) => `${entry.state}:${entry.pending ? "pending" : "saved"}`).join("|");
  const terminal = ["CLOSED", "HUMAN_REVIEW"].includes(event?.backendState ?? "");
  const scrollToCurrent = () => {
    const panel = bodyRef.current;
    const current = panel?.querySelector<HTMLElement>("[data-current-stage=true]");
    if (panel && current) panel.scrollTo({ top: current.getBoundingClientRect().top - panel.getBoundingClientRect().top + panel.scrollTop - 12, behavior: "smooth" });
  };
  useEffect(() => { setFollow(true); }, [event?.liveResult?.event_id]);
  useEffect(() => { if (mode === "live" && follow) scrollToCurrent(); }, [currentKey, follow, mode]);
  useEffect(() => {
    if (mode === "history" || terminal || !event) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [mode, terminal, Boolean(event)]);
  const start = timestampMs(event?.liveResult?.created_at);
  const end = mode === "history" || terminal ? timestampMs(event?.liveResult?.updated_at) : now;
  const elapsed = Number.isFinite(start) && Number.isFinite(end) ? `${Math.max(0, (end - start) / 1000).toFixed(0)} 秒` : "—";
  // Programmatic smooth scrolling must not disable following. Only user input does.
  const pauseFollow = () => { if (mode === "live") setFollow(false); };
  return <aside data-testid="event-detail-panel" data-mode={mode} className="relative flex h-full min-h-0 flex-col border border-slate-200 bg-white">
    <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-4 py-3">
      <div><p className="text-sm font-semibold">{mode === "history" ? "历史事件详情" : "最近事件处置详情"}</p><p className="mt-0.5 text-[10px] text-slate-500">{mode === "history" ? "事件快照 · 只读 · 不触发重跑" : "真实阶段记录 · 完整处置过程"}</p></div><Clock3 size={16} className="text-slate-400" />
    </div>
    {!event ? <div className="flex flex-1 flex-col items-center justify-center px-8 text-center"><p className="text-sm font-medium text-slate-700">当前没有事件</p><p className="mt-2 text-xs leading-5 text-slate-500">从监控区的摄像头设置中触发演示，即可查看识别、空间定位、派单、执行及验收全过程。</p></div> : <>
      <div className="shrink-0 border-b border-slate-100 px-4 py-3">
        <p className="text-sm font-semibold">{event.scenario.eventTitle}</p>
        <p className="mt-1 text-[10px] text-slate-500">{event.scenario.cameraId} · {clockLabel(event.liveResult?.created_at)} · 耗时 {elapsed}</p>
        <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-slate-600"><span className="border border-slate-200 px-1.5 py-0.5">{customerTerm((event.liveResult?.task_profile as Record<string, unknown>)?.object_type ?? event.scenario.category)}</span><span className="border border-slate-200 px-1.5 py-0.5">{event.liveResult?.mode === "DEMO_HISTORY" ? "演示历史 · 非 LIVE" : event.liveResult?.mode === "STABLE_REPLAY" ? "历史 AI 记录回放" : "LIVE 云端研判"}</span></div>
      </div>
      <div ref={bodyRef} data-testid="event-timeline-scroll" tabIndex={0} onWheel={pauseFollow} onTouchStart={pauseFollow} onPointerDown={pauseFollow} onKeyDown={(e) => { if (["ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End"].includes(e.key)) pauseFollow(); }} className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4">
        {!timeline.length && <p className="text-xs text-slate-500">{event.processing ? "正在创建事件…" : "尚无已保存的阶段记录。"}</p>}
        {timeline.map((entry, index) => <div data-current-stage={index === timeline.length - 1 || undefined} data-stage={entry.state} key={`${entry.state}-${index}`} className="relative border-l border-slate-200 pb-5 pl-4">
          <span className={`absolute -left-[5px] top-1 h-2 w-2 rounded-full ${entry.pending ? "animate-pulse bg-slate-500" : entry.state === "HUMAN_REVIEW" || entry.state === "HUMAN_FALLBACK" ? "bg-amber-500" : "bg-emerald-600"}`} />
          <div className="flex items-start justify-between gap-2"><h3 className="text-xs font-semibold text-slate-800">{entry.label}</h3><span className="whitespace-nowrap text-[10px] text-slate-400">{entry.pending ? "处理中" : clockLabel(entry.timestamp)}</span></div>
          <EventStageEvidence event={event} entry={entry} mode={mode} onCompleteManual={onCompleteManual} />
        </div>)}
        {!event.processing && Boolean(event.liveResult?.reason) && <p className="border-t border-slate-100 pt-2 text-[11px] leading-5 text-slate-500">当前记录：{customerTerm(event.liveResult?.reason)}</p>}
      </div>
      {mode === "live" && !follow && <button onClick={() => { setFollow(true); scrollToCurrent(); }} className="absolute bottom-3 right-3 flex items-center gap-1 border border-slate-300 bg-white px-2 py-1.5 text-[11px] font-medium text-slate-700 shadow-sm"><RotateCcw size={12} />回到当前进度</button>}
    </>}
  </aside>;
}
