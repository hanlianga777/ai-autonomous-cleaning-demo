import { BatteryCharging } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { MapCanvas } from "./MapCanvas";
import {
  projectBackendRoute,
  projectMapCoordinate,
  svgPath,
  type CanvasPoint,
  type EventTarget,
  type NavigationPlan,
  type RouteSegment,
} from "./spatialProjection";
import type { ActiveEvent } from "./types";
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
const ROBOT_ASSET_OFFSETS: Record<string, { x: number; scale: number }> = {
  "robot-a": { x: -1, scale: 1.2 }, "robot-b": { x: 0, scale: 1.15 }, "robot-c": { x: 1, scale: 1.18 }, "robot-d": { x: 0, scale: 1.12 },
};

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

function RouteLayer({ points, travelledDistance, terminal, style }: { points: CanvasPoint[]; travelledDistance: number; terminal: boolean; style?: NavigationPlan["visual_style"] }) {
  if (points.length < 2) return null;
  const fullPath = svgPath(points);
  const completedPath = svgPath(points, travelledDistance);
  const planned = style?.planned ?? "#1f5f8b";
  const completed = style?.completed ?? "#0c4a6e";
  return <svg className={`pointer-events-none absolute inset-0 z-10 h-full w-full ${terminal ? "opacity-45" : "opacity-100"}`} viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="园区规划路线">
    <path d={fullPath} fill="none" stroke={planned} strokeWidth="3" strokeDasharray="7 5" vectorEffect="non-scaling-stroke" />
    {travelledDistance > 0 && <path d={completedPath} fill="none" stroke={completed} strokeWidth="5" vectorEffect="non-scaling-stroke" />}
  </svg>;
}

function FleetAssetCard({ robot, active }: { robot: FleetRobot; active: boolean }) {
  const status = statusCopy[robot.status] ?? robot.status;
  const asset = ROBOT_ASSET_OFFSETS[robot.id] ?? { x: 0, scale: 1 };
  return <article className={`group relative border px-2 py-2 transition-colors ${active ? "border-slate-500 bg-slate-50" : "border-slate-200 bg-white hover:border-slate-300"}`}>
    <p className="text-[12px] font-semibold leading-4 text-slate-800">{robot.name}</p><div className="mt-1 flex items-center gap-1.5"><span className="flex h-7 w-8 shrink-0 items-center justify-center overflow-visible"><img src={`/visual-assets/robots/${robot.id}.png`} alt="" className="h-7 w-8 object-contain" style={{ transform: `translateX(${asset.x}px) scale(${asset.scale})` }} /></span><p className="flex-1 text-[12px] text-slate-500">{status}</p><span className="flex shrink-0 items-center gap-0.5 text-[12px] font-medium text-slate-600"><BatteryCharging size={11} strokeWidth={1.7} />{robot.battery}%</span></div>
    <div className="pointer-events-none absolute left-full top-0 z-50 ml-2 hidden w-52 border border-slate-300 bg-white p-3 text-[12px] leading-5 text-slate-600 shadow-lg group-hover:block"><p className="font-semibold text-slate-800">{robot.name}</p><p>{robot.location}</p><p className="mt-1 border-t border-slate-100 pt-1"><span className="text-slate-400">服务范围：</span>{robot.role ?? robot.zone ?? "园区服务区域"}</p><p><span className="text-slate-400">适用范围：</span>{robot.product_capability ?? robot.capabilities?.join(" / ") ?? "未配置"}</p></div>
  </article>;
}

function RobotMarker({ robot, point, active }: { robot: FleetRobot; point: CanvasPoint; active: boolean }) {
  const asset = ROBOT_ASSET_OFFSETS[robot.id] ?? { x: 0, scale: 1 };
  const isIndoor = robot.id === "robot-b" || robot.id === "robot-c";
  return <div className="absolute z-30 -translate-x-1/2 -translate-y-1/2" style={{ left: `${point.x}%`, top: `${point.y}%` }}><div className="relative flex flex-col items-center"><span className="pointer-events-none absolute bottom-[calc(100%-2px)] left-1/2 flex h-5 w-[116px] -translate-x-1/2 items-center justify-center whitespace-nowrap border border-white/90 bg-white/75 px-1.5 text-xs font-medium text-slate-700 shadow-sm backdrop-blur-[1px]">{robot.name}</span><span className={`flex h-8 w-11 items-center justify-center ${active ? "scale-110" : ""}`}><img src={`/visual-assets/robots/${robot.id}.png`} alt={robot.name} className={`h-8 w-11 object-contain drop-shadow-sm ${isIndoor ? "opacity-75" : "opacity-100"}`} style={{ transform: `translateX(${asset.x}px) scale(${asset.scale})` }} /></span><span className={`absolute bottom-0 left-1/2 h-1.5 w-1.5 -translate-x-1/2 rounded-full ${active ? "bg-[#4f7798]" : "bg-slate-600"}`} /></div></div>;
}

