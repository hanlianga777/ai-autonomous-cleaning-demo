import { BatteryMedium, Navigation, Route } from "lucide-react";
import { stageCopy } from "./data";
import type { ActiveEvent } from "./types";

type Point = { x: number; y: number; location: string };

const resting: Record<string, Point> = {
  "Robot A": { x: 16, y: 80, location: "东侧道路" },
  "Robot B": { x: 33, y: 55, location: "A栋1F" },
  "Robot C": { x: 73, y: 58, location: "B栋1F" },
  "Robot D": { x: 86, y: 77, location: "配送区" },
};
const target: Record<string, Point> = {
  outdoor: { x: 29, y: 80, location: "东侧道路" },
  liquid: { x: 37, y: 55, location: "A栋1F大堂" },
  can: { x: 35, y: 28, location: "A栋2F连廊" },
  oversized: { x: 37, y: 25, location: "A栋2F" },
};

function robotPosition(robot: string, event: ActiveEvent | null): Point {
  if (!event || event.scenario.robot !== robot) return resting[robot];
  const state = event.scenario.steps[event.stageIndex];
  if (state === "ROBOT_ASSIGNED") return resting[robot];
  if (event.scenario.id !== "can" && ["NAVIGATING", "CLEANING", "VERIFYING", "CLOSED"].includes(state)) return target[event.scenario.id];
  if (event.scenario.id === "can") {
    if (state === "NAVIGATING") return { x: 76, y: 53, location: "B栋1F电梯" };
    if (state === "ELEVATOR_TRANSFER") return { x: 76, y: 36, location: "B栋电梯上行" };
    if (state === "SKYBRIDGE_TRANSFER") return { x: 56, y: 26, location: "2F空中连廊" };
    if (["CLEANING", "VERIFYING", "CLOSED"].includes(state)) return target.can;
  }
  return resting[robot];
}

function RobotMarker({ robot, event, battery, name }: { robot: string; event: ActiveEvent | null; battery: number; name: string }) {
  const position = robotPosition(robot, event);
  const active = event?.scenario.robot === robot && !["CLOSED", "HUMAN_FALLBACK"].includes(event.scenario.steps[event.stageIndex]);
  const state = active ? stageCopy[event!.scenario.steps[event!.stageIndex]].title : "空闲";
  return <div className="absolute z-20 -translate-x-1/2 -translate-y-1/2 transition-[left,top] duration-1000 ease-in-out" style={{ left: `${position.x}%`, top: `${position.y}%` }}>
    <div className={`w-[74px] border px-1.5 py-1 shadow-sm ${active ? "border-slate-800 bg-white/95" : "border-slate-300 bg-white/80"}`}>
      <div className="flex items-center justify-between gap-1"><span className="h-3.5 w-3.5 border border-dashed border-slate-300 bg-slate-50" /><span className="text-[8px] font-semibold text-slate-800">{name}</span><BatteryMedium size={10} className={battery < 40 ? "text-amber-500" : "text-emerald-600"} /></div>
      <p className="mt-0.5 truncate text-[8px] text-slate-500">{active ? `${state} · ${position.location}` : `${position.location} · 图片待补充`}</p>
    </div>
    {active && <span className="mx-auto block h-1.5 w-1.5 animate-pulse rounded-full bg-rose-500" />}
  </div>;
}

function Tower({ name, floors, x, baseY, width, depth }: { name: string; floors: string[]; x: number; baseY: number; width: number; depth: number }) {
  return <g>
    {floors.map((floor, index) => {
      const y = baseY - index * 55;
      const fill = index === floors.length - 1 ? "#eff6ff" : "#f8fafc";
      return <g key={floor}>
        <polygon points={`${x},${y} ${x + width},${y} ${x + width + depth},${y - depth} ${x + depth},${y - depth}`} fill={fill} fillOpacity="0.9" stroke="#94a3b8" strokeWidth="1.5" />
        <polygon points={`${x},${y} ${x + width},${y} ${x + width},${y + 15} ${x},${y + 15}`} fill="#dbe4ef" fillOpacity="0.66" stroke="#cbd5e1" strokeWidth="0.9" />
        <polygon points={`${x + width},${y} ${x + width + depth},${y - depth} ${x + width + depth},${y - depth + 15} ${x + width},${y + 15}`} fill="#cbd5e1" fillOpacity="0.56" stroke="#cbd5e1" strokeWidth="0.9" />
        <text x={x + 12} y={y - 8} fontSize="10" fill="#475569" fontWeight="600">{floor}</text>
      </g>;
    })}
    <text x={x + width / 2} y={baseY + 33} fontSize="13" fill="#334155" textAnchor="middle" fontWeight="700">{name}</text>
  </g>;
}

