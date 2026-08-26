export interface WorkflowTransition { id: number; state: string; detail: Record<string, unknown>; created_at: string; }
export interface AssignmentCandidate { robot_id: string; robot_name: string; eligible: boolean; reject_reasons: string[]; score_components: Record<string, number>; final_score: number | null; route: { display_path: string[]; total_cost: number } | null; }
export interface AssignmentDecision { status: "ASSIGNED" | "HUMAN_FALLBACK"; selected_robot_id: string | null; selected_robot_name: string | null; reason: string; weights: Record<string, number>; candidates: AssignmentCandidate[]; }
export interface WorkflowEvent {
  event_id: string; state: string; template: string; confidence: number; camera_id: string; location: { building:string; floor:string; zone:string; map_id:string; x:number; y:number };
  task_profile: { object_type:string; pollution_form:string; severity:string; estimated_area:number; surface:string; required_capabilities:string[]; priority:string; crowd_level:string; };
  assignment_decision: AssignmentDecision | null; navigation_plan: { display_path: string[]; total_cost:number } | null; verification: { result:string; confidence:number; reason:string } | null; human_fallback: { work_order_id:string; status:string; reason:string } | null; transitions: WorkflowTransition[];
}
export interface EventTemplate { template: string; label: string; }
