import { useEffect, useState } from "react";
import { Camera, Eye, EyeOff, Map } from "lucide-react";

import { fetchSpatialOverview } from "@/api/spatial";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { Robot } from "@/types/dashboard";
import type { Camera as CameraType, SpatialOverview } from "@/types/spatial";

import { SpatialControlPanel } from "./SpatialControlPanel";
import { SpatialMapCanvas } from "./SpatialMapCanvas";

export function SpatialOperations({ robots }: { robots: Robot[] }) {
  const [overview, setOverview] = useState<SpatialOverview>();
  const [mapId, setMapId] = useState("PARK");
  const [showCoverage, setShowCoverage] = useState(true);
  const [selectedCamera, setSelectedCamera] = useState<CameraType>();
  const [error, setError] = useState("");

  useEffect(() => { fetchSpatialOverview().then((data) => { setOverview(data); setSelectedCamera(data.cameras.find((camera) => camera.camera_id === "CAM-A1-01")); }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Spatial API unavailable")); }, []);

  if (error) return <Card className="mt-5"><CardContent className="p-6 text-sm text-amber-700">空间引擎数据暂不可用：{error}。基础 Dashboard 仍可正常使用。</CardContent></Card>;
  if (!overview) return <Card className="mt-5"><CardContent className="p-6 text-sm text-slate-500">正在加载 Spatial Engine…</CardContent></Card>;

  const tabs = [{ map_id: "PARK", label: "Park View" }, ...overview.maps];
  return <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.55fr)_360px]">
    <Card className="overflow-hidden"><CardHeader className="flex flex-col gap-4 p-5 pb-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="section-kicker">Spatial engine</p><h2 className="mt-1 text-base font-semibold">园区 SLAM 运营地图</h2><p className="mt-1 text-xs text-slate-500">Park → Building → Floor → Zone → Coordinate</p></div><button onClick={() => setShowCoverage((current) => !current)} className="flex items-center gap-1.5 self-start rounded-sm border border-slate-200 px-2.5 py-1.5 text-xs text-slate-600 hover:bg-slate-50">{showCoverage ? <Eye size={14} /> : <EyeOff size={14} />}{showCoverage ? "隐藏 Coverage" : "显示 Coverage"}</button></CardHeader>
      <div className="border-y border-slate-100 px-5"><div className="flex overflow-x-auto"><div className="flex min-w-max gap-1 py-3">{tabs.map((map) => <button key={map.map_id} onClick={() => setMapId(map.map_id)} className={`rounded-sm px-2.5 py-1.5 text-xs transition-colors ${mapId === map.map_id ? "bg-slate-900 text-white" : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"}`}>{map.label}</button>)}</div></div></div>
      <SpatialMapCanvas selectedMap={mapId} overview={overview} robots={robots} showCoverage={showCoverage} onCameraSelect={setSelectedCamera} />
      <CardContent className="grid gap-3 p-5 sm:grid-cols-[1fr_auto]"><div className="flex gap-4 text-[11px] text-slate-500"><span className="flex items-center gap-1"><Map size={13} />{overview.maps.length} local maps</span><span className="flex items-center gap-1"><Camera size={13} />{overview.cameras.length} fixed cameras</span></div>{selectedCamera && <button onClick={() => setMapId(selectedCamera.map_id)} className="flex items-center gap-1 text-left text-xs text-slate-600 hover:text-slate-950"><span className="h-2 w-2 rounded-full bg-blue-700" />{selectedCamera.camera_id} · {selectedCamera.name}</button>}</CardContent>
    </Card>
    <div><SpatialControlPanel overview={overview} selectedCamera={selectedCamera} /><Card className="mt-5"><CardContent className="p-4"><p className="section-kicker">Phase boundary</p><p className="mt-2 text-xs leading-5 text-slate-500">当前仅展示空间位置、连接器、路线与标定映射。未实现任务调度、机器人执行、工作流、YOLO/Qwen-VL 或 Agent。</p></CardContent></Card></div>
  </section>;
}
