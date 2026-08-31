import { useEffect, useRef, useState } from "react";
import { EventStageEvidence } from "./EventStageEvidence";
import { clockLabel, timelineFor, timestampMs } from "./eventViewModel";
import type { ActiveEvent } from "./types";
import { isTerminalEvent } from "./runtimeSession";

/** One durable-event renderer: history is read-only, live adds follow + actions. */
function discoveryTitle(event: ActiveEvent) { return event.scenario.eventTitle.replace(/发现.*$/u, "发现 AI 清洁事件"); }

export function EventDetailPanel({ event, mode = "live", onCompleteManual, onViewArchive }: {
  event: ActiveEvent | null; mode?: "live" | "history"; onCompleteManual?: () => void; onViewArchive?: (eventId: string) => void;
}) {
  const [now, setNow] = useState(Date.now());
  const bodyRef = useRef<HTMLDivElement>(null);
  const timeline = event ? timelineFor(event, mode) : [];
  const currentKey = timeline.map((entry) => `${entry.state}:${entry.pending ? "pending" : "saved"}`).join("|");
  const terminal = isTerminalEvent(event);
  const scrollToCurrent = () => {
    const panel = bodyRef.current;
    const current = panel?.querySelector<HTMLElement>("[data-current-stage=true]");
    if (panel && current) panel.scrollTo({ top: current.getBoundingClientRect().top - panel.getBoundingClientRect().top + panel.scrollTop - 12, behavior: "smooth" });
  };
  useEffect(() => { if (mode === "live") scrollToCurrent(); }, [currentKey, mode]);
  useEffect(() => {
    if (mode === "history" || terminal || !event) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [mode, terminal, Boolean(event)]);
  const start = timestampMs(event?.liveResult?.created_at);
  const end = mode === "history" || terminal ? timestampMs(event?.liveResult?.updated_at) : now;
  const elapsed = Number.isFinite(start) && Number.isFinite(end) ? `${Math.max(0, (end - start) / 1000).toFixed(0)} 秒` : "—";
  return <aside data-testid="event-detail-panel" data-mode={mode} className="relative flex h-full min-h-0 flex-col border border-slate-200 bg-white">
    <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-4 py-3">
      <p className="text-sm font-semibold">{mode === "history" ? "事件处置详情" : "当前事件处置详情"}</p>
    </div>
    {!event ? <div className="flex flex-1 flex-col items-center justify-center px-8 text-center"><p className="text-sm font-medium text-slate-700">园区持续监测中</p><p className="mt-2 text-xs leading-5 text-slate-500">当前没有需要处置的事件。演示员可从监控区右上角的摄像头设置启动案例，查看识别、调度、执行与验收的完整记录。</p></div> : <>
      <div className="shrink-0 border-b border-slate-100 px-4 py-3">
        <p className="text-sm font-semibold">{discoveryTitle(event)}</p>
        <p className="mt-1 text-[12px] text-slate-400">{clockLabel(event.liveResult?.created_at)} · 已用时 {elapsed}</p>
      </div>
      <div ref={bodyRef} data-testid="event-timeline-scroll" tabIndex={0} className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4">
        {!timeline.length && <p className="text-xs text-slate-500">{event.processing ? "正在创建事件…" : "尚无已保存的阶段记录。"}</p>}
        {timeline.map((entry, index) => <div data-current-stage={index === timeline.length - 1 || undefined} data-stage={entry.state} key={`${entry.state}-${index}`} className="relative border-l border-slate-200 pb-5 pl-4">
          <span className={`absolute -left-[5px] top-1 h-2 w-2 rounded-full ${entry.pending ? "animate-pulse bg-slate-500" : entry.state === "HUMAN_REVIEW" || entry.state === "HUMAN_FALLBACK" ? "bg-amber-500" : "bg-emerald-600"}`} />
          <div className="flex items-start justify-between gap-2"><h3 className="text-xs font-semibold text-slate-800">{entry.label}</h3><span className="whitespace-nowrap text-[12px] text-slate-400">{entry.pending ? "处理中" : clockLabel(entry.timestamp)}</span></div>
          <EventStageEvidence event={event} entry={entry} mode={mode} onCompleteManual={onCompleteManual} onViewArchive={onViewArchive} />
        </div>)}
      </div>
    </>}
  </aside>;
}
