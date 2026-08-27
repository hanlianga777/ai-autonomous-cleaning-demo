import type { OperationsSnapshot } from "@/types/operations";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "运营指挥服务暂不可用" }));
    throw new Error(body.detail ?? "运营指挥服务暂不可用");
  }
  return response.json() as Promise<T>;
}

export const fetchOperationsSnapshot = (runId?: string) => request<OperationsSnapshot>(`/operations/snapshot${runId ? `?run_id=${encodeURIComponent(runId)}` : ""}`);
export const startOperationsRun = (eventId: string) => request<OperationsSnapshot>(`/operations/runs/${encodeURIComponent(eventId)}`, { method: "POST" });

export async function startOperationsUpload(file: File): Promise<OperationsSnapshot> {
  const form = new FormData();
  form.append("file", file);
  return request<OperationsSnapshot>("/operations/upload", { method: "POST", body: form });
}
