import { Building2, CircleDotDashed, Trees } from "lucide-react";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { Park, Robot } from "@/types/dashboard";

const markerClass = {
  "robot-a": "left-[16%] top-[73%]",
  "robot-b": "left-[40%] top-[54%]",
  "robot-c": "right-[16%] top-[54%]",
};

export function CampusOverview({ park, robots }: { park: Park; robots: Robot[] }) {
  return (
    <Card className="min-h-[360px] overflow-hidden">
      <CardHeader className="flex flex-row items-start justify-between p-5 pb-4">
        <div>
          <p className="section-kicker">Campus overview</p>
          <h2 className="mt-1 text-base font-semibold text-slate-900">园区基础信息</h2>
        </div>
        <span className="font-mono text-[11px] text-slate-400">{park.park_id}</span>
      </CardHeader>
      <CardContent className="p-5 pt-0">
        <div className="relative h-[236px] overflow-hidden border border-slate-200 bg-[#fafbfb] campus-grid">
          <div className="absolute inset-x-[38%] top-[24%] h-[18%] border-y border-dashed border-slate-300 bg-slate-100/70" />
          <div className="absolute left-[12%] top-[18%] h-[48%] w-[26%] border border-slate-300 bg-white p-3 shadow-sm">
            <Building2 size={17} className="text-slate-400" /><p className="mt-3 text-sm font-semibold text-slate-800">A 栋</p><p className="mt-1 text-[11px] text-slate-500">B1 · 1F · 2F</p>
          </div>
          <div className="absolute right-[12%] top-[18%] h-[48%] w-[26%] border border-slate-300 bg-white p-3 shadow-sm">
            <Building2 size={17} className="text-slate-400" /><p className="mt-3 text-sm font-semibold text-slate-800">B 栋</p><p className="mt-1 text-[11px] text-slate-500">1F · 2F</p>
          </div>
          <div className="absolute bottom-[10%] left-[7%] flex items-center gap-1.5 text-[11px] text-slate-500"><Trees size={14} />室外道路 / 广场</div>
          <div className="absolute left-1/2 top-[28%] -translate-x-1/2 text-[10px] font-medium tracking-wide text-slate-500">2F 连廊</div>
          {robots.map((robot) => <div key={robot.id} aria-label={robot.short_name} className={`absolute z-10 flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-slate-800 text-[10px] font-bold text-white shadow-sm ${markerClass[robot.id as keyof typeof markerClass]}`}><CircleDotDashed size={13} /></div>)}
        </div>
        <div className="mt-4 grid grid-cols-3 divide-x divide-slate-100 border-y border-slate-100 py-3">
          <div><p className="metric-value">{park.summary.buildings}</p><p className="metric-label">楼栋</p></div>
          <div className="pl-4"><p className="metric-value">{park.summary.managed_floors}</p><p className="metric-label">管理楼层</p></div>
          <div className="pl-4"><p className="metric-value">{park.summary.outdoor_zones}</p><p className="metric-label">室外区域</p></div>
        </div>
      </CardContent>
    </Card>
  );
}

