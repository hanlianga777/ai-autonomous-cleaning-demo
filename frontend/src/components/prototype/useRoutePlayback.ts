import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { timestampMs } from "./eventViewModel";
import { buildMotionPlan, sampleRouteMotion, type CanvasPoint, type RouteSegment } from "./spatialProjection";

type RoutePlaybackOptions = {
  active: boolean;
  navigationStartedAt?: string;
  points: CanvasPoint[];
  segments?: RouteSegment[];
  onComplete?: () => void;
};

type RoutePlayback = {
  point: CanvasPoint | null;
  travelledDistance: number;
  totalDistance: number;
  isElevatorPause: boolean;
  complete: boolean;
};

/**
 * A requestAnimationFrame-only visual projection of the backend route.
 * This is explicitly not fleet telemetry: its start is the persisted
 * NAVIGATING transition timestamp, so a refresh reconstructs visual progress.
 */
export function useRoutePlayback({ active, navigationStartedAt, points, segments, onComplete }: RoutePlaybackOptions): RoutePlayback {
  // Upstream event decoding may reconstruct equivalent arrays while a view is
  // rendering. Key the motion plan by its actual route values instead of array
  // identity so a local playback setState cannot restart the layout effect.
  const pointsKey = points.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)},${point.nodeId ?? ""}`).join("|");
  const segmentsKey = (segments ?? []).map((segment) => `${segment.from ?? ""}:${segment.to ?? ""}:${segment.type ?? ""}`).join("|");
  const plan = useMemo(() => buildMotionPlan(points, segments), [pointsKey, segmentsKey]);
  const routeKey = `${navigationStartedAt ?? ""}:${pointsKey}:${plan.totalDurationMs}`;
  const completeKey = useRef<string | null>(null);
  const onCompleteRef = useRef(onComplete);
  const [sample, setSample] = useState(() => sampleRouteMotion(plan, 0));

  useEffect(() => { onCompleteRef.current = onComplete; }, [onComplete]);

  // Layout timing prevents a start-position flash when the workbench remounts
  // after Event Center: progress is reconstructed from the persisted timestamp
  // before this MapCanvas is painted again.
  useLayoutEffect(() => {
    if (!active || !plan.points.length) {
      setSample(sampleRouteMotion(plan, plan.totalDurationMs));
      return;
    }
    // SQLite timestamps are UTC but do not carry an offset ("YYYY-MM-DD HH:mm:ss").
    // Date.parse would otherwise treat one as browser-local time and complete an
    // eight-hour-old-looking route immediately in an Asia/Shanghai browser.
    const parsedStart = timestampMs(navigationStartedAt);
    const startedAt = Number.isFinite(parsedStart) ? parsedStart : Date.now();
    let frameId = 0;
    const render = () => {
      const next = sampleRouteMotion(plan, Date.now() - startedAt);
      setSample(next);
      if (next.complete) {
        if (completeKey.current !== routeKey) {
          completeKey.current = routeKey;
          onCompleteRef.current?.();
        }
        return;
      }
      frameId = requestAnimationFrame(render);
    };
    frameId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(frameId);
  }, [active, navigationStartedAt, plan, routeKey]);

  return {
    point: sample.position,
    travelledDistance: sample.travelledDistance,
    totalDistance: plan.totalDistance,
    isElevatorPause: sample.isElevatorPause,
    complete: sample.complete,
  };
}
