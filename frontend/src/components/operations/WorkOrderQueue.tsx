import { ClipboardList, Play, Upload } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { OperationsSnapshot } from "@/types/operations";

export function WorkOrderQueue({ snapshot, onRun, onUpload }: { snapshot: OperationsSnapshot; onRun: (eventId: string) => void; onUpload: () => void }) {
  const active = snapshot.active_work_order;
  return <aside className="border border-slate-200 bg-white"><div className="flex items-center justify-between border-b border-slate-100 p-4"><div><p className="section-kicker">Work orders</p><h3 className="mt-1 text-sm font-semibold">任务工单</h3></div><Badge variant="outline">{active ? "1 活跃" : "等待事件"}</Badge></div>
    <div className="p-3">{active ? <article className="border border-slate-900 bg-slate-900 p-3 text-white"><p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-300">当前工单 · {active.display_state}</p><p className="mt-1 text-sm font-semibold">{active.asset_manifest.title}</p><p className="mt-1 text-[11px] text-slate-300">{active.event.location.building} · {active.event.location.floor} · {active.event.location.zone}</p><div className="mt-3 h-1.5 bg-slate-700"><div className="h-full bg-emerald-400" style={{ width: `${Math.round(active.progress * 100)}%` }} /></div></article> : <div className="border border-dashed border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-500">选择下方场景，或上传受控清洁前图创建一张演示工单。</div>}</div>
    <div className="border-t border-slate-100 p-3"><p className="mb-2 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">可演示场景</p><div className="space-y-2">{snapshot.catalog.map((item) => <button key={item.event_id} onClick={() => onRun(item.event_id)} className="flex w-full items-center justify-between gap-2 border border-slate-200 px-3 py-2.5 text-left hover:border-slate-500 hover:bg-slate-50"><span><span className="block text-xs font-semibold text-slate-700">{item.title}</span><span className="mt-0.5 block text-[10px] text-slate-500">{item.expected_robot === "HUMAN_FALLBACK" ? "人工兜底" : item.expected_robot.replace("ROBOT_", "Robot ")}</span></span><Play size={13} className="text-slate-400" /></button>)}</div><button onClick={onUpload} className="mt-3 flex w-full items-center justify-center gap-2 border border-slate-300 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"><Upload size={13} />上传清洁前图</button></div>
  </aside>;
}
