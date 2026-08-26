import type { AiLabResult } from "@/types/aiLab";
import type { DemoAssetManifest, WorkbenchScenarioResult } from "@/types/workbench";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) { const body = await response.json().catch(() => ({ detail: "工作台服务暂不可用" })); throw new Error(body.detail ?? "工作台服务暂不可用"); }
  return response.json() as Promise<T>;
}

export const fetchScenario02Assets = () => request<DemoAssetManifest>("/workbench/scenario02/assets");
export const runScenario02Workbench = () => request<WorkbenchScenarioResult>("/workbench/scenario02/run", { method: "POST" });
export async function analyzeWorkbenchUpload(file: File, cameraId = "CAM-A1-01"): Promise<AiLabResult> { const form = new FormData(); form.append("file", file); return request<AiLabResult>(`/ai-lab/analyze?camera_id=${encodeURIComponent(cameraId)}`, { method: "POST", body: form }); }
