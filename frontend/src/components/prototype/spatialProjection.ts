/**
 * Pure projection and motion helpers for the P1-B MapCanvas.
 *
 * The backend remains the source of route order, fleet positions and targets.
 * These functions only put those facts on the one campus white-model plane;
 * they never infer a route from a demo id or mutate runtime state.
 */

export type CanvasPoint = { x: number; y: number; label?: string; progressLabel?: string; nodeId?: string };

export type FleetPosition = {
  id: string;
  map_id: string;
  coordinates: { x: number; y: number };
};

export type EventTarget = { map_id: string; x: number; y: number };

export type AnalyticsHeatmapPoint = EventTarget & { zone_id?: string };

export type RouteSegment = { from?: string; to?: string; type?: string; cost?: number };

export type NavigationPlan = {
  node_path?: string[];
  display_anchors?: string[];
  visual_route_version?: number;
  visual_path?: CanvasPoint[];
  visual_style?: { route?: string; opacity?: number; stroke_width?: number; dasharray?: string };
  segments?: RouteSegment[];
  total_cost?: number;
};

export type MotionPlan = {
  points: CanvasPoint[];
  totalDistance: number;
  travelDurationMs: number;
  elevatorPause: { atDistance: number; durationMs: number } | null;
  totalDurationMs: number;
};

export type MotionSample = {
  position: CanvasPoint | null;
  travelledDistance: number;
  complete: boolean;
  isElevatorPause: boolean;
};

export type ContainedFrame = { left: number; top: number; width: number; height: number };

/** Persisted pause clocks make refresh and repeated pause/resume deterministic. */
export function navigationElapsedMs(startedAt: number, now: number, paused: boolean, pauseStartedAt: number, pausedMs: number): number {
  if (!Number.isFinite(startedAt)) return 0;
  const end = paused ? (Number.isFinite(pauseStartedAt) ? pauseStartedAt : startedAt) : now;
  const excluded = Number.isFinite(pausedMs) ? Math.max(0, pausedMs) : 0;
  return Math.max(0, end - startedAt - excluded);
}

// These anchors are the campus white-model's visual references. Their values
// are percentages *inside the image plane*, never percentages of a parent UI
// card. Backend map/node data selects which anchor is used.
export const CAMPUS_TOPOLOGY_ANCHORS: Record<string, CanvasPoint> = {
  OUTDOOR: { x: 50, y: 78, label: "园区道路", nodeId: "OUTDOOR" },
  A_B1: { x: 33, y: 66, label: "A栋 B1", nodeId: "A_B1" },
  A_1F: { x: 35, y: 52, label: "A栋 1F", nodeId: "A_1F" },
  A_2F: { x: 35, y: 28, label: "A栋 2F", nodeId: "A_2F" },
  B_1F: { x: 74, y: 57, label: "B栋 1F", nodeId: "B_1F" },
  B_2F: { x: 74, y: 34, label: "B栋 2F", nodeId: "B_2F" },
  A_ELEVATOR_1F: { x: 40, y: 49, label: "A栋电梯", nodeId: "A_ELEVATOR_1F" },
  A_ELEVATOR_2F: { x: 39, y: 31, label: "A栋电梯", nodeId: "A_ELEVATOR_2F" },
  B_ELEVATOR_1F: { x: 76, y: 52, label: "B栋电梯", nodeId: "B_ELEVATOR_1F" },
  B_ELEVATOR_2F: { x: 76, y: 37, label: "B栋电梯", nodeId: "B_ELEVATOR_2F" },
  SKYBRIDGE_B: { x: 61, y: 29, label: "连廊 B 端", nodeId: "SKYBRIDGE_B" },
  SKYBRIDGE_A: { x: 50, y: 29, label: "连廊 A 端", nodeId: "SKYBRIDGE_A" },
};

const FALLBACK_ANCHOR: CanvasPoint = { x: 50, y: 50, label: "园区位置" };

/** Visible road/building planes in the white-model image. The runtime map ID
 * and local coordinates remain authoritative; this only makes their movement
 * legible on the shared campus overview. */
const CAMPUS_MAP_FRAMES: Record<string, { left: number; top: number; width: number; height: number; reverseX?: boolean }> = {
  OUTDOOR: { left: 7, top: 69.5, width: 86, height: 17, reverseX: true },
  A_1F: { left: 21.5, top: 43, width: 27, height: 18 },
  A_2F: { left: 21.5, top: 19.5, width: 27, height: 17 },
  B_1F: { left: 60.5, top: 48.5, width: 27, height: 17 },
  B_2F: { left: 60.5, top: 25.5, width: 27, height: 17 },
};

