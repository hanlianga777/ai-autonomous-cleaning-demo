import { BatteryCharging } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { MapCanvas } from "./MapCanvas";
import {
  projectMapCoordinate,
  svgPath,
  type CanvasPoint,
  type NavigationPlan,
} from "./spatialProjection";
import type { ActiveEvent } from "./types";
import type { NavigationPresentation } from "./navigationPresentation";

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
  overview_position?: { x: number; y: number; label?: string };
  capabilities?: string[];
  role?: string;
  product_capability?: string;
  demo_configuration?: string;
  /** Live Fleet ownership, returned by /api/robots; not inferred from the event view. */
  active_task_id?: string | null;
};

type SpatialDispatchViewProps = {
  event: ActiveEvent | null;
  presentation: NavigationPresentation;
};

const statusCopy: Record<string, string> = {
  idle: "待命", assigned: "已分配", navigating: "行驶中", arrived: "已到达",
  cleaning: "清洁中", verifying: "验收中", charging: "充电中", paused: "已暂停",
};
const ROBOT_ASSET_OFFSETS: Record<string, { x: number; scale: number }> = {
  "robot-a": { x: -1, scale: 1.2 }, "robot-b": { x: 0, scale: 1.15 }, "robot-c": { x: 1, scale: 1.18 }, "robot-d": { x: 0, scale: 1.12 },
};
const FLEET_LIST_ASSET_OFFSETS: Record<string, { x: number; scale: number }> = {
  "robot-a": { x: 0, scale: 0.86 }, "robot-b": { x: 0, scale: 0.88 }, "robot-c": { x: 0, scale: 0.9 }, "robot-d": { x: 0, scale: 0.84 },
};

function fleetFromEvent(event: ActiveEvent | null, fallback: FleetRobot[]): FleetRobot[] {
  const snapshot = event?.liveResult?.fleet_snapshot;
  // The event snapshot is still a startup fallback. Once /api/robots answers,
  // use it so another task's live ownership/battery/status is not hidden.
  return fallback.length ? fallback : Array.isArray(snapshot) ? snapshot as FleetRobot[] : [];
}

function RouteLayer({ points, style }: { points: CanvasPoint[]; style?: NavigationPlan["visual_style"] }) {
  if (points.length < 2) return null;
  const fullPath = svgPath(points);
  return <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="园区规划路线">
    <path d={fullPath} fill="none" stroke={style?.route ?? "#b91c1c"} strokeOpacity={style?.opacity ?? 0.45} strokeWidth={style?.stroke_width ?? 5} strokeDasharray={style?.dasharray ?? "7 5"} vectorEffect="non-scaling-stroke" />
  </svg>;
}

function RouteEndpointRing({ point, style }: { point?: CanvasPoint; style?: NavigationPlan["visual_style"] }) {
  if (!point) return null;
  return <span aria-label="已识别垃圾点" className="pointer-events-none absolute z-40 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-[1.5px]" style={{ left: `${point.x}%`, top: `${point.y}%`, borderColor: style?.route ?? "#b91c1c", opacity: style?.opacity ?? 0.45 }} />;
}

function FleetSummary({ robot, translucent = false, workbenchList = false }: { robot: FleetRobot; translucent?: boolean; workbenchList?: boolean }) {
  const status = statusCopy[robot.status] ?? robot.status;
  const asset = FLEET_LIST_ASSET_OFFSETS[robot.id] ?? { x: 0, scale: 1 };
  const src = workbenchList ? `/visual-assets/workbench-fleet/${robot.id}.jpg` : `/visual-assets/robots/${robot.id}.png`;
  return <div className={translucent ? "border border-white/70 bg-white/55 px-2 py-2 shadow-lg backdrop-blur-sm" : "px-2 py-2"}>
    <p className="text-[12px] font-semibold leading-4 text-slate-800">{robot.name}</p><div className="mt-1 grid grid-cols-[32px_minmax(0,1fr)_auto] items-center gap-1.5"><span className="flex h-7 w-8 shrink-0 items-center justify-center overflow-hidden"><img src={src} alt="" className={`h-7 w-8 object-contain ${workbenchList ? "mix-blend-multiply" : ""}`} style={{ transform: `translateX(${asset.x}px) scale(${asset.scale})` }} /></span><p className="min-w-0 text-[12px] text-slate-500">{status}</p><span className="flex shrink-0 items-center gap-0.5 text-[12px] font-medium text-slate-600"><BatteryCharging size={11} strokeWidth={1.7} />{robot.battery}%</span></div>
  </div>;
}

