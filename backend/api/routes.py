import asyncio
import json

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from database.connection import get_transitions_after, list_events, read_snapshot
from analytics.service import analytics_overview, heatmap, kpis, robot_utilization, task_history
from optimization.agent import generate_recommendations
from operations.service import operations_snapshot, start_scenario, start_upload
from perception.service import MAX_UPLOAD_BYTES, RealInferenceError, ai_lab_schema, ai_lab_status, analyze_mock_case, analyze_upload, available_mock_cases, media_kind, save_upload
from spatial.calibration import CalibrationError, map_pixel_to_slam
from spatial.route_planner import RouteNotFoundError, plan_route
from spatial.service import get_map, spatial_overview
from workflow.engine import WorkflowError, create_mock_event, evaluate_event, event_detail, run_event, run_scenario_02
from workflow.fixtures import EVENT_TEMPLATES
from workbench.service import list_scenario_assets, run_scenario_02_workbench, run_workbench_event, run_workbench_upload, scenario_02_assets

router = APIRouter(prefix="/api", tags=["Demo API"])
API_CONTRACT = "operations.v1"


@router.get("/health")
def health_check() -> dict:
    status = ai_lab_status()
    return {"status": "ok", "phase": 8, "api_contract": API_CONTRACT, "mode": status["mode_label"], "ai_lab": {"active_mode": status["active_mode"], "real_ready": status["real_ready"]}}


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
        "system": {"mode": ai_lab_status()["mode_label"], "phase": "Phase 8 · Customer Demo Workbench"},
    }


@router.get("/analytics/overview", tags=["Analytics + Optimization"])
def get_analytics_overview() -> dict:
    return analytics_overview()


@router.get("/analytics/heatmap", tags=["Analytics + Optimization"])
def get_analytics_heatmap() -> list[dict]:
    return heatmap()


@router.get("/analytics/kpis", tags=["Analytics + Optimization"])
def get_analytics_kpis() -> dict:
    return kpis()


@router.get("/analytics/robot-utilization", tags=["Analytics + Optimization"])
def get_analytics_robot_utilization() -> list[dict]:
    return robot_utilization()


@router.get("/analytics/task-history", tags=["Analytics + Optimization"])
def get_analytics_task_history() -> list[dict]:
    return task_history()


@router.post("/optimization/recommend", tags=["Analytics + Optimization"])
def post_optimization_recommendations() -> dict:
    return generate_recommendations()


@router.get("/workbench/scenario02/assets", tags=["Customer Workbench"])
def get_workbench_scenario_02_assets() -> dict:
    return scenario_02_assets()


@router.post("/workbench/scenario02/run", tags=["Customer Workbench"])
def post_workbench_scenario_02_run() -> dict:
    return run_scenario_02_workbench()


@router.get("/workbench/scenarios", tags=["Customer Workbench"])
def get_workbench_scenarios() -> list[dict]:
    return list_scenario_assets()


@router.post("/workbench/events/{event_id}/run", tags=["Customer Workbench"])
def post_workbench_event(event_id: str) -> dict:
    try:
        return run_workbench_event(event_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/workbench/upload", tags=["Customer Workbench"])
async def post_workbench_upload(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="An upload filename is required.")
    try:
        media_kind(file.filename)
        content = await file.read()
        if not content:
            raise ValueError("The uploaded file is empty.")
        if len(content) > MAX_UPLOAD_BYTES:
            raise ValueError(f"The upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
        return run_workbench_upload(file.filename, content)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        await file.close()


@router.get("/operations/snapshot", tags=["Customer Operations"])
def get_operations_snapshot(run_id: str | None = Query(None)) -> dict:
    """Server-projected mock telemetry, work-order and fleet read model."""
    return operations_snapshot(run_id)


@router.post("/operations/runs/{event_id}", tags=["Customer Operations"])
def post_operations_run(event_id: str) -> dict:
    try:
        return start_scenario(event_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/operations/upload", tags=["Customer Operations"])
async def post_operations_upload(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="An upload filename is required.")
    try:
        media_kind(file.filename)
        content = await file.read()
        if not content:
            raise ValueError("The uploaded file is empty.")
        if len(content) > MAX_UPLOAD_BYTES:
            raise ValueError(f"The upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
        return start_upload(file.filename, content)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        await file.close()


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


@router.get("/ai-lab/status", tags=["AI Lab"])
def get_ai_lab_status() -> dict:
    """Expose the resolved runtime mode without exposing secrets."""
    return ai_lab_status()


@router.get("/ai-lab/schema", tags=["AI Lab"])
def get_ai_lab_schema() -> dict:
    return ai_lab_schema()


@router.get("/ai-lab/mock-cases", tags=["AI Lab"])
def get_ai_lab_mock_cases() -> list[dict[str, str]]:
    return available_mock_cases()


@router.post("/ai-lab/mock-cases/{case_name}", tags=["AI Lab"])
def post_ai_lab_mock_case(case_name: str) -> dict:
    try:
        return analyze_mock_case(case_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/ai-lab/analyze", tags=["AI Lab"])
async def post_ai_lab_analyze(
    file: UploadFile = File(...),
    camera_id: str = Query("CAM-A1-01"),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="An upload filename is required.")
    try:
        media_kind(file.filename)
        file_path = save_upload(file.filename, await file.read())
        return analyze_upload(file_path, file.filename, camera_id)
    except (ValueError, RealInferenceError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    finally:
        await file.close()


@router.post("/multiview/scenario02/run", tags=["Multi-view Perception Agent"])
def post_multiview_scenario_02() -> dict:
    try:
        return run_scenario_02()
    except WorkflowError as error:
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
