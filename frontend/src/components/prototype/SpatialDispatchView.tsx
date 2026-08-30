import { useEffect, useMemo, useState } from "react";
import { stageCopy } from "./data";
import type { ActiveEvent, PrototypeState } from "./types";

type FleetRobot = { id: string; name: string; status: string; battery: number; location: string; map_id: string; coordinates: { x: number; y: number } };
type NavigationPlan = { node_path?: string[]; display_anchors?: string[] };
type EventLocation = { map_id: string; x: number; y: number };
type Point = { x: number; y: number; label: string };

// Projection-only placement of existing Phase 2 topology nodes onto the campus
// illustration. Runtime route order and all robot/target coordinates come from
// the backend; this file never derives a route from a scenario id.
const nodeProjection: Record<string, Point> = {
  OUTDOOR: { x: 25, y: 78, label: "园区道路" }, A_B1: { x: 33, y: 66, label: "A栋 B1" }, A_1F: { x: 35, y: 52, label: "A栋 1F" }, A_2F: { x: 35, y: 28, label: "A栋 2F" },
  B_1F: { x: 74, y: 57, label: "B栋 1F" }, B_2F: { x: 74, y: 34, label: "B栋 2F" }, A_ELEVATOR_1F: { x: 40, y: 49, label: "A栋电梯" }, A_ELEVATOR_2F: { x: 39, y: 31, label: "A栋电梯" },
  B_ELEVATOR_1F: { x: 76, y: 52, label: "B栋电梯" }, B_ELEVATOR_2F: { x: 76, y: 37, label: "B栋电梯" }, SKYBRIDGE_B: { x: 61, y: 29, label: "连廊 B 端" }, SKYBRIDGE_A: { x: 50, y: 29, label: "连廊 A 端" },
};

function projectSpatial(mapId: string, x: number, y: number): Point { const base = nodeProjection[mapId] ?? { x: 50, y: 50, label: mapId }; return { x: base.x + (x - 50) * 0.08, y: base.y + (y - 30) * 0.08, label: base.label }; }
function displayState(event: ActiveEvent | null): PrototypeState { return event?.inFlightState ?? (event ? event.scenario.steps[event.stageIndex] : "IDLE"); }
function routeFor(event: ActiveEvent | null): Point[] { const plan = event?.liveResult?.navigation_plan as NavigationPlan | undefined; return (plan?.node_path ?? plan?.display_anchors ?? []).map((node) => nodeProjection[node]).filter((point): point is Point => Boolean(point)); }
function activeRobotId(event: ActiveEvent | null): string | null { return (event?.liveResult?.assignment_decision as { selected_robot_id?: string } | undefined)?.selected_robot_id ?? null; }

function RouteLayer({ route }: { route: Point[] }) { if (route.length < 2) return null; const path = route.map((point, index) => `${index ? "L" : "M"}${point.x},${point.y}`).join(" "); return <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="后端 Dijkstra 规划路线"><path d={path} fill="none" stroke="#94a3b8" strokeWidth="1.4" strokeDasharray="4 3" vectorEffect="non-scaling-stroke" /><path d={path} fill="none" stroke="#2563eb" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>; }

export function SpatialDispatchView({ event }: { event: ActiveEvent | null }) {
  const [fleet, setFleet] = useState<FleetRobot[]>([]); const state = displayState(event); const selectedRobot = activeRobotId(event); const route = routeFor(event);
  useEffect(() => { void fetch("/api/robots").then((response) => response.ok ? response.json() : Promise.reject()).then(setFleet).catch(() => setFleet([])); }, [event?.liveResult?.updated_at, event?.liveResult?.state]);
  const displayedFleet = useMemo(() => { const snapshot = event?.liveResult?.fleet_snapshot; return Array.isArray(snapshot) ? snapshot as FleetRobot[] : fleet; }, [event?.liveResult?.fleet_snapshot, fleet]);
  // A fixture discovery location is not a spatial result.  The marker appears
  // only after the backend has persisted the Camera→SLAM mapping.
  const target = event?.liveResult?.spatial_location as EventLocation | undefined;
  return <section className="relative grid min-h-[220px] grid-cols-[152px_1fr] overflow-hidden border border-slate-200 bg-[#f6f8f9]" aria-label="园区空间调度视图">
    <aside className="z-30 border-r border-slate-200 bg-white p-2"><p className="mb-2 text-[10px] font-semibold text-slate-500">共享 Fleet 状态</p>{displayedFleet.map((robot) => <div key={robot.id} className="mb-1 flex items-center gap-1.5 border-b border-slate-100 py-1"><img src={`/visual-assets/robots/${robot.id}.png`} className="h-6 w-8 object-contain" /><span className="min-w-0 flex-1 truncate text-[9px] text-slate-700">{robot.name} · {robot.id === selectedRobot ? stageCopy[state].title : robot.status === "idle" ? "空闲" : robot.status}</span><span className="text-[8px] text-slate-400">{robot.battery}%</span></div>)}</aside>
    <div className="relative overflow-hidden"><img src="/visual-assets/campus/campus-white-model.png" alt="A栋与B栋园区白模" className="absolute inset-0 h-full w-full object-contain" /><RouteLayer route={route} />
      {target && <div className="absolute z-20 -translate-x-1/2 -translate-y-1/2" style={{ left: `${projectSpatial(target.map_id, target.x, target.y).x}%`, top: `${projectSpatial(target.map_id, target.x, target.y).y}%` }}><span className="block h-4 w-4 rounded-full border-2 border-rose-500 bg-rose-100/90" /></div>}
      {displayedFleet.map((robot) => { const position = projectSpatial(robot.map_id, robot.coordinates.x, robot.coordinates.y); return <div key={robot.id} title={`${robot.name} · ${robot.location}`} className="absolute z-20 -translate-x-1/2 -translate-y-1/2" style={{ left: `${position.x}%`, top: `${position.y}%` }}><img src={`/visual-assets/robots/${robot.id}.png`} alt={robot.name} className={`h-9 w-12 object-contain ${robot.id === selectedRobot ? "scale-110" : "opacity-80"}`} /><span className="mx-auto block h-1.5 w-1.5 rounded-full bg-slate-700" /></div>; })}
      {route.length > 1 && <p className="absolute bottom-2 left-3 z-30 border border-slate-200 bg-white/95 px-2 py-1 text-[9px] text-slate-600">Dijkstra 园区拓扑路线 · {route.map((point) => point.label).join(" → ")}</p>}
    </div>
  </section>;
}