function CampusModel({ showRoute, scenario }: { showRoute: boolean; scenario?: string }) {
  const path = scenario === "can" ? "M730,250 L760,232 L760,159 L555,108 L350,130" : scenario === "outdoor" ? "M155,358 L290,360" : "M330,246 L370,238";
  return <svg className="absolute inset-0 h-full w-full" viewBox="0 60 1000 360" preserveAspectRatio="none" aria-label="透明园区建筑模型">
    <defs><filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="5" stdDeviation="5" floodColor="#64748b" floodOpacity="0.14" /></filter></defs>
    <polygon points="70,348 468,252 940,330 530,420" fill="#eef2f5" stroke="#cbd5e1" strokeWidth="1" />
    <path d="M95,348 L510,398 L910,330" fill="none" stroke="#cbd5e1" strokeWidth="18" strokeLinecap="round" opacity="0.55" />
    <path d="M95,348 L510,398 L910,330" fill="none" stroke="#ffffff" strokeWidth="1.4" strokeDasharray="6 7" opacity="0.9" />
    <text x="112" y="325" fontSize="11" fill="#64748b" fontWeight="600">室外道路 / 园区广场</text>
    <g filter="url(#soft-shadow)"><Tower name="A 栋" floors={["B1 设备区", "1F 大堂", "2F 公共区域"]} x={180} baseY={280} width={210} depth={68} /><Tower name="B 栋" floors={["1F 大厅", "2F 连廊入口"]} x={645} baseY={280} width={170} depth={56} /></g>
    <g opacity="0.85"><polygon points="390,170 645,170 701,114 446,114" fill="#e0f2fe" fillOpacity="0.68" stroke="#7dd3fc" strokeWidth="1.2" /><polygon points="390,170 645,170 645,185 390,185" fill="#cbd5e1" fillOpacity="0.5" /><text x="516" y="151" textAnchor="middle" fontSize="10" fill="#475569" fontWeight="700">2F 空中连廊</text></g>
    <g opacity="0.8"><rect x="750" y="182" width="20" height="87" fill="#e2e8f0" fillOpacity="0.76" stroke="#94a3b8" strokeDasharray="3 2" /><text x="760" y="227" textAnchor="middle" transform="rotate(-90 760 227)" fontSize="9" fill="#475569">B栋电梯</text></g>
    {showRoute && <g><path d={path} fill="none" stroke="#475569" strokeWidth="2" strokeDasharray="7 5" /><path d={path} fill="none" stroke="#ffffff" strokeWidth="0.6" strokeDasharray="7 5" opacity="0.65" /></g>}
  </svg>;
}

export function SpatialDispatchView({ event }: { event: ActiveEvent | null }) {
  const state = event ? event.scenario.steps[event.stageIndex] : "IDLE";
  const currentTarget = event ? target[event.scenario.id] : null;
  const activeRobot = event?.scenario.robot;
  const showRoute = Boolean(event && activeRobot && ["ROBOT_ASSIGNED", "NAVIGATING", "ELEVATOR_TRANSFER", "SKYBRIDGE_TRANSFER", "CLEANING", "VERIFYING"].includes(state));
  return <section className="relative min-h-[180px] overflow-hidden border border-slate-200 bg-[#f6f8f9]" aria-label="园区空间调度视图">
    <div className="absolute inset-x-0 top-0 z-30 flex h-10 items-center justify-between border-b border-slate-200 bg-white/92 px-3"><div className="flex items-center gap-2"><p className="text-sm font-semibold text-slate-900">园区空间调度</p><span className="text-[10px] text-slate-500">二维 SLAM 空间关系</span></div><div className="flex items-center gap-1.5 text-[10px] text-slate-500"><Route size={13} />固定视角</div></div>
    <div className="absolute inset-x-0 bottom-0 top-10 overflow-hidden"><CampusModel showRoute={showRoute} scenario={event?.scenario.id} />
      {currentTarget && <div className="absolute z-10 -translate-x-1/2 -translate-y-1/2" style={{ left: `${currentTarget.x}%`, top: `${currentTarget.y}%` }}><span className="block h-4 w-4 animate-pulse rounded-full border-2 border-rose-500 bg-rose-100/80" /><span className="absolute left-5 top-0 whitespace-nowrap text-[9px] font-semibold text-rose-700">清洁目标</span></div>}
      <RobotMarker robot="Robot A" name="室外清扫 A" event={event} battery={82} /><RobotMarker robot="Robot B" name="重载洗地 B" event={event} battery={71} /><RobotMarker robot="Robot C" name="室内清洁 C" event={event} battery={89} /><RobotMarker robot="Robot D" name="配送机器人 D" event={event} battery={64} />
    </div>
    <div className="absolute bottom-2 left-3 z-30 flex items-center gap-1.5 border border-slate-200 bg-white/90 px-2 py-1 text-[9px] text-slate-600"><Navigation size={11} className="text-slate-500" />{activeRobot ? `${activeRobot} · ${stageCopy[state].title}` : "4 台设备在线 · 配送机器人不参与清洁候选"}</div>
  </section>;
}
