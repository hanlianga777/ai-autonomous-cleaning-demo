import { BatteryMedium, MapPin, Navigation, Route } from "lucide-react";
import { stageCopy } from "./data";
import type { ActiveEvent } from "./types";

type Point = { x: number; y: number; floor?: string };

const resting: Record<string, Point> = {
  "Robot A": { x: 12, y: 78 }, "Robot B": { x: 29, y: 57 }, "Robot C": { x: 70, y: 57 }, "Robot D": { x: 83, y: 79 },
};
const target: Record<string, Point> = {
  outdoor: { x: 27, y: 80 }, liquid: { x: 35, y: 56 }, can: { x: 39, y: 28 }, oversized: { x: 39, y: 23 },
};

function robotPosition(robot: string, event: ActiveEvent | null): Point {
  if (!event || event.scenario.robot !== robot) return resting[robot];
  const state = event.scenario.steps[event.stageIndex];
  const scenario = event.scenario.id;
  if (state === "ROBOT_ASSIGNED") return resting[robot];
  if (scenario !== "can" && ["NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"].includes(state)) return target[scenario];
  if (scenario === "can") {
    if (state === "NAVIGATING") return { x: 72, y: 50, floor: "B1 → 电梯" };
    if (state === "ELEVATOR_TRANSFER") return { x: 72, y: 35, floor: "电梯上行" };
    if (state === "SKYBRIDGE_TRANSFER") return { x: 54, y: 24, floor: "空中连廊" };
    if (["CLEANING", "VERIFYING", "CLOSED"].includes(state)) return target.can;
  }
  return resting[robot];
}

function RobotMarker({ robot, event, battery }: { robot: string; event: ActiveEvent | null; battery: number }) {
  const position = robotPosition(robot, event);
  const active = event?.scenario.robot === robot && !["CLOSED", "HUMAN_FALLBACK"].includes(event.scenario.steps[event.stageIndex]);
  const state = active ? stageCopy[event!.scenario.steps[event!.stageIndex]].title : "待命";
  return <div className="absolute z-20 -translate-x-1/2 -translate-y-1/2 transition-all duration-1000" style={{ left: `${position.x}%`, top: `${position.y}%` }}>
    <div className={`w-28 border px-2 py-1.5 shadow-sm ${active ? "border-slate-900 bg-white" : "border-slate-300 bg-slate-50"}`}>
      <div className="flex items-center justify-between gap-1"><span className="text-[10px] font-semibold text-slate-800">{robot}</span><BatteryMedium size={12} className={battery < 40 ? "text-amber-500" : "text-emerald-600"} /></div>
      <p className="mt-0.5 truncate text-[9px] text-slate-500">{active ? state : "图片素材待补充 · 待命"}</p>
    </div>
    {active && <span className="mx-auto block h-2 w-2 animate-pulse rounded-full bg-rose-500" />}
  </div>;
}

export function SpatialDispatchView({ event }: { event: ActiveEvent | null }) {
  const state = event ? event.scenario.steps[event.stageIndex] : "IDLE";
  const currentTarget = event ? target[event.scenario.id] : null;
  const activeRobot = event?.scenario.robot;
  const showRoute = event && activeRobot && ["ROBOT_ASSIGNED", "NAVIGATING", "ELEVATOR_TRANSFER", "SKYBRIDGE_TRANSFER", "CLEANING", "VERIFYING"].includes(state);
  return <section className="relative min-h-0 overflow-hidden border border-slate-200 bg-[#f8fafb]" aria-label="园区空间调度视图">
    <div className="absolute inset-x-0 top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2.5"><div><p className="text-sm font-semibold text-slate-900">园区空间调度</p><p className="mt-0.5 text-[11px] text-slate-500">2.5D 园区概览 · 基于二维 SLAM 空间关系</p></div><div className="flex items-center gap-1.5 text-[11px] text-slate-500"><Route size={14} />固定视角</div></div>
    <div className="absolute inset-x-0 bottom-0 top-[55px] overflow-hidden">
      <div className="absolute bottom-[4%] left-[3%] right-[3%] h-[18%] border border-dashed border-slate-300 bg-[#eef1f2]"><span className="absolute left-3 top-2 text-[10px] font-semibold tracking-wider text-slate-500">园区东侧道路 · 室外区域</span></div>
      <Building className="left-[13%] top-[13%] w-[33%]" title="A 栋" floors={["2F 公共区域", "1F 大堂", "B1 设备区"]} />
      <Building className="left-[61%] top-[13%] w-[25%]" title="B 栋" floors={["2F 连廊入口", "1F 大厅"]} />
      <div className="absolute left-[46%] top-[20%] h-[8%] w-[15%] border-y border-slate-400 bg-slate-200"><span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 whitespace-nowrap text-[9px] font-semibold text-slate-600">2F 空中连廊</span></div>
      <div className="absolute left-[71%] top-[41%] h-[24%] border-l border-dashed border-slate-400"><span className="absolute -left-5 top-1/2 -rotate-90 whitespace-nowrap text-[9px] text-slate-500">电梯核</span></div>
      {showRoute && <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none"><path d={routePath(event!.scenario.id)} fill="none" stroke="#475569" strokeWidth="0.45" strokeDasharray="1.4 1.2" /></svg>}
      {currentTarget && <div className="absolute z-10 -translate-x-1/2 -translate-y-1/2" style={{ left: `${currentTarget.x}%`, top: `${currentTarget.y}%` }}><MapPin size={22} className="animate-pulse fill-rose-100 text-rose-600" /><span className="absolute left-6 top-1 whitespace-nowrap text-[10px] font-semibold text-rose-700">清洁目标</span></div>}
      <RobotMarker robot="Robot A" event={event} battery={82} /><RobotMarker robot="Robot B" event={event} battery={71} /><RobotMarker robot="Robot C" event={event} battery={89} /><RobotMarker robot="Robot D" event={event} battery={64} />
    </div>
    <div className="absolute bottom-3 left-4 z-30 flex items-center gap-2 border border-slate-200 bg-white px-2.5 py-1.5 text-[10px] text-slate-600"><Navigation size={12} className="text-slate-500" />{activeRobot ? `${activeRobot} · ${stageCopy[state].title}` : "4 台设备在线 · Robot D 不参与清洁候选"}</div>
  </section>;
}

function Building({ className, title, floors }: { className: string; title: string; floors: string[] }) {
  return <div className={`absolute ${className}`}>
    <div className="absolute -left-2 -right-2 -top-2 h-3 -skew-x-[35deg] border border-slate-400 bg-slate-200" />
    <div className="relative border border-slate-400 bg-white shadow-sm"><div className="border-b border-slate-300 bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-700">{title}</div>{floors.map((floor) => <div key={floor} className="border-b border-slate-200 px-2 py-2 last:border-0"><span className="text-[9px] font-medium text-slate-500">{floor}</span></div>)}</div>
  </div>;
}

function routePath(scenario: string) {
  if (scenario === "can") return "M70,57 L72,50 L72,35 L54,24 L39,28";
  if (scenario === "outdoor") return "M12,78 L27,80";
  return "M29,57 L35,56";
}
