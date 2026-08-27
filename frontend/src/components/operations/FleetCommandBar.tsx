import { BatteryCharging, Bot, MapPin, Radio } from "lucide-react";

import type { FleetTelemetry } from "@/types/operations";

const statusLabel: Record<string, string> = { idle: "待命", navigating: "导航中", arrived: "已到达", cleaning: "清洁中", verifying: "验收中" };

export function FleetCommandBar({ fleet }: { fleet: FleetTelemetry[] }) {
  return <section className="grid gap-3 md:grid-cols-3" aria-label="机器人实时状态">
    {fleet.map((robot) => <article key={robot.id} className="border border-slate-200 bg-white p-4 shadow-[0_1px_0_rgba(15,23,42,0.02)]">
      <div className="flex items-start justify-between gap-3"><div className="flex items-center gap-2"><span className={`flex h-8 w-8 items-center justify-center rounded-sm ${robot.status === "cleaning" ? "bg-emerald-700" : robot.status === "navigating" ? "bg-blue-700" : "bg-slate-800"} text-white`}><Bot size={16} /></span><div><p className="text-sm font-semibold text-slate-900">{robot.short_name}</p><p className="text-[11px] text-slate-500">{robot.role}</p></div></div><span className={`inline-flex items-center gap-1 text-[11px] font-semibold ${robot.status === "idle" ? "text-slate-500" : "text-emerald-700"}`}><Radio size={11} />{statusLabel[robot.status] ?? robot.status}</span></div>
      <div className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-3"><div><p className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">当前状态</p><p className="mt-1 truncate text-xs font-medium text-slate-700">{robot.activity}</p></div><div><p className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">电量</p><p className="mt-1 flex items-center gap-1 text-xs font-semibold text-slate-700"><BatteryCharging size={13} className={robot.battery < 30 ? "text-rose-600" : "text-emerald-600"} />{robot.battery}%</p></div></div>
      <p className="mt-3 flex items-center gap-1 text-[11px] text-slate-500"><MapPin size={12} />{robot.position.map_id} · ({robot.position.x.toFixed(1)}, {robot.position.y.toFixed(1)})</p>
    </article>)}
  </section>;
}
