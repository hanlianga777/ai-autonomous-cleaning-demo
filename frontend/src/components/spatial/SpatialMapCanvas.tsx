import { Building2, Camera, CircleDot, DoorOpen, Route as RouteIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Camera as CameraType, SpatialMap, SpatialOverview } from "@/types/spatial";
import type { Robot } from "@/types/dashboard";

const robotTone: Record<string, string> = { "robot-a": "#334155", "robot-b": "#b45309", "robot-c": "#0f766e" };

export function SpatialMapCanvas({ selectedMap, overview, robots, showCoverage, onCameraSelect }: { selectedMap: string; overview: SpatialOverview; robots: Robot[]; showCoverage: boolean; onCameraSelect: (camera: CameraType) => void; }) {
  if (selectedMap === "PARK") return <ParkMap overview={overview} robots={robots} />;
  const map = overview.maps.find((item) => item.map_id === selectedMap);
  if (!map) return <div className="flex h-[440px] items-center justify-center text-sm text-slate-500">空间地图数据不可用</div>;
  const cameras = overview.cameras.filter((camera) => camera.map_id === map.map_id);
  const mapRobots = robots.filter((robot) => overview.robot_positions[robot.id]?.map_id === map.map_id);
  return <div className="relative h-[440px] overflow-hidden bg-[#f7f9f9] p-4 sm:p-6">
    <div className="absolute left-5 top-5 z-10 flex items-center gap-2 border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-sm"><RouteIcon size={14} className="text-slate-500" /><span className="font-medium text-slate-700">{map.label}</span><span className="text-slate-400">SLAM local frame · metres</span></div>
    <svg className="h-full w-full" viewBox={`0 0 ${map.width} ${map.height}`} role="img" aria-label={`${map.label} SLAM map`}>
      <defs><pattern id="grid" width="5" height="5" patternUnits="userSpaceOnUse"><path d="M 5 0 L 0 0 0 5" fill="none" stroke="#e6eaec" strokeWidth="0.22" /></pattern></defs>
      <rect width={map.width} height={map.height} fill="url(#grid)" />
      {map.zones.map((zone, index) => <g key={zone.zone_id}><rect x={zone.x} y={zone.y} width={zone.w} height={zone.h} fill={index % 2 ? "#edf1f2" : "#f2f5f5"} stroke="#b9c2c7" strokeWidth="0.42" /><text x={zone.x + 2} y={zone.y + 4} fill="#5c6870" fontSize="2.4" fontWeight="600">{zone.name}</text><text x={zone.x + 2} y={zone.y + 7.2} fill="#8a969d" fontSize="1.65">{zone.surface_type.toUpperCase()} · {zone.crowd_level}</text></g>)}
      {map.obstacles.map((obstacle, index) => <rect key={index} {...obstacle} fill="#7b8790" opacity="0.84" />)}
      {showCoverage && cameras.map((camera) => <polygon key={camera.camera_id} points={camera.coverage_polygon.map((point) => `${point.x},${point.y}`).join(" ")} fill="#dbeafe" fillOpacity="0.48" stroke="#60a5fa" strokeWidth="0.4" strokeDasharray="1.2 1.2" />)}
      {(map.navigation_nodes ?? []).map((node, index) => <circle key={index} cx={node.x} cy={node.y} r="0.85" fill="#94a3b8" />)}
      {(map.entrances ?? []).map((entry) => <g key={entry.id}><rect x={entry.x - 1.7} y={entry.y - 1.7} width="3.4" height="3.4" fill="#fff" stroke="#64748b" strokeWidth="0.5" /><text x={entry.x + 2.5} y={entry.y + 0.8} fontSize="1.8" fill="#64748b">{entry.label}</text></g>)}
      {(map.elevators ?? []).map((elevator) => <g key={elevator.id}><rect x={elevator.x - 2.2} y={elevator.y - 2.2} width="4.4" height="4.4" fill="#fffbeb" stroke="#d97706" strokeWidth="0.65" /><path d={`M ${elevator.x - 0.9} ${elevator.y + 0.8} V ${elevator.y - 0.8} M ${elevator.x - 0.9} ${elevator.y - 0.8} l -0.7 0.7 M ${elevator.x - 0.9} ${elevator.y - 0.8} l 0.7 0.7 M ${elevator.x + 0.9} ${elevator.y - 0.8} V ${elevator.y + 0.8} M ${elevator.x + 0.9} ${elevator.y + 0.8} l -0.7 -0.7 M ${elevator.x + 0.9} ${elevator.y + 0.8} l 0.7 -0.7`} stroke="#a16207" strokeWidth="0.42" fill="none" /><text x={elevator.x + 3} y={elevator.y + 0.8} fontSize="1.8" fill="#a16207">{elevator.label}</text></g>)}
      {cameras.map((camera) => <g key={camera.camera_id} className="cursor-pointer" onClick={() => onCameraSelect(camera)}><circle cx={camera.camera_position.x} cy={camera.camera_position.y} r="2.1" fill="#1e3a5f" stroke="#fff" strokeWidth="0.65" /><path d={`M ${camera.camera_position.x - 0.8} ${camera.camera_position.y - 0.4} h 1.6 v 1.1 h -1.6z`} fill="#fff" /><text x={camera.camera_position.x + 2.8} y={camera.camera_position.y + 0.8} fontSize="1.8" fill="#1e3a5f" fontWeight="600">{camera.camera_id}</text></g>)}
      {mapRobots.map((robot) => { const position = overview.robot_positions[robot.id]; return <g key={robot.id}><circle cx={position.x} cy={position.y} r="2.3" fill={robotTone[robot.id]} stroke="#fff" strokeWidth="0.8" /><text x={position.x} y={position.y + 0.7} fill="#fff" fontSize="1.8" fontWeight="700" textAnchor="middle">{robot.short_name.slice(-1)}</text><text x={position.x + 3.1} y={position.y + 0.8} fill={robotTone[robot.id]} fontSize="1.8" fontWeight="700">{robot.short_name}</text></g>; })}
    </svg>
    <div className="absolute bottom-5 left-5 flex items-center gap-3 border border-slate-200 bg-white/95 px-3 py-2 text-[11px] text-slate-500"><span className="flex items-center gap-1"><Camera size={13} className="text-[#1e3a5f]" />Camera</span><span className="flex items-center gap-1"><Building2 size={13} className="text-amber-700" />Elevator</span><span className="flex items-center gap-1"><CircleDot size={13} />Nav node</span></div>
  </div>;
}

