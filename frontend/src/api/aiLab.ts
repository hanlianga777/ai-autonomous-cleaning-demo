import type { AiLabMockCase, AiLabResult, AiLabStatus } from "@/types/aiLab";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function unpack<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "AI Lab request failed" }));
    throw new Error(body.detail ?? "AI Lab request failed");
  }
  return response.json() as Promise<T>;
}

export const fetchAiLabStatus = () => fetch(`${apiBaseUrl}/ai-lab/status`).then(unpack<AiLabStatus>);
export const fetchAiLabMockCases = () => fetch(`${apiBaseUrl}/ai-lab/mock-cases`).then(unpack<AiLabMockCase[]>);
export const runAiLabMockCase = (mockCase: string) => fetch(`${apiBaseUrl}/ai-lab/mock-cases/${encodeURIComponent(mockCase)}`, { method: "POST" }).then(unpack<AiLabResult>);

export function analyzeAiUpload(file: File, cameraId: string): Promise<AiLabResult> {
  const body = new FormData();
  body.append("file", file);
  return fetch(`${apiBaseUrl}/ai-lab/analyze?camera_id=${encodeURIComponent(cameraId)}`, { method: "POST", body }).then(unpack<AiLabResult>);
}
