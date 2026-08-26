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

export interface AiLabResult {
  mode: "mock" | "real";
  mode_label: string;
  runtime_reason?: string;
  source: { filename: string; media_type: "image" | "video"; camera_id: string };
  pipeline: { yolo: string; vlm: string; keyframes: number };
  detections: AiDetection[];
  location: { camera_id: string; pixel: { u: number; v: number }; location: { building: string; floor: string; zone: string; x: number; y: number } } | null;
  vlm: { needs_cleaning: boolean; confidence: number; summary: string; raw: Record<string, unknown> };
  task_profile: { object_type: string; pollution_form: string; severity: string; estimated_area: number; surface: string; required_capabilities: string[]; priority: string; crowd_level: string };
  notes: string[];
}