function ParkMap({ overview, robots }: { overview: SpatialOverview; robots: Robot[] }) {
  const robotById = Object.fromEntries(robots.map((robot) => [robot.id, robot]));
  const marker = (robotId: string, left: string, top: string) => <div key={robotId} className={cn("absolute z-10 flex h-7 w-7 items-center justify-center rounded-full border-2 border-white text-[10px] font-bold text-white shadow-sm", robotId === "robot-a" ? "bg-slate-700" : robotId === "robot-b" ? "bg-amber-700" : "bg-teal-700", left, top)} title={robotById[robotId]?.short_name}>{robotById[robotId]?.short_name.slice(-1)}</div>;
  return <div className="relative h-[440px] overflow-hidden bg-[#f7f9f9] p-6 campus-grid">
    <div className="absolute left-[11%] top-[18%] h-[48%] w-[28%] border border-slate-300 bg-white p-5 shadow-sm"><Building2 size={22} className="text-slate-400" /><p className="mt-3 font-semibold text-slate-800">A 栋</p><p className="mt-1 text-xs text-slate-500">B1 · 1F · 2F</p><p className="mt-5 text-[11px] text-slate-400">A Elevator</p></div>
    <div className="absolute right-[11%] top-[18%] h-[48%] w-[28%] border border-slate-300 bg-white p-5 shadow-sm"><Building2 size={22} className="text-slate-400" /><p className="mt-3 font-semibold text-slate-800">B 栋</p><p className="mt-1 text-xs text-slate-500">1F · 2F</p><p className="mt-5 text-[11px] text-slate-400">B Elevator</p></div>
    <div className="absolute left-[39%] right-[39%] top-[32%] h-9 border-y border-dashed border-slate-300 bg-slate-100 px-2 pt-2 text-center text-[10px] font-medium text-slate-500">2F SKYBRIDGE</div>
    <div className="absolute bottom-[11%] left-[8%] text-xs text-slate-500"><DoorOpen size={15} className="mr-1 inline" />园区道路 · 公共广场 · 外围花岗岩</div>
    {marker("robot-a", "left-[22%]", "top-[76%]")}{marker("robot-b", "left-[31%]", "top-[52%]")}{marker("robot-c", "right-[27%]", "top-[49%]")}
    <div className="absolute right-5 top-5 border border-slate-200 bg-white/95 px-3 py-2 text-xs text-slate-500">Park View · {overview.maps.length} SLAM maps</div>
  </div>;
}
