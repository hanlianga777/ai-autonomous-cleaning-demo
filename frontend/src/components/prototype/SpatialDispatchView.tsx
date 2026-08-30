import { BatteryCharging, Navigation, Route, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { MapCanvas } from "./MapCanvas";
import {
  pointAtRouteDistance,
  projectBackendRoute,
  projectMapCoordinate,
  svgPath,
  type CanvasPoint,
  type EventTarget,
  type NavigationPlan,
  type RouteSegment,
} from "./spatialProjection";
import type { ActiveEvent, PrototypeState } from "./types";
import { useRoutePlayback } from "./useRoutePlayback";
import { isEventPaused, operationsOwnsEvent } from "./runtimeSession";

type FleetRobot = {
  id: string;
  name: string;
  status: string;
  battery: number;
  location: string;
  building?: string;
  floor?: string | null;
  zone?: string;
  map_id: string;
  coordinates: { x: number; y: number };
  capabilities?: string[];
  role?: string;
  product_capability?: string;
  demo_configuration?: string;
  /** Live Fleet ownership, returned by /api/robots; not inferred from the event view. */
  active_task_id?: string | null;
};

type Transition = {
  state?: string;
  created_at?: string;
  detail?: { fleet_robot?: FleetRobot };
};

type SpatialDispatchViewProps = {
  event: ActiveEvent | null;
  /** Main workbench owns the durable backend POST after visual route completion. */
  onNavigationComplete?: () => void;
};

const statusCopy: Record<string, string> = {
  idle: "待命", assigned: "已分配", navigating: "行驶中", arrived: "已到达",
  cleaning: "清洁中", verifying: "验收中", charging: "充电中", paused: "已暂停",
};
const EMPTY_ROUTE_SEGMENTS: RouteSegment[] = [];

function displayState(event: ActiveEvent | null): PrototypeState {
  return event?.inFlightState ?? (event ? event.scenario.steps[event.stageIndex] : "IDLE");
}

function activeRobotId(event: ActiveEvent | null): string | null {
  const decision = event?.liveResult?.assignment_decision as { selected_robot_id?: string } | undefined;
  return decision?.selected_robot_id ?? null;
}

function navigationStartedAt(event: ActiveEvent | null): string | undefined {
  const transitions = event?.liveResult?.transitions;
  if (!Array.isArray(transitions)) return undefined;
  return [...(transitions as Transition[])].reverse().find((transition) => transition.state === "NAVIGATING")?.created_at;
}

function navigationPlan(event: ActiveEvent | null): NavigationPlan | undefined {
  const value = event?.liveResult?.navigation_plan;
  return value && typeof value === "object" ? value as NavigationPlan : undefined;
}

function fleetFromEvent(event: ActiveEvent | null, fallback: FleetRobot[]): FleetRobot[] {
  const snapshot = event?.liveResult?.fleet_snapshot;
  // The event snapshot is still a startup fallback. Once /api/robots answers,
  // use it so another task's live ownership/battery/status is not hidden.
  return fallback.length ? fallback : Array.isArray(snapshot) ? snapshot as FleetRobot[] : [];
}

/** Route origin is the persisted assignment snapshot, never a later terminal fleet position. */
function routeOrigin(event: ActiveEvent | null, selectedRobot: FleetRobot | null): FleetRobot | null {
  const transitions = event?.liveResult?.transitions;
  if (Array.isArray(transitions)) {
    const assigned = [...(transitions as Transition[])].reverse().find((transition) => transition.state === "ASSIGNED");
    if (assigned?.detail?.fleet_robot) return assigned.detail.fleet_robot;
  }
  return selectedRobot;
}

function routeArrowPoints(points: CanvasPoint[], travelledDistance: number, totalDistance: number): CanvasPoint[] {
  if (points.length < 2 || !totalDistance) return [];
  return [0.32, 0.7]
    .map((ratio) => totalDistance * ratio)
    .filter((distance) => distance <= travelledDistance + 0.5)
    .map((distance) => pointAtRouteDistance(points, distance))
    .filter((point): point is CanvasPoint => Boolean(point));
}

function RouteLayer({ points, travelledDistance, totalDistance, terminal }: { points: CanvasPoint[]; travelledDistance: number; totalDistance: number; terminal: boolean }) {
  if (points.length < 2) return null;
  const fullPath = svgPath(points);
  const completedPath = svgPath(points, travelledDistance);
  return <svg className={`pointer-events-none absolute inset-0 z-10 h-full w-full ${terminal ? "opacity-45" : "opacity-100"}`} viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="后端 Dijkstra 园区拓扑路线">
    <path d={fullPath} fill="none" stroke="#a7b7c9" strokeWidth="1.15" strokeDasharray="3.5 3" vectorEffect="non-scaling-stroke" />
    {travelledDistance > 0 && <path d={completedPath} fill="none" stroke="#4f7798" strokeWidth="1.75" vectorEffect="non-scaling-stroke" />}
    {routeArrowPoints(points, travelledDistance, totalDistance).map((point, index) => <g key={`${point.x}-${point.y}-${index}`} transform={`translate(${point.x} ${point.y})`}><path d="M-1.4,-1.4 L1.5,0 L-1.4,1.4" fill="none" stroke="#4f7798" strokeWidth="0.8" vectorEffect="non-scaling-stroke" /></g>)}
  </svg>;
}

function FleetAssetCard({ robot, active }: { robot: FleetRobot; active: boolean }) {
  const status = statusCopy[robot.status] ?? robot.status;
  return <article className={`group relative border px-2 py-2 transition-colors ${active ? "border-slate-500 bg-slate-50" : "border-slate-200 bg-white hover:border-slate-300"}`}>
    <p className="text-[10px] font-semibold leading-4 text-slate-800">{robot.name}</p><div className="mt-1 flex items-center gap-1.5"><img src={`/visual-assets/robots/${robot.id}.png`} alt="" className="h-7 w-8 shrink-0 object-contain" /><p className="flex-1 text-[9px] text-slate-500">{status}</p><span className="flex shrink-0 items-center gap-0.5 text-[9px] font-medium text-slate-600"><BatteryCharging size={11} strokeWidth={1.7} />{robot.battery}%</span></div>
    <div className="pointer-events-none absolute left-full top-0 z-50 ml-2 hidden w-52 border border-slate-300 bg-white p-3 text-[10px] leading-5 text-slate-600 shadow-lg group-hover:block"><p className="font-semibold text-slate-800">{robot.name}</p><p>{robot.location}</p><p className="mt-1 border-t border-slate-100 pt-1"><span className="text-slate-400">服务范围：</span>{robot.role ?? robot.zone ?? "园区服务区域"}</p><p><span className="text-slate-400">适用范围：</span>{robot.product_capability ?? robot.capabilities?.join(" / ") ?? "未配置"}</p></div>
  </article>;
}

function RobotMarker({ robot, point, active }: { robot: FleetRobot; point: CanvasPoint; active: boolean }) {
  return <div className="absolute z-30 -translate-x-1/2 -translate-y-1/2" style={{ left: `${point.x}%`, top: `${point.y}%` }}><div className={`relative ${active ? "scale-110" : "opacity-80"}`}><img src={`/visual-assets/robots/${robot.id}.png`} alt={robot.name} className="h-8 w-11 object-contain drop-shadow-sm" /><span className={`absolute bottom-0 left-1/2 h-1.5 w-1.5 -translate-x-1/2 rounded-full ${active ? "bg-[#4f7798]" : "bg-slate-600"}`} /></div></div>;
}

export function SpatialDispatchView({ event, onNavigationComplete }: SpatialDispatchViewProps) {
  const [apiFleet, setApiFleet] = useState<FleetRobot[]>([]);
  const state = displayState(event);
  const selectedRobotId = activeRobotId(event);
  const plan = navigationPlan(event);
  const target = event?.liveResult?.spatial_location as EventTarget | undefined;

  useEffect(() => {
    let active = true;
    let inFlight = false;
    const loadFleet = async () => {
      if (!active || inFlight) return;
      inFlight = true;
      try {
        const response = await fetch("/api/robots");
        if (!response.ok) throw new Error("Fleet unavailable");
        const fleet = await response.json() as FleetRobot[];
        if (active && Array.isArray(fleet)) setApiFleet(fleet);
      } catch {
        // Keep the last known live response (or event snapshot fallback); do not erase it on one failed poll.
      } finally { inFlight = false; }
    };
    void loadFleet();
    const timer = window.setInterval(() => void loadFleet(), 1500);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  const displayedFleet = useMemo(() => fleetFromEvent(event, apiFleet), [apiFleet, event]);
  const selectedRobot = displayedFleet.find((robot) => robot.id === selectedRobotId) ?? null;
  const origin = routeOrigin(event, selectedRobot);
  const routePoints = useMemo(() => projectBackendRoute(plan, origin, target), [plan, origin, target]);
  const routeSegments = useMemo(
    () => Array.isArray(plan?.segments) ? plan.segments as RouteSegment[] : EMPTY_ROUTE_SEGMENTS,
    [plan],
  );
  const isNavigating = event?.backendState === "NAVIGATING";
  const paused = isEventPaused(event);
  const playback = useRoutePlayback({ active: Boolean(isNavigating && selectedRobot && routePoints.length > 1), paused, pauseStartedAt: typeof event?.liveResult?.operations_pause_started_at === "string" ? event.liveResult.operations_pause_started_at : undefined, pausedMs: typeof event?.liveResult?.operations_paused_ms === "number" ? event.liveResult.operations_paused_ms : 0, navigationStartedAt: navigationStartedAt(event), points: routePoints, segments: routeSegments, onComplete: operationsOwnsEvent(event) ? undefined : onNavigationComplete });
  const routeReady = routePoints.length > 1;
  const displayedTravel = isNavigating ? playback.travelledDistance : playback.totalDistance;
  const activePosition = isNavigating ? playback.point : null;

  return <section className="grid min-h-[248px] grid-cols-[152px_minmax(0,1fr)] overflow-hidden border border-slate-200 bg-[#f6f8f9]" aria-label="园区空间调度">
    <aside className="z-40 overflow-visible border-r border-slate-200 bg-[#fbfcfd] p-2" aria-label="机器人状态"><div className="mb-2 border-b border-slate-200 pb-2"><p className="text-[11px] font-semibold text-slate-700">园区空间调度</p><p className="mt-0.5 text-[9px] text-slate-400">当前机器人状态</p></div><div className="space-y-1.5">{displayedFleet.map((robot) => <FleetAssetCard key={robot.id} robot={robot} active={robot.id === selectedRobotId || Boolean(robot.active_task_id)} />)}{!displayedFleet.length && <p className="py-4 text-center text-[10px] text-slate-400">机器人信息暂不可用</p>}</div></aside>
    <MapCanvas imageSrc="/visual-assets/campus/campus-white-model.png" alt="A栋与B栋园区空间白模" className="min-h-[248px] bg-[#eef2f5]">
      <>
        <RouteLayer points={routePoints} travelledDistance={displayedTravel} totalDistance={playback.totalDistance} terminal={!isNavigating && routeReady} />
        {target && <div className="absolute z-20 -translate-x-1/2 -translate-y-1/2" style={{ left: `${projectMapCoordinate(target.map_id, target.x, target.y).x}%`, top: `${projectMapCoordinate(target.map_id, target.x, target.y).y}%` }} aria-label="已定位事件位置"><span className="block h-4 w-4 rounded-full border-2 border-rose-500 bg-rose-100/95 shadow-sm" /><span className="absolute left-1/2 top-5 -translate-x-1/2 whitespace-nowrap text-[8px] font-medium text-rose-700">事件位置</span></div>}
        {displayedFleet.map((robot) => { const position = robot.id === selectedRobotId && activePosition ? activePosition : projectMapCoordinate(robot.map_id, robot.coordinates.x, robot.coordinates.y); return <RobotMarker key={robot.id} robot={robot} point={position} active={robot.id === selectedRobotId} />; })}
        {isNavigating && !paused && playback.isElevatorPause && <div className="absolute z-40 -translate-x-1/2 -translate-y-full border border-slate-300 bg-white px-2 py-1 text-[10px] font-medium text-slate-700 shadow-sm" style={{ left: `${playback.point?.x ?? 50}%`, top: `${playback.point?.y ?? 50}%` }}>乘梯中</div>}
        <div className="absolute bottom-[3%] left-[3%] z-40 flex max-w-[72%] items-center gap-1.5 border border-slate-200 bg-white/95 px-2 py-1 text-[9px] text-slate-600 shadow-sm"><Route size={11} strokeWidth={1.7} className="shrink-0 text-[#4f7798]" />{routeReady ? <span>{isNavigating ? "机器人正沿规划路线前往现场" : "本次处置路线已保存"}</span> : <span>定位完成后显示前往现场的路线</span>}</div>
        {selectedRobot && isNavigating && <div className="absolute right-[3%] top-[3%] z-40 flex items-center gap-1 border border-slate-200 bg-white/95 px-2 py-1 text-[9px] text-slate-600 shadow-sm"><Navigation size={11} className="text-[#4f7798]" />{selectedRobot.name} · {paused ? "已暂停" : "行驶中"}</div>}
        {!event && <div className="absolute left-1/2 top-1/2 z-20 flex -translate-x-1/2 -translate-y-1/2 items-center gap-1.5 border border-slate-200 bg-white/95 px-3 py-1.5 text-[10px] text-slate-500 shadow-sm"><Sparkles size={12} />等待固定摄像头发现事件</div>}
      </>
    </MapCanvas>
  </section>;
}
