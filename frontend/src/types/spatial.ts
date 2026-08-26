export interface Zone {
  zone_id: string; name: string; surface_type: string; crowd_level: string; cleaning_priority: string; x: number; y: number; w: number; h: number;
}
export interface Point { x: number; y: number; }
export interface Camera {
  camera_id: string; name: string; map_id: string; building: string; floor: string; zone: string; camera_position: Point; coverage_polygon: Point[]; calibration_points: Array<{ pixel: {u:number;v:number}; slam: Point }>; neighbor_cameras: string[];
}
export interface SpatialMap { map_id: string; label: string; building: string; floor: string; width: number; height: number; zones: Zone[]; obstacles: Array<{x:number;y:number;w:number;h:number}>; elevators?: Array<{id:string;label:string;x:number;y:number}>; entrances?: Array<{id:string;label:string;x:number;y:number}>; navigation_nodes?: Point[]; }
export interface SpatialOverview { maps: SpatialMap[]; cameras: Camera[]; robot_positions: Record<string, {map_id:string;x:number;y:number}>; }
export interface Route { start_map:string; target_map:string; total_cost:number; node_path:string[]; display_path:string[]; segments:Array<{from:string;to:string;type:string;cost:number}>; }
export interface MappingResult { camera_id:string; pixel:{u:number;v:number}; location:{building:string;floor:string;zone:string;x:number;y:number}; }
