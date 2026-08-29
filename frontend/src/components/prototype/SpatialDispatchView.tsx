import { useEffect, useState } from "react";
import { stageCopy } from "./data";
import { campusTopology, eventAnchorByDemo, standbyAnchorByRobot, type TopologyAnchor } from "./topology";
import type { ActiveEvent, PrototypeState } from "./types";

type Assignment = { selected_robot_name?: string | null };
type NavigationPlan = { anchor_sequence?: string[] };
const fleet = [["Robot A", "室外清扫 A", 82], ["Robot B", "重载洗地 B", 71], ["Robot C", "室内清洁 C", 89], ["Robot D", "配送机器人 D", 64]] as const;

function activeRobot(event: ActiveEvent | null) {
  return (event?.liveResult?.assignment_decision as Assignment | undefined)?.selected_robot_name ?? null;
}
function displayState(event: ActiveEvent | null): PrototypeState { return event?.inFlightState ?? (event ? event.scenario.steps[event.stageIndex] : "IDLE"); }
function routeFor(event: ActiveEvent | null): TopologyAnchor[] {
  const plan = event?.liveResult?.navigation_plan as NavigationPlan | undefined;
  return (plan?.anchor_sequence ?? []).map((id) => campusTopology[id]).filter((anchor): anchor is TopologyAnchor => Boolean(anchor));
}
function positionFor(robot: string, event: ActiveEvent | null, tick: number): TopologyAnchor {
  const standby = campusTopology[standbyAnchorByRobot[robot]];
  if (activeRobot(event) !== robot) return standby;
  const route = routeFor(event); const state = displayState(event);
  if (!route.length || state === "ROBOT_ASSIGNED") return standby;
  if (state === "NAVIGATING") return route[Math.min(route.length - 1, Math.floor((tick % (route.length * 2)) / 2))];
  return route[route.length - 1] ?? standby;
}

function RobotMarker({ robot, label, battery, event, tick }: { robot: string; label: string; battery: number; event: ActiveEvent | null; tick: number }) {
  const [hovered, setHovered] = useState(false); const position = positionFor(robot, event, tick);
  const active = activeRobot(event) === robot && !["CLOSED", "HUMAN_FALLBACK", "HUMAN_REVIEW"].includes(displayState(event));
  const status = active ? stageCopy[displayState(event)].title : "空闲";
  return <div onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)} className="absolute z-20 -translate-x-1/2 -translate-y-1/2 transition-[left,top] duration-700 ease-in-out" style={{ left: `${position.normalized_x * 100}%`, top: `${position.normalized_y * 100}%` }}>
    <div className={`w-[clamp(34px,4vw,54px)] ${robot === "Robot A" || robot === "Robot D" ? "opacity-100" : "opacity-80"} ${active ? "scale-110" : ""} transition-transform`}><img className="mx-auto h-9 w-full object-contain" src={`/visual-assets/robots/${robot.toLowerCase().replace(" ", "-")}.png`} alt={`${label} 机器人`} /></div>
    {hovered && <div className="absolute left-1/2 top-full z-30 mt-1 w-40 -translate-x-1/2 border border-slate-300 bg-white p-1.5 text-[9px] text-slate-600 shadow-sm"><b className="block text-slate-800">{label}</b><p>电量 {battery}% · {status}</p><p>{position.label}</p></div>}
    {active && <span className="mx-auto block h-1.5 w-1.5 animate-pulse rounded-full bg-rose-500" />}
  </div>;
}

function RouteLayer({ route, state, tick }: { route: TopologyAnchor[]; state: PrototypeState; tick: number }) {
  if (route.length < 2) return null;
  const path = route.map((point, index) => `${index === 0 ? "M" : "L"}${point.normalized_x * 100},${point.normalized_y * 100}`).join(" ");
  const progress = state === "ROBOT_ASSIGNED" ? 0 : state === "NAVIGATING" ? Math.min(92, 18 + tick * (76 / Math.max(route.length * 4, 1))) : 100;
  return <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="机器人规划路线"><path d={path} fill="none" stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="4 3" vectorEffect="non-scaling-stroke" /><path d={path} fill="none" stroke="#2563eb" strokeWidth="2.2" pathLength="100" strokeDasharray={`${progress} 100`} vectorEffect="non-scaling-stroke" /></svg>;
}

export function SpatialDispatchView({ event }: { event: ActiveEvent | null }) {
  const [tick, setTick] = useState(0); const state = displayState(event);
  useEffect(() => { if (state !== "NAVIGATING") { setTick(0); return; } const timer = window.setInterval(() => setTick((value) => value + 1), 650); return () => window.clearInterval(timer); }, [state, event?.liveResult?.event_id]);
  const selectedRobot = activeRobot(event); const route = routeFor(event); const target = event ? campusTopology[eventAnchorByDemo[event.scenario.id]] : null;
  const showRoute = Boolean(selectedRobot && route.length > 1 && ["ROBOT_ASSIGNED", "NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"].includes(state));
  return <section className="relative grid min-h-[220px] grid-cols-[132px_1fr] overflow-hidden border border-slate-200 bg-[#f6f8f9]" aria-label="园区空间调度视图">
    <aside className="z-30 border-r border-slate-200 bg-white p-2"><p className="mb-2 text-[10px] font-semibold text-slate-500">设备资产</p>{fleet.map(([robot, label, battery]) => <div key={robot} className="mb-1 flex items-center gap-1.5 border-b border-slate-100 py-1"><img src={`/visual-assets/robots/${robot.toLowerCase().replace(" ", "-")}.png`} className="h-6 w-8 object-contain" /><span className="text-[9px] text-slate-700">{label} · {robot === selectedRobot ? stageCopy[state].title : "空闲"}</span><span className="ml-auto text-[8px] text-slate-400">{battery}%</span></div>)}</aside>
    <div className="relative overflow-hidden"><img src="/visual-assets/campus/campus-white-model.png" alt="A栋与B栋园区白模" className="absolute inset-0 h-full w-full object-contain" /><RouteLayer route={showRoute ? route : []} state={state} tick={tick} />
      {target && <div className="absolute z-10 -translate-x-1/2 -translate-y-1/2" style={{ left: `${target.normalized_x * 100}%`, top: `${target.normalized_y * 100}%` }}><span className="block h-4 w-4 animate-pulse rounded-full border-2 border-rose-500 bg-rose-100/80" /></div>}
      {fleet.map(([robot, label, battery]) => <RobotMarker key={robot} robot={robot} label={label} battery={battery} event={event} tick={tick} />)}
    </div>
  </section>;
}
