import type { DashboardData } from "@/types/dashboard";

// Vite proxies this path locally, avoiding origin-specific CORS failures.
// A deployed environment can supply an absolute endpoint with VITE_API_BASE_URL.
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const fallbackDashboard: DashboardData = {
  park: {
    park_id: "east-harbor-campus",
    name: "东港智慧园区",
    status: "operational",
    timezone: "Asia/Shanghai",
    summary: { buildings: 2, managed_floors: 5, outdoor_zones: 3, robot_fleet: 3 },
    areas: [
      { id: "OUTDOOR", name: "园区室外", type: "outdoor", zones: 3 },
      { id: "A", name: "A 栋", type: "building", floors: ["B1", "1F", "2F"] },
      { id: "B", name: "B 栋", type: "building", floors: ["1F", "2F"] },
    ],
  },
  robots: [
    { id: "robot-a", code: "R-A01", name: "Outdoor Sweeper", short_name: "Robot A", model: "OS-200", role: "室外道路清扫", status: "idle", battery: 88, location: "园区道路 · 东入口", zone: "Outdoor East Road", building: "OUTDOOR", floor: null, last_seen: "离线 Mock", capabilities: ["室外", "干垃圾", "道路清扫"] },
    { id: "robot-b", code: "R-B02", name: "Heavy Scrubber", short_name: "Robot B", model: "HS-450", role: "重度地面清洁", status: "charging", battery: 64, location: "A 栋 1F · 设备间", zone: "A1 Service Bay", building: "A", floor: "1F", last_seen: "离线 Mock", capabilities: ["湿洗", "强吸力", "刷洗"] },
    { id: "robot-c", code: "R-C03", name: "Indoor Light Cleaner", short_name: "Robot C", model: "IL-120", role: "室内日常清洁", status: "idle", battery: 91, location: "B 栋 1F · 大堂西侧", zone: "B1 West Lobby", building: "B", floor: "1F", last_seen: "离线 Mock", capabilities: ["干垃圾", "地毯", "低噪声"] },
  ],
  fleet: { available: 2, charging: 1, average_battery: 81 },
  system: { mode: "DEMO MOCK MODE", phase: "Phase 1 · Foundation" },
};

export async function fetchDashboard(): Promise<DashboardData> {
  const response = await fetch(`${apiBaseUrl}/dashboard`);
  if (!response.ok) throw new Error("无法获取园区 Mock 数据");
  return response.json() as Promise<DashboardData>;
}
