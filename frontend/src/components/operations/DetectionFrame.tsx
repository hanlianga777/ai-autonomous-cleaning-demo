import type { DemoAsset } from "@/types/workbench";

export function DetectionFrame({ asset, label, compact = false }: { asset?: DemoAsset; label: string; compact?: boolean }) {
  return <div className={`relative overflow-hidden bg-slate-100 ${compact ? "aspect-[16/8]" : "aspect-[16/10]"}`}>
    {asset?.url ? <img src={asset.url} alt={label} className="h-full w-full object-cover" /> : <div className="flex h-full items-center justify-center text-xs text-slate-400">{label}不可用</div>}
    {(asset?.detection_overlays ?? []).map((overlay, index) => {
      const left = `${overlay.bbox.x1 * 100}%`;
      const top = `${overlay.bbox.y1 * 100}%`;
      const width = `${(overlay.bbox.x2 - overlay.bbox.x1) * 100}%`;
      const height = `${(overlay.bbox.y2 - overlay.bbox.y1) * 100}%`;
      return <div key={`${overlay.label}-${index}`} className="absolute border-2 border-rose-500 shadow-[0_0_0_1px_rgba(255,255,255,0.72)]" style={{ left, top, width, height }}>
        <span className="absolute -top-6 left-0 whitespace-nowrap bg-rose-600 px-1.5 py-1 text-[10px] font-semibold leading-none text-white shadow-sm">{overlay.label} · {(overlay.confidence * 100).toFixed(0)}%</span>
      </div>;
    })}
  </div>;
}
