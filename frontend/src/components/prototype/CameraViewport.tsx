import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { Camera } from "./types";

/**
 * The source demo frames are 1448 × 1086 (4:3). The viewport may be 16:9,
 * but the image and its controlled overlays must share the same 4:3 layer.
 * This keeps bbox coordinates stable even when the viewport has letterboxes.
 */
export function CameraViewport({ camera, showDetections = false, compact = false, zoomable = true, fill = false }: { camera: Camera; showDetections?: boolean; compact?: boolean; zoomable?: boolean; fill?: boolean }) {
  const [zoomed, setZoomed] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const element = container.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      const width = Math.min(entry.contentRect.width, entry.contentRect.height * 4 / 3);
      setSize({ width, height: width * 3 / 4 });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, [fill, compact]);
  useEffect(() => { const close = (event: KeyboardEvent) => event.key === "Escape" && setZoomed(false); window.addEventListener("keydown", close); return () => window.removeEventListener("keydown", close); }, []);
  const frame = <div ref={container} className={`relative flex w-full items-center justify-center overflow-hidden bg-slate-950 ${fill ? "h-full" : compact ? "aspect-[4/3]" : "aspect-video"}`}>
    <div data-testid="camera-image-plane" className="relative shrink-0" style={size}>
      <img src={camera.image} alt={`${camera.id} ${camera.location}`} className="absolute inset-0 h-full w-full object-contain" />
      {showDetections && camera.overlay?.map((item, index) => {
        const [x1, y1, x2, y2] = item.bbox;
        const paddingX = 0; const paddingY = 0;
        return <div key={`${item.label}-${index}`} className="absolute border-[1.5px] border-rose-500" style={{ left: `${Math.max(0, x1 - paddingX) * 100}%`, top: `${Math.max(0, y1 - paddingY) * 100}%`, width: `${Math.min(1, x2 + paddingX) * 100 - Math.max(0, x1 - paddingX) * 100}%`, height: `${Math.min(1, y2 + paddingY) * 100 - Math.max(0, y1 - paddingY) * 100}%` }}>
          <span className="absolute -top-5 left-0 whitespace-nowrap bg-rose-600 px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white">{item.label} · {Math.round(item.confidence * 100)}%</span>
        </div>;
      })}
    </div>
  </div>;
  if (!zoomable) return frame;
  return <><button type="button" onClick={() => setZoomed(true)} aria-label={`放大查看 ${camera.id}`} className={`block w-full text-left ${fill ? "h-full" : ""}`}>{frame}</button>{zoomed && <div role="dialog" aria-modal="true" aria-label={`${camera.id} 证据放大`} onClick={() => setZoomed(false)} className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/85 p-6"><div onClick={(event) => event.stopPropagation()} className="relative h-[80vh] w-full max-w-6xl"><button type="button" onClick={() => setZoomed(false)} className="absolute -right-1 -top-10 flex h-8 w-8 items-center justify-center border border-white/50 bg-slate-900 text-white" aria-label="关闭放大图"><X size={16} /></button><CameraViewport camera={camera} showDetections={showDetections} zoomable={false} fill /><p className="mt-2 text-center text-xs text-white/75">{camera.id} · {camera.location}</p></div></div>}</>;
}
