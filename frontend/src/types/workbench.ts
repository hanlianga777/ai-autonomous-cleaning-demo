import type { AiLabResult } from "@/types/aiLab";
import type { MultiViewTrace } from "@/types/multiview";
import type { WorkflowEvent } from "@/types/workflow";

export interface DemoAsset { camera_id: string; event_id: string; filename: string; label: string; available: boolean; url: string | null; }
export interface DemoAssetManifest { event_id: string; metadata: { event_id: string; camera_id: string; building: string; floor: string; zone: string; view_role: string; object_type: string; expected_robot: string } | null; assets: DemoAsset[]; missing_assets: string[]; }
export interface WorkbenchScenarioResult { asset_manifest: DemoAssetManifest; initial_ai_result: AiLabResult; workflow_event: WorkflowEvent & { multi_view_trace: MultiViewTrace }; multi_view: MultiViewTrace; }
