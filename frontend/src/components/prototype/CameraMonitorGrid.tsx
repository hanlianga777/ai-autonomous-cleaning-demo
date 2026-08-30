import { MoreHorizontal, Play, Settings2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { CameraViewport } from "./CameraViewport";
import { scenarios } from "./data";
import { monitorViews } from "./eventViewModel";
import { canStartDemo } from "./runtimeSession";
import type { ActiveEvent } from "./types";

/** Two primary camera slots, not a multi-view Agent evidence gallery. */
export function CameraMonitorGrid({ event, onTrigger }: { event: ActiveEvent | null; onTrigger: (id: typeof scenarios[number]["id"]) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const busy = !canStartDemo(event);
  useEffect(() => {
    const close = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);
  return <section className="flex min-h-0 flex-col border border-slate-200 bg-white" aria-label="固定摄像头监控">
    <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-3 py-1.5">
      <div><p className="text-sm font-semibold text-slate-900">固定摄像头监控</p><p className="text-[10px] text-slate-500">2 路重点区域 · 受控摄像头证据</p></div>
      <div ref={menuRef} className="relative">
        <button aria-label="摄像头设置" onClick={() => setMenuOpen((open) => !open)} className="p-2 text-slate-500 hover:bg-slate-100"><MoreHorizontal size={18} /></button>
        {menuOpen && <div className="absolute right-0 top-10 z-[70] w-72 border border-slate-200 bg-white p-2 shadow-lg">
          <div className="flex items-center gap-2 px-2 py-2 text-xs font-medium text-slate-700"><Settings2 size={14} />演示控制</div>
          {busy && <p className="px-2 pb-2 text-[11px] text-amber-700">请先完成当前事件，避免覆盖运行中的任务。</p>}
          {scenarios.map((scenario, index) => <button key={scenario.id} disabled={busy} data-testid={`trigger-${scenario.id}`} onClick={() => { setMenuOpen(false); onTrigger(scenario.id); }} className="flex w-full items-center gap-2 border-t border-slate-100 px-2 py-2 text-left text-xs text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"><span className="flex h-5 w-5 items-center justify-center border border-slate-300 font-mono text-[10px]">{index + 1}</span><Play size={12} />{scenario.triggerLabel}</button>)}
        </div>}
      </div>
    </div>
    <div className="grid min-h-0 flex-1 grid-cols-2 gap-1 bg-slate-200 p-1">
      {monitorViews(event).map(({ camera, available, eventView, after, detections }) => <div key={camera.id} data-camera-id={camera.id} data-evidence-role={after ? "after" : "before"} className="relative min-h-0 overflow-hidden bg-slate-950">
        {available ? <CameraViewport camera={camera} showDetections={detections} fill /> : <p className="flex h-full items-center justify-center text-xs text-slate-300">本阶段证据暂不可用</p>}
        <div className="pointer-events-none absolute left-1 top-1 bg-slate-950/75 px-1.5 py-0.5 text-[10px] text-white">{camera.id}</div>
        <div className={`pointer-events-none absolute right-1 top-1 px-1.5 py-0.5 text-[10px] text-white ${eventView && !after ? "bg-amber-700" : "bg-slate-800/85"}`}>{!eventView ? "空闲画面" : after ? "处置后证据" : "处置前证据"}</div>
        <div className="pointer-events-none absolute bottom-1 left-1 bg-slate-950/75 px-1.5 py-0.5 text-[10px] text-slate-100">{camera.location}</div>
      </div>)}
    </div>
  </section>;
}
