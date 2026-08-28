export interface AiLabStatus {
  requested_mode: "auto" | "mock" | "real";
  active_mode: "mock" | "real";
  mode_label: string;
  real_ready: boolean;
  reason: string;
  models: { yolo: string; qwen_vl: string };
  accepted_media: { images: string[]; videos: string[] };
  max_upload_mb: number;
}

export interface AiDetection {
  class_name: string;
  confidence: number;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  frame_index: number;
}

export interface AiLabMockCase { case: string; label: string; camera_id: string; }

export interface AiLabWorkflowInput {
  event_id: string; state: string; source: string; confidence: number; camera_id: string;
  location: { building: string; floor: string; zone: string; map_id: string; x: number; y: number };
  task_profile: AiLabResult["task_profile"];
}

export interface AiLabSchedulerPreview {
  status: "ASSIGNED" | "HUMAN_FALLBACK" | "NOT_READY";
  selected_robot_name?: string | null;
  reason: string;
}

export interface AiLabResult {
  schema_version: "ai-lab.v1";
  mode: "mock" | "real";
  mode_label: string;
  runtime_reason?: string;
  source: { filename: string; media_type: "image" | "video"; camera_id: string };
  pipeline: { yolo: string; vlm: string; keyframes: number };
  detections: AiDetection[];
  location: { camera_id: string; pixel: { u: number; v: number }; location: { building: string; floor: string; zone: string; map_id: string; x: number; y: number } } | null;
  perception: { need_clean: boolean; confidence: number; summary: string; raw: Record<string, unknown> };
  task_profile: { object_type: string; pollution_form: string; severity: string; estimated_area: number; surface: string; required_capabilities: string[]; priority: string; crowd_level: string };
  notes: string[];
  workflow_input: AiLabWorkflowInput | null;
  scheduler_preview: AiLabSchedulerPreview | null;
  cloud_review?: { status: "NOT_CONFIGURED" | "REAL" | "FAILED"; model: string; need_clean?: boolean; confidence?: number; summary?: string; business_class?: string; reason?: string };
}
