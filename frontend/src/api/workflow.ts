import type { AssignmentDecision, EventTemplate, WorkflowEvent } from "@/types/workflow";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, method = "GET"): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { method });
  if (!response.ok) { const body = await response.json().catch(() => ({ detail: "Workflow API request failed" })); throw new Error(body.detail ?? "Workflow API request failed"); }
  return response.json() as Promise<T>;
}

export const fetchEventTemplates = () => request<EventTemplate[]>("/events/templates");
export const createMockEvent = (template: string) => request<WorkflowEvent>(`/events/mock/${encodeURIComponent(template)}`, "POST");
export const runWorkflow = (eventId: string) => request<WorkflowEvent>(`/events/${encodeURIComponent(eventId)}/run`, "POST");
export const fetchWorkflowEvent = (eventId: string) => request<WorkflowEvent>(`/events/${encodeURIComponent(eventId)}`);
export const evaluateScheduler = (eventId: string) => request<AssignmentDecision>(`/scheduler/evaluate?event_id=${encodeURIComponent(eventId)}`, "POST");
