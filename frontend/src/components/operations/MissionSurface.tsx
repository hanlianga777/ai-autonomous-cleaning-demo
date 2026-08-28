import { CheckCircle2, MapPinned, ScanLine } from "lucide-react";

import { SpatialMissionMap } from "@/components/operations/SpatialMissionMap";
import { DetectionFrame } from "@/components/operations/DetectionFrame";
import type { OperationsSnapshot } from "@/types/operations";
import type { SpatialOverview } from "@/types/spatial";

const executionStates = new Set(["ASSIGNED", "NAVIGATING", "ARRIVED", "CLEANING"]);

export function MissionSurface({ snapshot, spatial, mapId, onMapChange }: { snapshot: OperationsSnapshot; spatial?: SpatialOverview; mapId: string; onMapChange: (id: string) => void }) {
  const order = snapshot.active_work_order;
  if (!order) return <section className="flex min-h-[510px] items-center justify-center border border-slate-200 bg-white p-8 text-center"><div><ScanLine size={22} className="mx-auto text-slate-300" /><h3 className="mt-3 text-sm font-semibold text-slate-700">等待新的清洁事件</h3><p className="mt-1 max-w-sm text-xs leading-5 text-slate-500">固定摄像头发现异常后，这里会先呈现现场画面，再在派单后切换为机器人空间执行。</p></div></section>;
  const before = order.asset_manifest.assets.find((asset) => asset.role === "before");
  const after = order.asset_manifest.assets.find((asset) => asset.role === "after");
  if (order.display_state === "CLOSED") return <section className="overflow-hidden border border-slate-200 bg-white"><header className="flex items-center justify-between border-b border-slate-100 p-4"><div><p className="section-kicker">固定摄像头自动验收</p><h3 className="mt-1 text-base font-semibold">清洁前后对比</h3></div><span className="flex items-center gap-1 text-xs font-semibold text-emerald-700"><CheckCircle2 size={14} />验收通过</span></header><div className="grid gap-px bg-slate-200 sm:grid-cols-2"><Frame asset={before} label="清洁前" /><Frame asset={after} label="清洁后" /></div><p className="p-3 text-[11px] leading-5 text-slate-500">固定摄像头复核完成后才会关闭工单。当前演示为 Mock Verification；REAL 模式会明确显示真实视觉模型的返回。</p></section>;
  if (executionStates.has(order.display_state)) return <SpatialMissionMap spatial={spatial} mapId={mapId} onMapChange={onMapChange} fleet={snapshot.fleet} activeWorkOrder={order} />;
  return <section className="overflow-hidden border border-slate-200 bg-white"><header className="flex items-center justify-between border-b border-slate-100 p-4"><div><p className="section-kicker">固定摄像头现场</p><h3 className="mt-1 text-base font-semibold">{order.event.location.building} 栋 · {order.event.location.floor} · {order.event.location.zone}</h3></div><span className="text-xs font-semibold text-amber-700">AI 正在判断</span></header><DetectionFrame asset={before} label="清洁前现场" /><p className="flex items-center gap-1 p-3 text-[11px] text-slate-500"><MapPinned size={13} />确认后将使用既有 Camera → SLAM 计算定位，并交给确定性调度器。</p></section>;
}

function Frame({ asset, label }: { asset?: import("@/types/workbench").DemoAsset; label: string }) { return <div className="bg-white p-3"><p className="mb-2 text-xs font-semibold text-slate-600">{label}</p><DetectionFrame asset={asset} label={label} /></div>; }
