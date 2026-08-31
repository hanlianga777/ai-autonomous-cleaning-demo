import { useMemo } from "react";
import { isEventPaused } from "./runtimeSession";
import { projectBackendRoute, routeWaypointAtDistance, type CanvasPoint, type NavigationPlan, type RouteSegment } from "./spatialProjection";
import type { ActiveEvent } from "./types";
import { useRoutePlayback } from "./useRoutePlayback";

export type NavigationPresentation = {
  selectedRobotId: string | null;
  plan: NavigationPlan | undefined;
  routePoints: CanvasPoint[];
  routeSegments: RouteSegment[];
  routeReady: boolean;
  isNavigating: boolean;
  paused: boolean;
  displayedTravel: number;
  robotPosition: CanvasPoint | null;
  progressLabel?: string;
  isElevatorPause: boolean;
};

type Transition = { state?: string; created_at?: string };

function navigationStartedAt(event: ActiveEvent | null): string | undefined {
  const transitions = event?.liveResult?.transitions;
  if (!Array.isArray(transitions)) return undefined;
  return [...(transitions as Transition[])].reverse().find((transition) => transition.state === "NAVIGATING")?.created_at;
}

function navigationPlan(event: ActiveEvent | null): NavigationPlan | undefined {
  const value = event?.liveResult?.navigation_plan ?? event?.liveResult?.visual_route_preview;
  return value && typeof value === "object" ? value as NavigationPlan : undefined;
}

/**
 * The workbench's sole animation clock. The map and event detail consume this
 * projection, while the backend remains the sole owner of durable stages.
 */
export function useNavigationPresentation(event: ActiveEvent | null): NavigationPresentation {
  const selectedRobotId = typeof (event?.liveResult?.assignment_decision as { selected_robot_id?: unknown } | undefined)?.selected_robot_id === "string"
    ? (event?.liveResult?.assignment_decision as { selected_robot_id: string }).selected_robot_id
    : null;
  const plan = navigationPlan(event);
  const routePoints = useMemo(() => projectBackendRoute(plan, null, null), [plan]);
  const routeSegments = useMemo(() => {
    const routeNodeIds = new Set(routePoints.map((point) => point.nodeId));
    if (!routeNodeIds.size || !Array.isArray(plan?.segments)) return [];
    return (plan.segments as RouteSegment[]).filter((segment) => !segment.from || !segment.to || (routeNodeIds.has(segment.from) && routeNodeIds.has(segment.to)));
  }, [plan, routePoints]);
  const isNavigating = event?.backendState === "NAVIGATING";
  const paused = isEventPaused(event);
  const playback = useRoutePlayback({
    active: Boolean(isNavigating && selectedRobotId && routePoints.length > 1),
    paused,
    pauseStartedAt: typeof event?.liveResult?.operations_pause_started_at === "string" ? event.liveResult.operations_pause_started_at : undefined,
    pausedMs: typeof event?.liveResult?.operations_paused_ms === "number" ? event.liveResult.operations_paused_ms : 0,
    navigationStartedAt: navigationStartedAt(event),
    points: routePoints,
    segments: routeSegments,
  });
  const routeReady = routePoints.length > 1;
  const displayedTravel = isNavigating ? playback.travelledDistance : playback.totalDistance;
  const waypoint = routeWaypointAtDistance(routePoints, displayedTravel);
  const progressLabel = isNavigating && routeReady
    ? (playback.isElevatorPause ? "正在乘坐 B 栋电梯前往 B 栋 2F" : waypoint?.progressLabel ?? waypoint?.label)
    : undefined;
  const robotPosition = !routeReady
    ? null
    : isNavigating
      ? playback.point ?? routePoints[0]
      : event?.backendState === "ASSIGNED" ? routePoints[0] : routePoints.at(-1) ?? null;
  return {
    selectedRobotId,
    plan,
    routePoints,
    routeSegments,
    routeReady,
    isNavigating,
    paused,
    displayedTravel,
    robotPosition,
    progressLabel,
    isElevatorPause: playback.isElevatorPause,
  };
}