// These five positions are calibrated to the visible building/road surfaces
// in campus-white-model.png.  They are a presentation transform for the
// canonical backend zones (not a second location source): every key retains
// the exact map_id + x/y + zone_id returned by Analytics.
export const ANALYTICS_ZONE_PROJECTIONS: Record<string, CanvasPoint> = {
  "a1-east-entrance": { x: 40.0, y: 57.5, label: "A 栋 1F · 东入口" },
  "a1-main-lobby": { x: 31.5, y: 48.5, label: "A 栋 1F · 主大堂" },
  "b1-west-lobby": { x: 66.5, y: 58.5, label: "B 栋 1F · 西侧大堂" },
  "outdoor-east-road": { x: 87.0, y: 76.0, label: "园区室外 · 东入口道路" },
  "a2-corridor": { x: 29.0, y: 30.0, label: "A 栋 2F · 北侧走廊" },
};

function clamp(value: number, minimum = 2, maximum = 98): number {
  return Math.min(maximum, Math.max(minimum, value));
}

function samePoint(left: CanvasPoint, right: CanvasPoint): boolean {
  return Math.abs(left.x - right.x) < 0.01 && Math.abs(left.y - right.y) < 0.01;
}

export function calculateContainedFrame(
  containerWidth: number,
  containerHeight: number,
  assetWidth: number,
  assetHeight: number,
): ContainedFrame {
  if (containerWidth <= 0 || containerHeight <= 0 || assetWidth <= 0 || assetHeight <= 0) {
    return { left: 0, top: 0, width: 0, height: 0 };
  }
  const scale = Math.min(containerWidth / assetWidth, containerHeight / assetHeight);
  const width = assetWidth * scale;
  const height = assetHeight * scale;
  return { left: (containerWidth - width) / 2, top: (containerHeight - height) / 2, width, height };
}

/** Project a Phase 2 local map coordinate onto its campus white-model anchor. */
export function projectMapCoordinate(mapId: string, x: number, y: number): CanvasPoint {
  const frame = CAMPUS_MAP_FRAMES[mapId];
  if (frame) {
    const normalizedX = Math.min(1, Math.max(0, x / 100));
    const normalizedY = Math.min(1, Math.max(0, y / 60));
    return {
      x: clamp(frame.left + (frame.reverseX ? 1 - normalizedX : normalizedX) * frame.width),
      y: clamp(frame.top + normalizedY * frame.height),
      label: CAMPUS_TOPOLOGY_ANCHORS[mapId]?.label ?? FALLBACK_ANCHOR.label,
      nodeId: CAMPUS_TOPOLOGY_ANCHORS[mapId]?.nodeId,
    };
  }
  const anchor = CAMPUS_TOPOLOGY_ANCHORS[mapId] ?? FALLBACK_ANCHOR;
  // The current six Phase 2 maps are all explicitly 100 × 60 metres in
  // backend/spatial/spatial_data.py. This remains an overview projection, not
  // a calibration transform or a replacement for the backend SLAM geometry.
  return {
    x: clamp(anchor.x + (x - 50) * 0.085),
    y: clamp(anchor.y + (y - 30) * 0.085),
    label: anchor.label,
    nodeId: anchor.nodeId,
  };
}

/**
 * Project a factual Analytics aggregation onto its matching white-model area.
 * Canonical zones use the verified calibration above; other legitimate
 * runtime rows retain the general map projection rather than being invented
 * or silently dropped from the density layer.
 */
export function projectAnalyticsHeatmapPoint(point: AnalyticsHeatmapPoint): CanvasPoint {
  const calibrated = point.zone_id ? ANALYTICS_ZONE_PROJECTIONS[point.zone_id] : undefined;
  if (calibrated) return { ...calibrated };
  return projectMapCoordinate(point.map_id, point.x, point.y);
}

export function projectTopologyNode(nodeId: string): CanvasPoint | null {
  const anchor = CAMPUS_TOPOLOGY_ANCHORS[nodeId];
  return anchor ? { ...anchor } : null;
}

export function compactRoutePoints(points: CanvasPoint[]): CanvasPoint[] {
  return points.filter((point, index) => index === 0 || !samePoint(point, points[index - 1]));
}

/**
 * The overview route is a versioned, persisted backend snapshot. The Dijkstra
 * path remains operational metadata and must never be converted into a second
 * display route, because that would visually invent branches.
 */
export function projectBackendRoute(
  plan: NavigationPlan | null | undefined,
  _fleetRobot: FleetPosition | null | undefined,
  _target: EventTarget | null | undefined,
): CanvasPoint[] {
  const visualPath = plan?.visual_path;
  if (plan?.visual_route_version === 5 && Array.isArray(visualPath) && visualPath.length > 1 && visualPath.every((point) => Number.isFinite(point?.x) && Number.isFinite(point?.y))) {
    return compactRoutePoints(visualPath.map((point) => {
      const { node_id, progress_label, ...canvasPoint } = point as CanvasPoint & { node_id?: string; progress_label?: string };
      const progressLabel = canvasPoint.progressLabel ?? progress_label;
      return { ...canvasPoint, x: clamp(canvasPoint.x), y: clamp(canvasPoint.y), nodeId: canvasPoint.nodeId ?? node_id, ...(progressLabel ? { progressLabel } : {}) };
    }));
  }
  return [];
}

