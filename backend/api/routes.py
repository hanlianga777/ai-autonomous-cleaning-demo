import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from database.connection import get_transitions_after, list_events, read_snapshot
from spatial.calibration import CalibrationError, map_pixel_to_slam
from spatial.route_planner import RouteNotFoundError, plan_route
from spatial.service import get_map, spatial_overview
from workflow.engine import WorkflowError, create_mock_event, evaluate_event, event_detail, run_event
from workflow.fixtures import EVENT_TEMPLATES

router = APIRouter(prefix="/api", tags=["Demo API"])


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "phase": 3, "mode": "DEMO MOCK MODE"}


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
        "system": {"mode": "DEMO MOCK MODE", "phase": "Phase 3 · Workflow + Scheduler"},
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


@router.get("/events", tags=["Workflow + Scheduler"])
def get_events(limit: int = Query(20, ge=1, le=100)) -> list[dict]:
    return list_events(limit)


@router.get("/events/templates", tags=["Workflow + Scheduler"])
def get_event_templates() -> list[dict]:
    return [{"template": key, "label": value["label"]} for key, value in EVENT_TEMPLATES.items()]


@router.post("/events/mock/{template_name}", tags=["Workflow + Scheduler"])
def post_mock_event(template_name: str) -> dict:
    try:
        return create_mock_event(template_name)
    except WorkflowError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/events/{event_id}/run", tags=["Workflow + Scheduler"])
def post_run_event(event_id: str) -> dict:
    try:
        return run_event(event_id)
    except WorkflowError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/scheduler/evaluate", tags=["Workflow + Scheduler"])
def post_scheduler_evaluate(event_id: str = Query(...)) -> dict:
    try:
        return evaluate_event(event_id)
    except WorkflowError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/events/stream", tags=["Workflow + Scheduler"])
async def stream_events(last_event_id: int = Query(0, ge=0)) -> StreamingResponse:
    async def event_stream():
        cursor = last_event_id
        while True:
            transitions = get_transitions_after(cursor)
            for transition in transitions:
                cursor = transition["id"]
                yield f"event: workflow\ndata: {json.dumps(transition, ensure_ascii=False)}\n\n"
            if not transitions:
                yield ": keepalive\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/events/{event_id}", tags=["Workflow + Scheduler"])
def get_event_detail(event_id: str) -> dict:
    try:
        return event_detail(event_id)
    except WorkflowError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
