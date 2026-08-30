from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import router
from database.connection import initialize_database
from analytics.history_seed import seed_history
from robot_operations.repository import initialize as initialize_operations
from robot_operations.repository import recover_interrupted_requests
from robot_operations.routes import router as operations_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    initialize_operations()
    recover_interrupted_requests()
    seed_history()
    yield


app = FastAPI(
    title="AI Autonomous Cleaning Demo",
    version="0.6.0",
    description="Phase 8: customer-facing autonomous cleaning task workbench.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Both hostnames are commonly used by Vite during local demos. Keep this
    # explicit rather than using a permissive wildcard with credentials.
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/demo-assets", StaticFiles(directory=Path(__file__).resolve().parents[1] / "sample_data" / "camera_events"), name="demo-assets")
app.include_router(router)
app.include_router(operations_router)
