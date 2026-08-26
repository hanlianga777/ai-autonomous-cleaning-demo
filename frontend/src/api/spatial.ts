import type { MappingResult, Route, SpatialOverview } from "@/types/spatial";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Spatial API request failed" }));
    throw new Error(body.detail ?? "Spatial API request failed");
  }
  return response.json() as Promise<T>;
}

export const fetchSpatialOverview = () => request<SpatialOverview>("/spatial/overview");
export const fetchRoute = (start: string, target: string) => request<Route>(`/spatial/routes?start=${encodeURIComponent(start)}&target=${encodeURIComponent(target)}`);
export const fetchMapping = (cameraId: string, u: number, v: number) => request<MappingResult>(`/spatial/cameras/${encodeURIComponent(cameraId)}/map?u=${u}&v=${v}`);
