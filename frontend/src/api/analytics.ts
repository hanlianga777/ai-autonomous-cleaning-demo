import type { AnalyticsOverview, OptimizationResult } from "@/types/analytics";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, method = "GET"): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { method });
  if (!response.ok) { const body = await response.json().catch(() => ({ detail: "Analytics API request failed" })); throw new Error(body.detail ?? "Analytics API request failed"); }
  return response.json() as Promise<T>;
}

export const fetchAnalyticsOverview = () => request<AnalyticsOverview>("/analytics/overview");
export const generateOptimization = () => request<OptimizationResult>("/optimization/recommend", "POST");
