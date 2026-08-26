from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from database.connection import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="AI Autonomous Cleaning Demo",
    version="0.5.0",
    description="Phase 7: interview-ready UX over the established autonomous cleaning demo.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Both hostnames are commonly used by Vite during local demos. Keep this
    # explicit rather than using a permissive wildcard with credentials.
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
