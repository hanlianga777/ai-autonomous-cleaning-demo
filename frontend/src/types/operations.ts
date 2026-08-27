import type { AiLabResult } from "@/types/aiLab";
import type { MultiViewTrace } from "@/types/multiview";
import type { SpatialMap } from "@/types/spatial";
import type { DemoAssetManifest } from "@/types/workbench";
import type { AssignmentDecision, WorkflowEvent, WorkflowTransition } from "@/types/workflow";

export interface FleetTelemetry {
  id: string;
  name: string;
  short_name: string;
  status: string;
  battery: number;
  location: string;
  role: string;
  activity: string;
  telemetry_mode: "DEMO_PLAYBACK";
  position: { map_id: string; x: number; y: number };
  route_progress?: string[];
  active_event_id?: string;
}

export interface OperationsWorkOrder {
  work_order_id: string;
  event_id: string;
  display_state: string;
  progress: number;
  event: WorkflowEvent;
  initial_ai_result: AiLabResult;
  multi_view: MultiViewTrace | null;
  asset_manifest: DemoAssetManifest;
  assignment_decision: AssignmentDecision;
  verification_pending: boolean;
  human_work_order: WorkflowEvent["human_fallback"];
  audit_transitions: WorkflowTransition[];
}

export interface OperationsSnapshot {
  schema_version: "operations.v1";
  telemetry_mode: "DEMO_PLAYBACK";
  message?: string;
  run_id?: string;
  elapsed_seconds?: number;
  fleet: FleetTelemetry[];
  active_work_order: OperationsWorkOrder | null;
  catalog: DemoAssetManifest[];
}

export interface OperationsMapProps {
  map: SpatialMap;
  fleet: FleetTelemetry[];
  activeWorkOrder: OperationsWorkOrder | null;
}
