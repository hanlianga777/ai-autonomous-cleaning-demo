import { BatteryMedium, Navigation, Route } from "lucide-react";
import { stageCopy } from "./data";
import type { ActiveEvent } from "./types";

type Point = { x: number; y: number; location: string };

const resting: Record<string, Point> = {
  "Robot A": { x: 0.16, y: 0.8, location: "东侧道路" },
  "Robot B": { x: 0.33, y: 0.55, location: "A栋1F" },
  "Robot C": { x: 0.73, y: 0.58, location: "B栋1F" },
  "Robot D": { x: 0.86, y: 0.77, location: "配送区" },
};
const target: Record<string, Point> = {
  outdoor: { x: 0.29, y: 0.8, location: "东侧道路" },
  liquid: { x: 0.37, y: 0.55, location: "A栋1F大堂" },
  can: { x: 0.35, y: 0.28, location: "A栋2F连廊" },
  oversized: { x: 0.37, y: 0.25, location: "A栋2F" },
};

function robotPosition(robot: string, event: ActiveEvent | null): Point {
  if (!event || event.scenario.robot !== robot) return resting[robot];
  const state = event.scenario.steps[event.stageIndex];
  if (state === "ROBOT_ASSIGNED") return resting[robot];
  if (event.scenario.id !== "can" && ["NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"].includes(state)) return target[event.scenario.id];
  if (event.scenario.id === "can") {
    if (state === "NAVIGATING") return { x: 0.76, y: 0.53, location: "B栋1F电梯" };
    if (state === "ELEVATOR_TRANSFER") return { x: 0.76, y: 0.36, location: "B栋电梯上行" };
    if (state === "SKYBRIDGE_TRANSFER") return { x: 0.56, y: 0.26, location: "2F空中连廊" };
    if (["CLEANING", "VERIFYING", "CLOSED"].includes(state)) return target.can;
  }
  return resting[robot];
}

function RobotMarker({ robot, event, battery, name }: { robot: string; event: ActiveEvent | null; battery: number; name: string }) {
  const position = robotPosition(robot, event);
  const active = event?.scenario.robot === robot && !["CLOSED", "HUMAN_FALLBACK"].includes(event.scenario.steps[event.stageIndex]);
  const state = active ? stageCopy[event!.scenario.steps[event!.stageIndex]].title : "空闲";
  return <div className="absolute z-20 -translate-x-1/2 -translate-y-1/2 transition-[left,top] duration-1000 ease-in-out" style={{ left: `${position.x * 100}%`, top: `${position.y * 100}%` }}>
    <div className={`w-[72px] ${active ? "scale-110" : "opacity-75"} transition-transform`}><img className="mx-auto h-8 w-12 object-contain" src={`/visual-assets/robots/${robot.toLowerCase().replace(" ", "-")}.png`} alt={`${name} 机器人`} /><div className="flex items-center justify-center gap-1 border border-slate-300 bg-white/90 px-1 py-0.5"><span className="truncate text-[8px] font-semibold text-slate-800">{name}</span><BatteryMedium size={10} className={battery < 40 ? "text-amber-500" : "text-emerald-600"} /></div><p className="mt-0.5 truncate text-center text-[8px] text-slate-600">{active ? state : position.location}</p></div>
    {active && <span className="mx-auto block h-1.5 w-1.5 animate-pulse rounded-full bg-rose-500" />}
  </div>;
}

function RouteLayer({ showRoute, scenario, state }: { showRoute: boolean; scenario?: string; state: string }) {
  const points = scenario === "can"
    ? [resting["Robot C"], { x: 0.76, y: 0.53, location: "B栋1F电梯" }, { x: 0.76, y: 0.36, location: "B栋2F电梯" }, { x: 0.56, y: 0.26, location: "2F空中连廊" }, target.can]
    : scenario === "outdoor"
      ? [resting["Robot A"], target.outdoor]
      : scenario === "liquid"
        ? [resting["Robot B"], target.liquid]
        : [resting["Robot B"], target.oversized];
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x * 100},${point.y * 100}`).join(" ");
  const progress = scenario === "can"
    ? state === "NAVIGATING" ? 24 : state === "ELEVATOR_TRANSFER" ? 46 : state === "SKYBRIDGE_TRANSFER" ? 76 : 100
    : state === "ROBOT_ASSIGNED" ? 0 : state === "NAVIGATING" ? 58 : 100;
  if (!showRoute) return null;
  return <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="机器人规划路线">
    <path d={path} fill="none" stroke="#94a3b8" strokeWidth="0.75" strokeDasharray="2.4 1.6" vectorEffect="non-scaling-stroke" />
    <path d={path} fill="none" stroke="#334155" strokeWidth="1.25" pathLength="100" strokeDasharray={`${progress} 100`} vectorEffect="non-scaling-stroke" />
  </svg>;
}

export function SpatialDispatchView({ event }: { event: ActiveEvent | null }) {
  const state = event ? event.scenario.steps[event.stageIndex] : "IDLE";
  const currentTarget = event ? target[event.scenario.id] : null;
  const activeRobot = event?.scenario.robot;
  const showRoute = Boolean(event && activeRobot && ["ROBOT_ASSIGNED", "NAVIGATING", "ELEVATOR_TRANSFER", "SKYBRIDGE_TRANSFER", "CLEANING", "VERIFYING"].includes(state));
  return <section className="relative min-h-[180px] overflow-hidden border border-slate-200 bg-[#f6f8f9]" aria-label="园区空间调度视图">
    <div className="absolute inset-x-0 top-0 z-30 flex h-10 items-center justify-between border-b border-slate-200 bg-white/92 px-3"><div className="flex items-center gap-2"><p className="text-sm font-semibold text-slate-900">园区空间调度</p><span className="text-[10px] text-slate-500">二维 SLAM 空间关系</span></div><div className="flex items-center gap-1.5 text-[10px] text-slate-500"><Route size={13} />固定视角</div></div>
    <div className="absolute inset-x-0 bottom-0 top-10 overflow-hidden"><img src="/visual-assets/campus/campus-white-model.png" alt="A栋与B栋园区白模" className="absolute inset-0 h-full w-full object-contain" /><RouteLayer showRoute={showRoute} scenario={event?.scenario.id} state={state} />
      {currentTarget && <div className="absolute z-10 -translate-x-1/2 -translate-y-1/2" style={{ left: `${currentTarget.x * 100}%`, top: `${currentTarget.y * 100}%` }}><span className="block h-4 w-4 animate-pulse rounded-full border-2 border-rose-500 bg-rose-100/80" /><span className="absolute left-5 top-0 whitespace-nowrap text-[9px] font-semibold text-rose-700">清洁目标</span></div>}
      <RobotMarker robot="Robot A" name="室外清扫 A" event={event} battery={82} /><RobotMarker robot="Robot B" name="重载洗地 B" event={event} battery={71} /><RobotMarker robot="Robot C" name="室内清洁 C" event={event} battery={89} /><RobotMarker robot="Robot D" name="配送机器人 D" event={event} battery={64} />
    </div>
    <div className="absolute bottom-2 left-3 z-30 flex items-center gap-1.5 border border-slate-200 bg-white/90 px-2 py-1 text-[9px] text-slate-600"><Navigation size={11} className="text-slate-500" />{activeRobot ? `${activeRobot} · ${stageCopy[state].title}` : "4 台设备在线 · 配送机器人不参与清洁候选"}</div>
  </section>;
}