function idlePresentationPosition(robot: FleetRobot): CanvasPoint {
  if (robot.id === "robot-d" && !robot.active_task_id) return { x: 84, y: 81, label: "园区道路" };
  return projectMapCoordinate(robot.map_id, robot.coordinates.x, robot.coordinates.y);
}

export function SpatialDispatchView({ event, onNavigationComplete }: SpatialDispatchViewProps) {
  const [apiFleet, setApiFleet] = useState<FleetRobot[]>([]);
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
    () => {
      const routeNodeIds = new Set(routePoints.map((point) => point.nodeId));
      if (!routeNodeIds.size || !Array.isArray(plan?.segments)) return EMPTY_ROUTE_SEGMENTS;
      return (plan.segments as RouteSegment[]).filter((segment) => !segment.from || !segment.to || (routeNodeIds.has(segment.from) && routeNodeIds.has(segment.to)));
    },
    [plan, routePoints],
  );
  const isNavigating = event?.backendState === "NAVIGATING";
  const paused = isEventPaused(event);
  const playback = useRoutePlayback({ active: Boolean(isNavigating && selectedRobot && routePoints.length > 1), paused, pauseStartedAt: typeof event?.liveResult?.operations_pause_started_at === "string" ? event.liveResult.operations_pause_started_at : undefined, pausedMs: typeof event?.liveResult?.operations_paused_ms === "number" ? event.liveResult.operations_paused_ms : 0, navigationStartedAt: navigationStartedAt(event), points: routePoints, segments: routeSegments, onComplete: operationsOwnsEvent(event) ? undefined : onNavigationComplete });
  const routeReady = routePoints.length > 1;
  const displayedTravel = isNavigating ? playback.travelledDistance : playback.totalDistance;
  const activePosition = isNavigating ? playback.point : null;

  return <section className="grid min-h-[248px] grid-cols-[152px_minmax(0,1fr)] overflow-hidden border border-slate-200 bg-[#f6f8f9]" aria-label="园区空间调度">
    <aside className="z-40 overflow-visible border-r border-slate-200 bg-[#fbfcfd] p-2" aria-label="机器人状态"><div className="mb-2 border-b border-slate-200 pb-2"><p className="text-[12px] font-semibold text-slate-700">园区空间调度</p><p className="mt-0.5 text-[12px] text-slate-400">当前机器人状态</p></div><div className="space-y-1.5">{displayedFleet.map((robot) => <FleetAssetCard key={robot.id} robot={robot} active={robot.id === selectedRobotId || Boolean(robot.active_task_id)} />)}{!displayedFleet.length && <p className="py-4 text-center text-[12px] text-slate-400">机器人信息暂不可用</p>}</div></aside>
    <MapCanvas imageSrc="/visual-assets/campus/campus-white-model.png" alt="A栋与B栋园区空间白模" className="min-h-[248px] bg-[#eef2f5]">
      <>
        <RouteLayer points={routePoints} travelledDistance={displayedTravel} terminal={!isNavigating && routeReady} style={plan?.visual_style} />
        {target && <div className="absolute z-20 -translate-x-1/2 -translate-y-1/2" style={{ left: `${projectMapCoordinate(target.map_id, target.x, target.y).x}%`, top: `${projectMapCoordinate(target.map_id, target.x, target.y).y}%` }} aria-label="已定位事件位置"><span className="block h-4 w-4 rounded-full border-2 border-rose-500 bg-rose-100/95 shadow-sm" /><span className="absolute left-1/2 top-5 -translate-x-1/2 whitespace-nowrap text-[12px] font-medium text-rose-700">事件位置</span></div>}
        {displayedFleet.map((robot) => { const position = robot.id === selectedRobotId ? (activePosition ?? routePoints.at(-1) ?? idlePresentationPosition(robot)) : idlePresentationPosition(robot); return <RobotMarker key={robot.id} robot={robot} point={position} active={robot.id === selectedRobotId} />; })}
        {isNavigating && !paused && playback.isElevatorPause && <div className="absolute z-40 -translate-x-1/2 -translate-y-full border border-slate-300 bg-white px-2 py-1 text-[12px] font-medium text-slate-700 shadow-sm" style={{ left: `${playback.point?.x ?? 50}%`, top: `${playback.point?.y ?? 50}%` }}>乘梯中</div>}
      </>
    </MapCanvas>
  </section>;
}
