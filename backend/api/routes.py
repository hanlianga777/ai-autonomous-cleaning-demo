from fastapi import APIRouter, HTTPException, Query

from database.connection import read_snapshot
from spatial.calibration import CalibrationError, map_pixel_to_slam
from spatial.route_planner import RouteNotFoundError, plan_route
from spatial.service import get_map, spatial_overview

router = APIRouter(prefix="/api", tags=["Demo API"])


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "phase": 2, "mode": "DEMO MOCK MODE"}


@router.get("/park")
def get_park() -> dict:
    return read_snapshot("park")


@router.get("/robots")
def get_robots() -> list[dict]:
    return read_snapshot("robots")


@router.get("/dashboard")
def get_dashboard() -> dict:
    park = read_snapshot("park")
    robots = read_snapshot("robots")
    return {
        "park": park,
        "robots": robots,
        "fleet": {
            "available": sum(robot["status"] == "idle" for robot in robots),
            "charging": sum(robot["status"] == "charging" for robot in robots),
            "average_battery": round(sum(robot["battery"] for robot in robots) / len(robots)),
        },
        "system": {"mode": "DEMO MOCK MODE", "phase": "Phase 2 · Spatial Engine"},
    }


@router.get("/robots/{robot_id}")
def get_robot(robot_id: str) -> dict:
    robot = next((item for item in read_snapshot("robots") if item["id"] == robot_id), None)
    if robot is None:
        raise HTTPException(status_code=404, detail="Robot not found")
    return robot


@router.get("/spatial/overview", tags=["Spatial Engine"])
def get_spatial_overview() -> dict:
    return spatial_overview()


@router.get("/spatial/maps/{map_id}", tags=["Spatial Engine"])
def get_spatial_map(map_id: str) -> dict:
    map_data = get_map(map_id)
    if map_data is None:
        raise HTTPException(status_code=404, detail="Spatial map not found")
    return map_data


@router.get("/spatial/routes", tags=["Spatial Engine"])
def get_spatial_route(start: str = Query(...), target: str = Query(...)) -> dict:
    try:
        return plan_route(start, target)
    except RouteNotFoundError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/spatial/cameras/{camera_id}/map", tags=["Spatial Engine"])
def get_camera_mapping(camera_id: str, u: float = Query(...), v: float = Query(...)) -> dict:
    try:
        return map_pixel_to_slam(camera_id, u, v)
    except CalibrationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
