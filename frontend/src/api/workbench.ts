import type { DemoAssetManifest, WorkbenchScenarioResult } from "@/types/workbench";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "工作台服务暂不可用" }));
    throw new Error(body.detail ?? "工作台服务暂不可用");
  }
  return response.json() as Promise<T>;
}

export const fetchWorkbenchScenarios = () => request<DemoAssetManifest[]>("/workbench/scenarios");
export const runWorkbenchEvent = (eventId: string) => request<WorkbenchScenarioResult>(`/workbench/events/${encodeURIComponent(eventId)}/run`, { method: "POST" });

export async function runWorkbenchUpload(file: File): Promise<WorkbenchScenarioResult> {
  const form = new FormData();
  form.append("file", file);
  return request<WorkbenchScenarioResult>("/workbench/upload", { method: "POST", body: form });
}

// Compatibility exports for pre-existing Scenario 02 API consumers.
export const fetchScenario02Assets = () => request<DemoAssetManifest>("/workbench/scenario02/assets");
export const runScenario02Workbench = () => request<WorkbenchScenarioResult>("/workbench/scenario02/run", { method: "POST" });
