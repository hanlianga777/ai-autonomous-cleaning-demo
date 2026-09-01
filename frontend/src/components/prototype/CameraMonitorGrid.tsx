import { MoreHorizontal, Play, Settings2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { CameraViewport } from "./CameraViewport";
import { scenarios } from "./data";
import { monitorViews } from "./eventViewModel";
import { canStartDemo } from "./runtimeSession";
import type { ActiveEvent } from "./types";

/** Customer monitor wall: a primary event view plus two normal operational views. */
export function CameraMonitorGrid({ event, onTrigger }: { event: ActiveEvent | null; onTrigger: (id: typeof scenarios[number]["id"]) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [now, setNow] = useState(() => new Date());
  const menuRef = useRef<HTMLDivElement>(null);
  const busy = !canStartDemo(event);
  useEffect(() => {
    const close = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  const liveTime = new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(now);
  return <section className="flex min-h-0 flex-col border border-slate-200 bg-white" aria-label="固定摄像头监控">
    <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-3 py-1.5">
      <div><p className="text-sm font-semibold text-slate-900">固定摄像头监控</p></div>
      <div ref={menuRef} className="relative">
        <button aria-label="摄像头设置" onClick={() => setMenuOpen((open) => !open)} className="p-2 text-slate-500 hover:bg-slate-100"><MoreHorizontal size={18} /></button>
        {menuOpen && <div className="absolute right-0 top-10 z-[70] w-72 border border-slate-200 bg-white p-2 shadow-lg">
          <div className="flex items-center gap-2 px-2 py-2 text-xs font-medium text-slate-700"><Settings2 size={14} />AI 清洁事件</div>
          {busy && <p className="px-2 pb-2 text-[12px] text-amber-700">请先完成当前事件，避免覆盖运行中的任务。</p>}
          {scenarios.map((scenario, index) => <button key={scenario.id} disabled={busy} data-testid={`trigger-${scenario.id}`} onClick={() => { setMenuOpen(false); onTrigger(scenario.id); }} className="flex w-full items-center gap-2 border-t border-slate-100 px-2 py-2 text-left text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"><span className="flex h-5 w-5 shrink-0 items-center justify-center border border-slate-300 font-mono text-[12px]">{index + 1}</span><Play size={12} className="shrink-0" />{scenario.triggerLabel}</button>)}
        </div>}
      </div>
    </div>
    <div className="grid min-h-0 flex-1 grid-cols-3 gap-1 bg-slate-200 p-1">
      {monitorViews(event).map(({ camera, available, eventView, after }) => <div key={camera.id} data-camera-id={camera.id} data-evidence-role={after ? "after" : "before"} className="relative min-h-0 overflow-hidden bg-slate-950">
        {available ? <CameraViewport camera={camera} showDetections={false} fill presentationLabel={camera.location} /> : <p className="flex h-full items-center justify-center text-xs text-slate-300">本阶段证据暂不可用</p>}
        <div className="pointer-events-none absolute left-1 top-1 bg-slate-950/75 px-1.5 py-0.5 text-[12px] text-white">{camera.location}</div>
        <time dateTime={now.toISOString()} className="pointer-events-none absolute bottom-2 right-2 bg-slate-950/65 px-1.5 py-0.5 font-mono text-[12px] tabular-nums text-white">{liveTime}</time>
        <div className="pointer-events-none absolute bottom-2 left-2 flex h-7 w-7 items-center justify-center rounded-full bg-white/25 text-white"><Play size={13} fill="currentColor" /></div>
      </div>)}
    </div>
  </section>;
}
