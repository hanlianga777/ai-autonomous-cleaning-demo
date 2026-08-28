import { MoreHorizontal, Play, Settings2 } from "lucide-react";
import { useEffect, useState } from "react";
import { CameraViewport } from "./CameraViewport";
import { cameras, defaultCameraIds, scenarios } from "./data";
import type { ActiveEvent, Camera } from "./types";

function CameraTile({ camera, active, supplemental, selected, onSelect }: { camera: Camera; active: boolean; supplemental: boolean; selected: boolean; onSelect: () => void }) {
  return <button type="button" onClick={onSelect} className={`group relative min-w-0 overflow-hidden border bg-slate-950 text-left transition ${selected ? "border-slate-100 ring-1 ring-slate-700" : active ? "border-rose-300 ring-1 ring-rose-200" : supplemental ? "border-amber-300" : "border-slate-200"}`}>
    <div className={`relative overflow-hidden transition-transform duration-500 ${active ? "scale-[1.012]" : ""}`}>
      <CameraViewport camera={camera} showDetections={active || supplemental} />
    </div>
    <span className="absolute left-1/2 top-1/2 flex h-9 w-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/70 bg-slate-950/35 text-white"><Play size={15} fill="currentColor" /></span>
    <div className="absolute left-2 top-2 flex items-center gap-1.5 bg-slate-950/68 px-1.5 py-1 text-[10px] font-semibold text-white"><span>{camera.id}</span><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />在线</div>
    <div className="absolute bottom-2 left-2 bg-slate-950/68 px-1.5 py-1 text-[10px] text-slate-100">{camera.location} · {new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date())}</div>
    {active && <><span className="absolute inset-0 animate-pulse border-2 border-rose-400/80" /><div className="absolute right-2 top-2 bg-rose-600 px-1.5 py-1 text-[10px] font-semibold text-white">发现异常</div></>}
    {supplemental && <span className="absolute right-2 top-2 bg-amber-500 px-1.5 py-1 text-[10px] font-medium text-white">Agent 临时调取</span>}
  </button>;
}

export function CameraMonitorGrid({ event, onTrigger }: { event: ActiveEvent | null; onTrigger: (id: typeof scenarios[number]["id"], mode?: "live" | "replay") => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [, setClockTick] = useState(0);
  useEffect(() => { const timer = window.setInterval(() => setClockTick((value) => value + 1), 1000); return () => window.clearInterval(timer); }, []);
  const stage = event ? event.scenario.steps[event.stageIndex] : "IDLE";
  const cameraIds = defaultCameraIds;
  return <section className="flex min-h-0 flex-col border border-slate-200 bg-white" aria-label="固定摄像头监控">
    <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
      <div><p className="text-sm font-semibold text-slate-900">固定摄像头监控</p><p className="mt-0.5 text-[10px] text-slate-500">2 路园区重点区域</p></div>
      <div className="relative">
        <button aria-label="摄像头设置" onClick={() => setMenuOpen((open) => !open)} className="rounded-sm p-2 text-slate-500 hover:bg-slate-100"><MoreHorizontal size={18} /></button>
        {menuOpen && <div className="absolute right-0 top-10 z-30 w-72 border border-slate-200 bg-white p-2 shadow-lg">
          <div className="flex items-center gap-2 px-2 py-2 text-xs font-medium text-slate-700"><Settings2 size={14} />摄像头视图设置</div>
          <div className="border-t border-slate-100 px-2 pb-1 pt-3"><p className="mb-2 text-[11px] font-semibold text-slate-500">演示控制</p>
            {scenarios.map((scenario) => <div key={scenario.id} className="border-b border-slate-100 py-1 last:border-0"><button data-testid={`trigger-${scenario.id}`} onClick={() => { setMenuOpen(false); onTrigger(scenario.id, "live"); }} className="flex w-full items-center gap-2 px-2 py-1.5 text-left text-xs text-slate-700 hover:bg-slate-50"><Play size={13} className="text-slate-400" />{scenario.triggerLabel}</button><button data-testid={`replay-${scenario.id}`} onClick={() => { setMenuOpen(false); onTrigger(scenario.id, "replay"); }} className="ml-7 px-2 py-1 text-[10px] text-slate-500 hover:bg-slate-50 hover:text-slate-800">手动稳定回放</button></div>)}
          </div>
        </div>}
      </div>
    </div>
    <div className="grid min-h-0 grid-cols-2 gap-1 bg-slate-200 p-1">
      {cameraIds.map((id) => { const camera = cameras[id]; const displayCamera = !event && camera.afterImage ? { ...camera, image: camera.afterImage } : camera; return <CameraTile key={id} camera={displayCamera} active={event?.scenario.cameraId === id && stage !== "CLOSED" && stage !== "IDLE"} supplemental={false} selected={selectedCamera === id} onSelect={() => setSelectedCamera(id)} />; })}
    </div>
  </section>;
}