export function distanceBetween(start: CanvasPoint, end: CanvasPoint): number {
  return Math.hypot(end.x - start.x, end.y - start.y);
}

export function routeLength(points: CanvasPoint[]): number {
  return points.slice(1).reduce((total, point, index) => total + distanceBetween(points[index], point), 0);
}

export function pointAtRouteDistance(points: CanvasPoint[], distance: number): CanvasPoint | null {
  if (!points.length) return null;
  if (points.length === 1) return points[0];
  const totalDistance = routeLength(points);
  if (distance >= totalDistance) return points[points.length - 1];
  let remaining = Math.max(0, distance);
  for (let index = 1; index < points.length; index += 1) {
    const start = points[index - 1];
    const end = points[index];
    const segmentLength = distanceBetween(start, end);
    if (Math.abs(remaining - segmentLength) < 0.0001) return end;
    if (remaining <= segmentLength || index === points.length - 1) {
      const fraction = segmentLength ? Math.min(1, remaining / segmentLength) : 1;
      return { x: start.x + (end.x - start.x) * fraction, y: start.y + (end.y - start.y) * fraction };
    }
    remaining -= segmentLength;
  }
  return points[points.length - 1];
}

/** The last persisted route node reached at a display distance. */
export function routeWaypointAtDistance(points: CanvasPoint[], distance: number): CanvasPoint | null {
  if (!points.length) return null;
  let covered = 0;
  for (let index = 1; index < points.length; index += 1) {
    covered += distanceBetween(points[index - 1], points[index]);
    if (distance + 0.0001 < covered) return points[index - 1];
  }
  return points[points.length - 1];
}

function distanceToNode(points: CanvasPoint[], nodeIndex: number): number {
  return routeLength(points.slice(0, nodeIndex + 1));
}

export function buildMotionPlan(points: CanvasPoint[], segments: RouteSegment[] = []): MotionPlan {
  const totalDistance = routeLength(points);
  const elevator = segments.find((segment) => segment.type === "elevator");
  // Pause at the actual entry node (`segment.from`), not the exit node. Node
  // IDs survive route compaction, unlike positional segment indexes.
  const pauseNodeIndex = elevator?.from ? points.findIndex((point) => point.nodeId === elevator.from) : -1;
  const elevatorPause = pauseNodeIndex > 0
    ? { atDistance: distanceToNode(points, pauseNodeIndex), durationMs: 1000 }
    : null;
  // This duration is a labelled PoC visualisation pacing, derived from route
  // length—not device telemetry or a scheduler estimate.
  const travelDurationMs = totalDistance ? Math.max(6000, Math.round(totalDistance * 220)) : 0;
  return {
    points,
    totalDistance,
    travelDurationMs,
    elevatorPause,
    totalDurationMs: travelDurationMs + (elevatorPause?.durationMs ?? 0),
  };
}

export function sampleRouteMotion(plan: MotionPlan, elapsedMs: number): MotionSample {
  if (!plan.points.length) return { position: null, travelledDistance: 0, complete: true, isElevatorPause: false };
  if (!plan.totalDistance || !plan.travelDurationMs) {
    return { position: plan.points[plan.points.length - 1], travelledDistance: plan.totalDistance, complete: true, isElevatorPause: false };
  }
  const elapsed = Math.max(0, elapsedMs);
  const pause = plan.elevatorPause;
  const beforePauseTravel = pause ? plan.travelDurationMs * (pause.atDistance / plan.totalDistance) : Infinity;
  if (pause && elapsed >= beforePauseTravel && elapsed < beforePauseTravel + pause.durationMs) {
    return {
      position: pointAtRouteDistance(plan.points, pause.atDistance),
      travelledDistance: pause.atDistance,
      complete: false,
      isElevatorPause: true,
    };
  }
  const adjustedElapsed = pause && elapsed >= beforePauseTravel + pause.durationMs ? elapsed - pause.durationMs : elapsed;
  const travelledDistance = Math.min(plan.totalDistance, plan.totalDistance * (adjustedElapsed / plan.travelDurationMs));
  return {
    position: pointAtRouteDistance(plan.points, travelledDistance),
    travelledDistance,
    complete: elapsed >= plan.totalDurationMs,
    isElevatorPause: false,
  };
}

export function svgPath(points: CanvasPoint[], distance?: number): string {
  let displayed = points;
  if (distance !== undefined) {
    displayed = [];
    let remaining = Math.max(0, distance);
    if (points.length) displayed.push(points[0]);
    for (let index = 1; index < points.length; index += 1) {
      const start = points[index - 1];
      const end = points[index];
      const segmentLength = distanceBetween(start, end);
      if (remaining >= segmentLength) {
        displayed.push(end);
        remaining -= segmentLength;
        continue;
      }
      const partial = pointAtRouteDistance([start, end], remaining);
      if (partial && !samePoint(partial, start)) displayed.push(partial);
      break;
    }
  }
  return displayed.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" ");
}
