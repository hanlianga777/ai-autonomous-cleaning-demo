import asyncio
import json

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from database.connection import get_event, get_fleet_state, read_snapshot, reset_fleet_state
from event_archive.service import archive_index
from analytics.service import analytics_overview, heatmap, kpis, robot_utilization, task_history
from operations.service import list_work_orders, operations_snapshot, start_scenario, start_upload
from perception.service import MAX_UPLOAD_BYTES, RealInferenceError, ai_lab_schema, ai_lab_status, analyze_mock_case, analyze_upload, available_mock_cases, interview_ai_readiness_probe, media_kind, save_upload, system_ai_status
from spatial.calibration import CalibrationError, map_pixel_to_slam
from spatial.route_planner import RouteNotFoundError, plan_route
from spatial.service import get_map, spatial_overview
from demo_v1.service import (
    assign_event,
    cloud_review,
    customer_event_snapshot,
    complete_cleaning,
    complete_demo04_manual,
    complete_navigation,
    create_demo_event,
    edge_review,
    locate_event,
    multi_view_review,
    scenario_catalog,
    start_autonomous_progression,
    start_navigation,
    verify_event,
)
from api.runtime_contract import runtime_fingerprint

router = APIRouter(prefix="/api", tags=["Demo API"])
API_CONTRACT = "operations.v1"


@router.get("/demo-v1/scenarios", tags=["Integrated Customer Demo"])
def get_demo_v1_scenarios() -> list[dict]:
    return scenario_catalog()


def _demo_stage(handler, *args, **kwargs) -> dict:
    try:
        return handler(*args, **kwargs)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/demo-v1/events", tags=["Integrated Customer Demo"])
def post_demo_v1_event(
    demo_id: str = Query(..., pattern="^demo0[1-4]$"),
    mode: str = Query("live", pattern="^(live|replay)$"),
) -> dict:
    created = _demo_stage(create_demo_event, demo_id, "STABLE_REPLAY" if mode == "replay" else "LIVE")
    start_autonomous_progression(str(created["event_id"]))
    return created


