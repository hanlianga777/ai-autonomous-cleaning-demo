import type { Camera } from "./types";

/**
 * The source demo frames are 1448 × 1086 (4:3). The viewport may be 16:9,
 * but the image and its controlled overlays must share the same 4:3 layer.
 * This keeps bbox coordinates stable even when the viewport has letterboxes.
 */
export function CameraViewport({ camera, showDetections = false, compact = false }: { camera: Camera; showDetections?: boolean; compact?: boolean }) {
  return <div className={`relative flex w-full items-center justify-center overflow-hidden bg-slate-950 ${compact ? "aspect-[4/3]" : "aspect-video"}`}>
    <div className="relative h-full aspect-[4/3] max-w-full">
      <img src={camera.image} alt={`${camera.id} ${camera.location}`} className="absolute inset-0 h-full w-full object-contain" />
      {showDetections && camera.overlay?.map((item, index) => {
        const [x1, y1, x2, y2] = item.bbox;
        return <div key={`${item.label}-${index}`} className="absolute border-2 border-rose-500 shadow-[0_0_0_1px_rgba(255,255,255,0.82)]" style={{ left: `${x1 * 100}%`, top: `${y1 * 100}%`, width: `${(x2 - x1) * 100}%`, height: `${(y2 - y1) * 100}%` }}>
          <span className="absolute -top-5 left-0 whitespace-nowrap bg-rose-600 px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white">{item.label} {Math.round(item.confidence * 100)}%</span>
        </div>;
      })}
    </div>
  </div>;
}
