import { CircleDot } from "lucide-react";
import { useEffect, useState } from "react";
import { CameraMonitorGrid } from "./CameraMonitorGrid";
import { EventDetailPanel } from "./EventDetailPanel";
import { scenarios, stageCopy } from "./data";
import { SpatialDispatchView } from "./SpatialDispatchView";
import type { ActiveEvent } from "./types";

export function PrototypeWorkbench() {
  const [event, setEvent] = useState<ActiveEvent | null>(null);
  const [running, setRunning] = useState(false);
  useEffect(() => {
    if (!event || !running) return;
    const state = event.scenario.steps[event.stageIndex];
    if (["CLOSED", "HUMAN_FALLBACK"].includes(state)) { setRunning(false); return; }
    const timer = window.setTimeout(() => setEvent((current) => current && ({ ...current, stageIndex: Math.min(current.stageIndex + 1, current.scenario.steps.length - 1) })), 1150);
    return () => window.clearTimeout(timer);
  }, [event, running]);
  const trigger = (id: typeof scenarios[number]["id"]) => { const scenario = scenarios.find((item) => item.id === id); if (scenario) { setEvent({ scenario, stageIndex: 0, startedAt: new Date().toISOString() }); setRunning(true); } };
  const state = event ? event.scenario.steps[event.stageIndex] : "IDLE";
  return <div className="h-screen min-h-[680px] overflow-hidden bg-[#f6f7f8] text-slate-900">
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-5 lg:px-7"><div className="flex items-center gap-3"><div className="flex h-8 w-8 items-center justify-center bg-slate-900 text-[10px] font-bold text-white">CO</div><div><p className="text-sm font-semibold">自主清洁工作台</p><p className="text-[10px] uppercase tracking-[0.12em] text-slate-400">Campus operations</p></div></div><div className="flex items-center gap-2 text-xs text-slate-600"><span className="hidden border border-slate-200 px-2 py-1 sm:inline">原型验证环境</span><span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500" />园区监测正常</span></div></header>
    <main className="h-[calc(100vh-64px)] min-h-[616px] p-3 lg:p-4"><div className="mb-3 flex h-10 items-center justify-between"><div><p className="text-[11px] font-medium uppercase tracking-[0.13em] text-slate-400">Autonomous cleaning operations</p><p className="text-xs text-slate-600">从摄像头发现问题，到空间调度、清洁和验收闭环。</p></div><div className={`hidden items-center gap-1.5 text-xs font-medium md:flex ${event ? "text-slate-800" : "text-slate-500"}`}><CircleDot size={14} className={event && running ? "animate-pulse text-rose-500" : "text-emerald-500"} />{stageCopy[state].title}</div></div>
      <div className="grid h-[calc(100%-52px)] grid-cols-1 gap-3 xl:grid-cols-[minmax(0,72fr)_minmax(320px,28fr)]"><div className="grid min-h-0 grid-rows-[42%_58%] gap-3"><CameraMonitorGrid event={event} onTrigger={trigger} /><SpatialDispatchView event={event} /></div><EventDetailPanel event={event} /></div>
    </main>
  </div>;
}
