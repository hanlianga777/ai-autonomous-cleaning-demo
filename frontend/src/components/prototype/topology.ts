export type TopologyAnchor = {
  id: string;
  building: "OUTDOOR" | "A" | "B";
  floor: "ROAD" | "1F" | "2F";
  normalized_x: number;
  normalized_y: number;
  type: "standby" | "event" | "road" | "elevator_entry" | "elevator_exit" | "skybridge_entry" | "skybridge_exit";
  label: string;
};

/** Customer-map projection of the locked Phase 2 topology, not freehand SVG coordinates. */
export const campusTopology: Record<string, TopologyAnchor> = {
  OUTDOOR_A_STANDBY: { id: "OUTDOOR_A_STANDBY", building: "OUTDOOR", floor: "ROAD", normalized_x: 0.18, normalized_y: 0.79, type: "standby", label: "东侧道路待命点" },
  OUTDOOR_D_STANDBY: { id: "OUTDOOR_D_STANDBY", building: "OUTDOOR", floor: "ROAD", normalized_x: 0.85, normalized_y: 0.77, type: "standby", label: "配送区待命点" },
  OUTDOOR_EAST_ROAD_EVENT: { id: "OUTDOOR_EAST_ROAD_EVENT", building: "OUTDOOR", floor: "ROAD", normalized_x: 0.28, normalized_y: 0.78, type: "road", label: "东侧道路" },
  A_1F_ROBOT_B_STANDBY: { id: "A_1F_ROBOT_B_STANDBY", building: "A", floor: "1F", normalized_x: 0.33, normalized_y: 0.55, type: "standby", label: "A栋1F待命点" },
  A_1F_LOBBY_EVENT: { id: "A_1F_LOBBY_EVENT", building: "A", floor: "1F", normalized_x: 0.39, normalized_y: 0.55, type: "event", label: "A栋1F大堂" },
  B_1F_ROBOT_C_STANDBY: { id: "B_1F_ROBOT_C_STANDBY", building: "B", floor: "1F", normalized_x: 0.73, normalized_y: 0.58, type: "standby", label: "B栋1F待命点" },
  B_1F_ELEVATOR_ENTRY: { id: "B_1F_ELEVATOR_ENTRY", building: "B", floor: "1F", normalized_x: 0.75, normalized_y: 0.51, type: "elevator_entry", label: "B栋1F电梯入口" },
  B_2F_ELEVATOR_EXIT: { id: "B_2F_ELEVATOR_EXIT", building: "B", floor: "2F", normalized_x: 0.74, normalized_y: 0.35, type: "elevator_exit", label: "B栋2F电梯出口" },
  B_2F_SKYBRIDGE_ENTRY: { id: "B_2F_SKYBRIDGE_ENTRY", building: "B", floor: "2F", normalized_x: 0.59, normalized_y: 0.28, type: "skybridge_entry", label: "B栋2F连廊入口" },
  A_2F_SKYBRIDGE_EXIT: { id: "A_2F_SKYBRIDGE_EXIT", building: "A", floor: "2F", normalized_x: 0.51, normalized_y: 0.27, type: "skybridge_exit", label: "A栋2F连廊出口" },
  A_2F_CAN_EVENT: { id: "A_2F_CAN_EVENT", building: "A", floor: "2F", normalized_x: 0.35, normalized_y: 0.28, type: "event", label: "A栋2F连廊区域" },
  A_2F_LARGE_OBJECT_EVENT: { id: "A_2F_LARGE_OBJECT_EVENT", building: "A", floor: "2F", normalized_x: 0.37, normalized_y: 0.25, type: "event", label: "A栋2F公共区域" },
};

export const eventAnchorByDemo = { outdoor: "OUTDOOR_EAST_ROAD_EVENT", liquid: "A_1F_LOBBY_EVENT", can: "A_2F_CAN_EVENT", oversized: "A_2F_LARGE_OBJECT_EVENT" } as const;
export const standbyAnchorByRobot: Record<string, string> = { "赛特净界 S5": "OUTDOOR_A_STANDBY", "高仙 Omnie": "A_1F_ROBOT_B_STANDBY", "蜗小白 SC50": "B_1F_ROBOT_C_STANDBY", "普渡 FlashBot Max": "OUTDOOR_D_STANDBY" };