function FleetAssetCard({ robot, active }: { robot: FleetRobot; active: boolean }) {
  return <article className={`group relative border transition-colors ${active ? "border-slate-500 bg-slate-50" : "border-slate-200 bg-white hover:border-slate-300"}`}>
    <FleetSummary robot={robot} workbenchList />
    <div className="pointer-events-none absolute left-full top-0 z-50 ml-2 hidden w-52 border border-slate-300 bg-white p-3 text-[12px] leading-5 text-slate-600 shadow-lg group-hover:block"><p className="font-semibold text-slate-800">{robot.name}</p><p>{robot.location}</p><p className="mt-1 border-t border-slate-100 pt-1"><span className="text-slate-400">服务范围：</span>{robot.role ?? robot.zone ?? "园区服务区域"}</p><p><span className="text-slate-400">适用范围：</span>{robot.product_capability ?? robot.capabilities?.join(" / ") ?? "未配置"}</p></div>
  </article>;
}

function RobotMarker({ robot, point, active }: { robot: FleetRobot; point: CanvasPoint; active: boolean }) {
  const asset = ROBOT_ASSET_OFFSETS[robot.id] ?? { x: 0, scale: 1 };
  const isIndoor = robot.id === "robot-b" || robot.id === "robot-c";
  const expandInward = point.x > 68;
  return <div className="group absolute z-30 -translate-x-1/2 -translate-y-1/2 outline-none" style={{ left: `${point.x}%`, top: `${point.y}%` }} tabIndex={0} aria-label={`${robot.name} 地图机器人`}><div className="relative flex flex-col items-center"><span className="pointer-events-none absolute bottom-[calc(100%-1px)] left-1/2 flex h-4 w-[104px] -translate-x-1/2 items-center justify-center whitespace-nowrap border border-white/80 bg-white/55 px-1 text-xs font-normal text-slate-700 shadow-sm backdrop-blur-[1px] scale-[0.92]">{robot.name}</span><span className="flex h-8 w-11 items-center justify-center"><img src={`/visual-assets/robots/${robot.id}.png`} alt={robot.name} className={`h-8 w-11 object-contain drop-shadow-sm ${isIndoor ? "opacity-60" : "opacity-100"}`} style={{ transform: `translateX(${asset.x}px) scale(${asset.scale})` }} /></span>{!active && <span className="absolute bottom-0 left-1/2 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-slate-600" />}</div><div className={`pointer-events-none absolute top-1/2 z-50 hidden w-[136px] -translate-y-1/2 group-hover:block group-focus:block ${expandInward ? "right-full mr-3" : "left-full ml-3"}`}><FleetSummary robot={robot} translucent /></div></div>;
}

function idlePresentationPosition(robot: FleetRobot): CanvasPoint {
  if (robot.overview_position) return robot.overview_position;
  if (robot.id === "robot-d" && !robot.active_task_id) return { x: 84, y: 81, label: "园区道路" };
  return projectMapCoordinate(robot.map_id, robot.coordinates.x, robot.coordinates.y);
}

export function SpatialDispatchView({ event, presentation }: SpatialDispatchViewProps) {
  const [apiFleet, setApiFleet] = useState<FleetRobot[]>([]);
  const { selectedRobotId, plan, routePoints, routeReady, isNavigating, paused, robotPosition, isElevatorPause } = presentation;

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
  return <section className="grid min-h-[248px] grid-cols-[152px_minmax(0,1fr)] overflow-hidden border border-slate-200 bg-[#f6f8f9]" aria-label="园区空间调度">
    <aside className="z-40 overflow-visible border-r border-slate-200 bg-[#fbfcfd] p-2" aria-label="机器人状态"><div className="mb-2 border-b border-slate-200 pb-2"><p className="text-[12px] font-semibold text-slate-700">园区空间调度</p><p className="mt-0.5 text-[12px] text-slate-400">当前机器人状态</p></div><div className="space-y-1.5">{displayedFleet.map((robot) => <FleetAssetCard key={robot.id} robot={robot} active={robot.id === selectedRobotId || Boolean(robot.active_task_id)} />)}{!displayedFleet.length && <p className="py-4 text-center text-[12px] text-slate-400">机器人信息暂不可用</p>}</div></aside>
    <MapCanvas imageSrc="/visual-assets/campus/campus-white-model.png" alt="A栋与B栋园区空间白模" className="min-h-[248px] bg-[#eef2f5]">
      <>
        <RouteLayer points={routePoints} style={plan?.visual_style} />
        {routeReady && <RouteEndpointRing point={routePoints.at(-1)} style={plan?.visual_style} />}
        {displayedFleet.map((robot) => { const position = robot.id === selectedRobotId ? (robotPosition ?? idlePresentationPosition(robot)) : idlePresentationPosition(robot); return <RobotMarker key={robot.id} robot={robot} point={position} active={robot.id === selectedRobotId} />; })}
        {isNavigating && !paused && isElevatorPause && <div className="absolute z-40 -translate-x-1/2 -translate-y-full border border-slate-300 bg-white/80 px-2 py-1 text-xs font-normal text-slate-700 shadow-sm" style={{ left: `${robotPosition?.x ?? 50}%`, top: `${robotPosition?.y ?? 50}%` }}>乘梯中</div>}
      </>
    </MapCanvas>
  </section>;
}
