from fastapi import APIRouter, HTTPException
from observability.service import trace_view

router = APIRouter(prefix="/api/advanced", tags=["Read-only Technical Observability"])


@router.get("/trace")
def get_trace(event_id: str | None = None):
    try:
        return trace_view(event_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
