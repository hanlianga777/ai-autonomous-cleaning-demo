import type { AiLabResult } from "@/types/aiLab";
import type { MultiViewTrace } from "@/types/multiview";
import type { WorkflowEvent } from "@/types/workflow";

export type DemoAssetRole = "before" | "after" | "evidence";

export interface DetectionOverlay {
  label: string;
  confidence: number;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  source: "CONTROLLED_REPLAY";
}

export interface DemoAsset {
  camera_id: string;
  event_id: string;
  filename: string;
  label: string;
  role: DemoAssetRole;
  available: boolean;
  url: string | null;
  sha256: string | null;
  detection_overlays: DetectionOverlay[];
}

export interface DemoAssetManifest {
  event_id: string;
  title: string;
  subtitle: string;
  expected_robot: "ROBOT_A" | "ROBOT_B" | "ROBOT_C" | "HUMAN_FALLBACK";
  verification_mode: "AUTONOMOUS" | "HUMAN_REQUIRED";
  location_label: string;
  metadata: Record<string, string> | null;
  assets: DemoAsset[];
  missing_assets: string[];
}

export interface WorkbenchScenarioResult {
  asset_manifest: DemoAssetManifest;
  initial_ai_result: AiLabResult;
  workflow_event: WorkflowEvent & { multi_view_trace?: MultiViewTrace | null };
  multi_view: MultiViewTrace | null;
  upload_match?: { event_id: string; camera_id: string; filename: string; sha256: string };
}
