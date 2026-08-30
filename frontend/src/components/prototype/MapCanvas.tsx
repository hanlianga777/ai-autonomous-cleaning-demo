import { useEffect, useRef, useState, type ReactNode } from "react";
import { calculateContainedFrame, type ContainedFrame } from "./spatialProjection";

type MapCanvasProps = {
  children: ReactNode | ((frame: ContainedFrame) => ReactNode);
  className?: string;
  imageSrc: string;
  alt: string;
};

const FALLBACK_IMAGE_SIZE = { width: 1680, height: 948 };

/**
 * The only overlay coordinate system for the campus white model.
 *
 * It calculates the same `object-contain` rectangle as the image, then places
 * every overlay in that inner rectangle. Consumers receive percentage-space
 * coordinates (0..100) and must not position items against the outer panel.
 */
export function MapCanvas({ children, className = "", imageSrc, alt }: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageSize, setImageSize] = useState(FALLBACK_IMAGE_SIZE);
  const [frame, setFrame] = useState<ContainedFrame>({ left: 0, top: 0, width: 0, height: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const update = () => {
      const bounds = container.getBoundingClientRect();
      setFrame(calculateContainedFrame(bounds.width, bounds.height, imageSize.width, imageSize.height));
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(container);
    return () => observer.disconnect();
  }, [imageSize.height, imageSize.width]);

  const content = typeof children === "function" ? children(frame) : children;

  return (
    <div ref={containerRef} className={`relative min-h-0 overflow-hidden ${className}`}>
      <img
        src={imageSrc}
        alt={alt}
        draggable={false}
        className="pointer-events-none absolute object-contain select-none"
        style={{ left: frame.left, top: frame.top, width: frame.width, height: frame.height }}
        onLoad={(event) => {
          const image = event.currentTarget;
          if (image.naturalWidth && image.naturalHeight) {
            setImageSize({ width: image.naturalWidth, height: image.naturalHeight });
          }
        }}
      />
      {frame.width > 0 && frame.height > 0 && (
        <div
          className="absolute"
          style={{ left: frame.left, top: frame.top, width: frame.width, height: frame.height }}
          aria-label="园区地图内层坐标画布"
        >
          {content}
        </div>
      )}
    </div>
  );
}
