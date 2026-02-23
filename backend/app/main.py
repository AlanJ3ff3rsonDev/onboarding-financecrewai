"""FastAPI application initialization."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.models import orm as _orm  # noqa: F401 — register models with Base
from app.routers import agent, audio, enrichment, interview, sessions, simulation

UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CollectAI Onboarding API",
    description="Self-service onboarding backend for collection agent configuration",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(sessions.router)
app.include_router(enrichment.router)
app.include_router(interview.router)
app.include_router(audio.router)
app.include_router(agent.router)
app.include_router(simulation.router)

# Serve uploaded files (avatars, etc.)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
