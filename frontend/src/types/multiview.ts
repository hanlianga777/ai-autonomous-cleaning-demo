export type MultiViewDecision = "CONFIRM" | "REJECT" | "HUMAN_REVIEW";

export interface MultiViewToolCall { tool: "Camera Coverage Tool" | "Frame Fetch Tool" | "VLM Tool"; camera_id?: string; frame_id?: string; selected_cameras?: MultiViewCamera[]; summary?: string; confidence?: number; }
export interface MultiViewCamera { camera_id: string; name: string; map_id: string; zone: string; selection_basis: string; }
export interface MultiViewEvidence { camera_id: string; frame_id: string; observation: string; confidence: number; }
export interface MultiViewTrace { triggered: boolean; initial_confidence: number; selected_cameras: MultiViewCamera[]; tool_calls: MultiViewToolCall[]; evidence: MultiViewEvidence[]; final_confidence: number; decision: MultiViewDecision | null; iteration_count: number; limits: { max_additional_cameras: number; max_agent_iterations: number }; }
export interface MultiViewScenarioEvent { event_id: string; state: string; assignment_decision: { selected_robot_name: string | null } | null; multi_view_trace: MultiViewTrace; }
