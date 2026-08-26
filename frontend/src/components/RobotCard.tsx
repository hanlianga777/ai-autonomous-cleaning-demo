import { BatteryCharging, BatteryFull, ChevronRight, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { Robot } from "@/types/dashboard";

export function RobotCard({ robot }: { robot: Robot }) {
  const isCharging = robot.status === "charging";
  const StatusIcon = isCharging ? BatteryCharging : BatteryFull;

  return (
    <Card className="group transition-colors hover:border-slate-300">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center border border-slate-200 bg-slate-50 text-xs font-bold text-slate-700">
              {robot.short_name.slice(-1)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold text-slate-900">{robot.short_name}</p>
                <span className="font-mono text-[10px] text-slate-400">{robot.code}</span>
              </div>
              <p className="mt-0.5 text-xs text-slate-500">{robot.name}</p>
            </div>
          </div>
          <Badge variant={isCharging ? "warning" : "success"}>{isCharging ? "充电中" : "待命"}</Badge>
        </div>

        <div className="mt-4 grid grid-cols-[1fr_auto] gap-x-3 gap-y-3 border-y border-slate-100 py-3 text-xs">
          <div className="flex min-w-0 items-center gap-1.5 text-slate-500"><MapPin size={13} /><span className="truncate">{robot.location}</span></div>
          <div className="flex items-center gap-1.5 font-medium text-slate-700"><StatusIcon size={14} />{robot.battery}%</div>
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="flex gap-1.5">
            {robot.capabilities.slice(0, 2).map((capability) => <span key={capability} className="text-[11px] text-slate-500">{capability}</span>)}
          </div>
          <button className="flex items-center gap-0.5 text-xs font-medium text-slate-600 transition-colors hover:text-slate-950">详情 <ChevronRight size={14} /></button>
        </div>
      </CardContent>
    </Card>
  );
}

