export type RobotStatus = "idle" | "charging";

export interface Robot {
  id: string;
  code: string;
  name: string;
  short_name: string;
  model: string;
  role: string;
  status: RobotStatus;
  battery: number;
  location: string;
  zone: string;
  building: string;
  floor: string | null;
  last_seen: string;
  capabilities: string[];
}

export interface Park {
  park_id: string;
  name: string;
  status: string;
  timezone: string;
  summary: { buildings: number; managed_floors: number; outdoor_zones: number; robot_fleet: number };
  areas: Array<{ id: string; name: string; type: string; zones?: number; floors?: string[] }>;
}

export interface DashboardData {
  park: Park;
  robots: Robot[];
  fleet: { available: number; charging: number; average_battery: number };
  system: { mode: string; phase: string };
}