@router.get("/demo-v1/events/{event_id}", tags=["Integrated Customer Demo"])
def get_demo_v1_event(event_id: str) -> dict:
    """Read the authoritative customer projection for a live demo event."""
    try:
        return customer_event_snapshot(event_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/demo-v1/events/{event_id}/edge-review", tags=["Integrated Customer Demo"])
def post_demo_v1_edge_review(event_id: str) -> dict:
    return _demo_stage(edge_review, event_id)


@router.post("/demo-v1/events/{event_id}/multi-view", tags=["Integrated Customer Demo"])
def post_demo_v1_multi_view(event_id: str) -> dict:
    return _demo_stage(multi_view_review, event_id)


@router.post("/demo-v1/events/{event_id}/cloud-review", tags=["Integrated Customer Demo"])
def post_demo_v1_cloud_review(event_id: str, simulate_unavailable: bool = Query(False)) -> dict:
    return _demo_stage(cloud_review, event_id, force_unavailable=simulate_unavailable)


@router.post("/demo-v1/events/{event_id}/locate", tags=["Integrated Customer Demo"])
def post_demo_v1_locate(event_id: str) -> dict:
    return _demo_stage(locate_event, event_id)


@router.post("/demo-v1/events/{event_id}/assign", tags=["Integrated Customer Demo"])
def post_demo_v1_assign(event_id: str) -> dict:
    return _demo_stage(assign_event, event_id)


@router.post("/demo-v1/events/{event_id}/start-navigation", tags=["Integrated Customer Demo"])
def post_demo_v1_start_navigation(event_id: str) -> dict:
    return _demo_stage(start_navigation, event_id)


@router.post("/demo-v1/events/{event_id}/complete-navigation", tags=["Integrated Customer Demo"])
def post_demo_v1_complete_navigation(event_id: str) -> dict:
    return _demo_stage(complete_navigation, event_id)


@router.post("/demo-v1/events/{event_id}/complete-cleaning", tags=["Integrated Customer Demo"])
def post_demo_v1_complete_cleaning(event_id: str) -> dict:
    return _demo_stage(complete_cleaning, event_id)


@router.post("/demo-v1/events/{event_id}/verify", tags=["Integrated Customer Demo"])
def post_demo_v1_verify(event_id: str) -> dict:
    return _demo_stage(verify_event, event_id)


@router.post("/demo-v1/runs/{demo_id}", tags=["Integrated Customer Demo"])
def post_demo_v1_run(demo_id: str, mode: str = Query("live", pattern="^(live|replay)$")) -> dict:
    raise HTTPException(status_code=410, detail="This one-shot endpoint is retired. Create /demo-v1/events and advance one stage at a time.")


@router.post("/demo-v1/runs/{demo_id}/simulate-unavailable", tags=["Integrated Customer Demo"])
def post_demo_v1_unavailable(demo_id: str) -> dict:
    raise HTTPException(status_code=410, detail="This one-shot endpoint is retired. Use /demo-v1/events/{event_id}/cloud-review?simulate_unavailable=true.")


@router.post("/demo-v1/manual-work-orders/{event_id}/complete", tags=["Integrated Customer Demo"])
def post_demo_v1_manual_completion(event_id: str) -> dict:
    # A cleaning event delegated to Robot Operations has one mutation owner.
    # Its task-card action supplies the session boundary and durable lease; do
    # not leave this legacy endpoint as a bypass merely because it is hidden.
    if (get_event(event_id) or {}).get("operations_task_id"):
        raise HTTPException(status_code=409, detail="Task-owned manual completion must use the Robot Operations task action.")
    try:
        return complete_demo04_manual(event_id)
    except (ValueError, RealInferenceError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/health")
def health_check() -> dict:
    status = ai_lab_status()
    return {
        "status": "ok",
        "phase": 8,
        "api_contract": API_CONTRACT,
        **runtime_fingerprint(),
        "mode": status["mode_label"],
        "ai_lab": {"active_mode": status["active_mode"], "real_ready": status["real_ready"]},
    }


@router.get("/system/ai-status", tags=["System"])
def get_system_ai_status() -> dict:
    return system_ai_status()


@router.post("/system/ai-readiness/probe", tags=["System"])
def post_interview_ai_readiness_probe() -> dict:
    return interview_ai_readiness_probe()


@router.get("/park")
def get_park() -> dict:
    return read_snapshot("park")


@router.get("/robots")
def get_robots() -> list[dict]:
    return get_fleet_state()


@router.post("/fleet/reset", tags=["Integrated Customer Demo"])
def post_fleet_reset() -> dict:
    return {"fleet": _demo_stage(reset_fleet_state), "source": "explicit_demo_reset"}


@router.get("/dashboard")
def get_dashboard() -> dict:
    park = read_snapshot("park")
    robots = get_fleet_state()
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
def get_analytics_overview(event_type: str | None = None, since: str | None = None,
                           until: str | None = None, hour: int | None = Query(None, ge=0, le=23), time_slot: str | None = None) -> dict:
    try:
        return analytics_overview(event_type=event_type, since=since, until=until, hour=hour, time_slot=time_slot)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


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
    raise HTTPException(status_code=410, detail="Fixed recommendations are retired. Use /api/robot-operations/advice; regeneration requires an explicit POST.")


@router.get("/workbench/scenario02/assets", tags=["Customer Workbench"])
def get_workbench_scenario_02_assets() -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. The active Workbench uses /api/demo-v1/scenarios and /api/demo-v1/events.")


@router.post("/workbench/scenario02/run", tags=["Customer Workbench"])
def post_workbench_scenario_02_run() -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Use the authoritative /demo-v1/events runtime.")


@router.get("/workbench/scenarios", tags=["Customer Workbench"])
def get_workbench_scenarios() -> list[dict]:
    raise HTTPException(status_code=410, detail="Retired customer path. Use /api/demo-v1/scenarios.")


@router.post("/workbench/events/{event_id}/run", tags=["Customer Workbench"])
def post_workbench_event(event_id: str) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Use the authoritative /demo-v1/events runtime.")


@router.post("/workbench/upload", tags=["Customer Workbench"])
async def post_workbench_upload(file: UploadFile = File(...)) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Upload workflows are engineering-test only.")


@router.get("/operations/snapshot", tags=["Customer Operations"])
def get_operations_snapshot(run_id: str | None = Query(None)) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Use the active Workbench and Robot Operations Agent projections.")


@router.get("/operations/work-orders", tags=["Customer Operations"])
def get_operations_work_orders(limit: int = Query(50, ge=1, le=100)) -> list[dict]:
    raise HTTPException(status_code=410, detail="Retired customer path. Use /api/event-archive.")


@router.post("/operations/runs/{event_id}", tags=["Customer Operations"])
def post_operations_run(event_id: str) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Use Robot Operations or /demo-v1/events.")


@router.post("/operations/upload", tags=["Customer Operations"])
async def post_operations_upload(file: UploadFile = File(...)) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Upload workflows are engineering-test only.")


@router.get("/robots/{robot_id}")
def get_robot(robot_id: str) -> dict:
    robot = next((item for item in get_fleet_state() if item["id"] == robot_id), None)
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
    raise HTTPException(status_code=410, detail="AI Lab mock execution is engineering-test only and is not a customer runtime path.")


@router.post("/ai-lab/analyze", tags=["AI Lab"])
async def post_ai_lab_analyze(
    file: UploadFile = File(...),
    camera_id: str = Query("CAM-A1-01"),
) -> dict:
    await file.close()
    raise HTTPException(status_code=410, detail="AI Lab uploads are engineering-test only and are not a customer runtime path.")


@router.post("/multiview/scenario02/run", tags=["Multi-view Perception Agent"])
def post_multiview_scenario_02() -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Multi-view is evidence-gated within cloud-review.")


@router.get("/events", tags=["Workflow + Scheduler"])
def get_events(limit: int = Query(20, ge=1, le=100)) -> list[dict]:
    raise HTTPException(status_code=410, detail="Retired customer path. Read customer records through /api/event-archive.")


@router.get("/event-archive", tags=["Read-only Event Archive"])
def get_event_archive(category: str = "all", q: str = Query("", max_length=200),
                      event_type: str | None = None, handling_mode: str | None = None,
                      since: str | None = None, until: str | None = None, map_id: str | None = None,
                      offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                      hour: int | None = Query(None, ge=0, le=23), x: float | None = None, y: float | None = None, time_slot: str | None = None) -> dict:
    try:
        return archive_index(category=category, q=q, event_type=event_type, handling_mode=handling_mode,
                             since=since, until=until, map_id=map_id, offset=offset, limit=limit, hour=hour, x=x, y=y, time_slot=time_slot)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/event-archive/{event_id}", tags=["Read-only Event Archive"])
def get_event_archive_detail(event_id: str) -> dict:
    """Read an event through the archive boundary, never the legacy workflow API."""
    if event_id.startswith("integrated-"):
        return get_demo_v1_event(event_id)
    from event_archive.service import archived_event_snapshot
    try:
        return archived_event_snapshot(event_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/events/templates", tags=["Workflow + Scheduler"])
def get_event_templates() -> list[dict]:
    raise HTTPException(status_code=410, detail="Mock workflow templates are engineering-test only.")


@router.post("/events/mock/{template_name}", tags=["Workflow + Scheduler"])
def post_mock_event(template_name: str) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Mock events are engineering-test only.")


@router.post("/events/{event_id}/run", tags=["Workflow + Scheduler"])
def post_run_event(event_id: str) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Use the authoritative /demo-v1/events runtime.")


@router.post("/scheduler/evaluate", tags=["Workflow + Scheduler"])
def post_scheduler_evaluate(event_id: str = Query(...)) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Scheduler is invoked only by the authoritative runtime.")


@router.get("/events/stream", tags=["Workflow + Scheduler"])
async def stream_events(last_event_id: int = Query(0, ge=0)) -> StreamingResponse:
    raise HTTPException(status_code=410, detail="Legacy workflow streaming is retired. Customer surfaces poll the authoritative archive/runtime projections.")


@router.get("/events/{event_id}", tags=["Workflow + Scheduler"])
def get_event_detail(event_id: str) -> dict:
    raise HTTPException(status_code=410, detail="Retired customer path. Read customer records through /api/event-archive/{event_id}.")
