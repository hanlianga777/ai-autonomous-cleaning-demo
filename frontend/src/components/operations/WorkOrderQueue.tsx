import { Camera, Play, Upload } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { OperationsSnapshot } from "@/types/operations";

export function WorkOrderQueue({ snapshot, onRun, onUpload }: { snapshot: OperationsSnapshot; onRun: (eventId: string) => void; onUpload: () => void }) {
  const active = snapshot.active_work_order;
  const scenario02 = snapshot.catalog.find((item) => item.event_id === "event-beverage-spill-002");
  return <aside className="border border-slate-200 bg-white"><div className="flex items-center justify-between border-b border-slate-100 p-4"><div><p className="section-kicker">清洁工单</p><h3 className="mt-1 text-sm font-semibold">事件列表</h3></div><Badge variant="outline">{active ? "执行中" : "暂无事件"}</Badge></div>
    <div className="p-3">{active ? <article className="border-l-2 border-slate-900 bg-slate-50 p-3"><p className="text-[10px] font-bold tracking-[0.1em] text-slate-400">当前工单</p><p className="mt-1 text-sm font-semibold text-slate-800">液体污渍</p><p className="mt-1 text-[11px] text-slate-500">{active.event.location.building} 栋 · {active.event.location.floor} · {active.event.location.zone}</p><p className="mt-2 text-[11px] font-medium text-slate-700">{active.assignment_decision.selected_robot_name ?? "AI 研判中"}</p></article> : <div className="border border-dashed border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-500">固定摄像头发现异常后，会在此生成一张新的清洁工单。</div>}</div>
    <div className="border-t border-slate-100 p-3"><p className="mb-2 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">快速创建演示工单</p>{scenario02 && <button onClick={() => onRun(scenario02.event_id)} className="flex w-full items-center justify-between gap-2 border border-slate-200 px-3 py-3 text-left hover:border-slate-500 hover:bg-slate-50"><span><span className="block text-xs font-semibold text-slate-700">Scenario 02 · 大堂液体污渍</span><span className="mt-1 flex items-center gap-1 text-[10px] text-slate-500"><Camera size={11} />A 栋 1F 主摄像头</span></span><Play size={13} className="text-slate-400" /></button>}<button onClick={onUpload} className="mt-3 flex w-full items-center justify-center gap-2 border border-slate-300 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"><Upload size={13} />上传受控清洁前图</button><p className="mt-2 text-[10px] leading-4 text-slate-400">本轮仅产品化 Scenario 02；其他 Scenario 保留在技术详情中。</p></div>
  </aside>;
}
