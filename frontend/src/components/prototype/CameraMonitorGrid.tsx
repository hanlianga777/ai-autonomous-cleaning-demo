import { Eye, MoreHorizontal, Play, Settings2 } from "lucide-react";
import { useState } from "react";
import { cameras, defaultCameraIds, scenarios } from "./data";
import type { ActiveEvent, Camera } from "./types";

function CameraTile({ camera, active, supplemental, selected, onSelect }: { camera: Camera; active: boolean; supplemental: boolean; selected: boolean; onSelect: () => void }) {
  return <button type="button" onClick={onSelect} className={`group relative min-w-0 overflow-hidden border bg-slate-950 text-left transition ${selected ? "border-slate-900 ring-1 ring-slate-900" : active ? "border-rose-300 ring-1 ring-rose-200" : supplemental ? "border-amber-300" : "border-slate-200"}`}>
    <div className="relative aspect-[4/3] overflow-hidden bg-slate-100">
      <img src={camera.image} alt={`${camera.id} ${camera.location}`} className="h-full w-full object-contain" />
      {(active || supplemental) && camera.overlay?.map((item, index) => {
        const [x1, y1, x2, y2] = item.bbox;
        return <div key={`${item.label}-${index}`} className={`absolute border-2 ${supplemental ? "border-amber-400" : "border-rose-500"}`} style={{ left: `${x1 * 100}%`, top: `${y1 * 100}%`, width: `${(x2 - x1) * 100}%`, height: `${(y2 - y1) * 100}%` }}>
          <span className={`absolute -top-5 left-0 whitespace-nowrap px-1.5 py-0.5 text-[10px] font-semibold text-white ${supplemental ? "bg-amber-500" : "bg-rose-600"}`}>{item.label} {Math.round(item.confidence * 100)}%</span>
        </div>;
      })}
      {active && <span className="absolute inset-0 animate-pulse border-2 border-rose-400/80" />}
      {supplemental && <span className="absolute right-2 top-2 bg-amber-500 px-1.5 py-1 text-[10px] font-medium text-white">Agent 临时调取</span>}
    </div>
    <div className="absolute inset-x-0 bottom-0 flex items-end justify-between bg-slate-950/75 px-2.5 pb-2 pt-2 text-white">
      <div><p className="text-[11px] font-semibold tracking-wide">{camera.id}</p><p className="max-w-[150px] truncate text-[10px] text-slate-200">{camera.location}</p></div>
      <div className="flex items-center gap-1 text-[10px] text-emerald-200"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />在线</div>
    </div>
    {active && <div className="absolute left-2 top-2 flex items-center gap-1 bg-rose-600 px-1.5 py-1 text-[10px] font-semibold text-white"><span className="h-1.5 w-1.5 rounded-full bg-white" />发现异常</div>}
  </button>;
}

export function CameraMonitorGrid({ event, onTrigger }: { event: ActiveEvent | null; onTrigger: (id: typeof scenarios[number]["id"]) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const stage = event ? event.scenario.steps[event.stageIndex] : "IDLE";
  const isMultiview = event?.scenario.id === "liquid" && stage === "MULTI_VIEW";
  const cameraIds = isMultiview ? ["CAM-A1-01", "CAM-A1-02", "CAM-A1-04", "CAM-A2-11"] : defaultCameraIds;
  return <section className="flex min-h-0 flex-col border border-slate-200 bg-white" aria-label="固定摄像头监控">
    <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5">
      <div><p className="text-sm font-semibold text-slate-900">固定摄像头监控</p><p className="mt-0.5 text-[11px] text-slate-500">4 路园区重点区域 · 点击画面仅切换查看</p></div>
      <div className="relative">
        <button aria-label="摄像头设置" onClick={() => setMenuOpen((open) => !open)} className="rounded-sm p-2 text-slate-500 hover:bg-slate-100"><MoreHorizontal size={18} /></button>
        {menuOpen && <div className="absolute right-0 top-10 z-30 w-72 border border-slate-200 bg-white p-2 shadow-lg">
          <div className="flex items-center gap-2 px-2 py-2 text-xs font-medium text-slate-700"><Settings2 size={14} />摄像头视图设置</div>
          <div className="border-t border-slate-100 px-2 pb-1 pt-3"><p className="mb-2 text-[11px] font-semibold text-slate-500">演示控制</p>
            {scenarios.map((scenario) => <button key={scenario.id} data-testid={`trigger-${scenario.id}`} onClick={() => { setMenuOpen(false); onTrigger(scenario.id); }} className="flex w-full items-center gap-2 px-2 py-2 text-left text-xs text-slate-700 hover:bg-slate-50"><Play size={13} className="text-slate-400" />{scenario.triggerLabel}</button>)}
          </div>
        </div>}
      </div>
    </div>
    <div className="grid min-h-0 flex-1 grid-cols-2 gap-px bg-slate-200">
      {cameraIds.map((id) => <CameraTile key={id} camera={cameras[id]} active={event?.scenario.cameraId === id && stage !== "CLOSED" && stage !== "IDLE"} supplemental={isMultiview && id !== "CAM-A1-01"} selected={selectedCamera === id} onSelect={() => setSelectedCamera(id)} />)}
    </div>
    <div className="flex items-center justify-between border-t border-slate-100 px-3 py-1.5 text-[10px] text-slate-500"><span className="flex items-center gap-1"><Eye size={12} />{selectedCamera ? `正在查看 ${selectedCamera}` : "实时画面"}</span><span>{new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date())}</span></div>
  </section>;
}
