import type { MultiViewScenarioEvent } from "@/types/multiview";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

export async function runMultiViewScenario02(): Promise<MultiViewScenarioEvent> {
  const response = await fetch(`${apiBaseUrl}/multiview/scenario02/run`, { method: "POST" });
  if (!response.ok) { const body = await response.json().catch(() => ({ detail: "Multi-view request failed" })); throw new Error(body.detail ?? "Multi-view request failed"); }
  return response.json() as Promise<MultiViewScenarioEvent>;
}
