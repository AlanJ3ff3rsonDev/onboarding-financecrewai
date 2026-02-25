"""FastAPI application initialization."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.dependencies import verify_api_key
from app.models import orm as _orm  # noqa: F401 — register models with Base
from app.routers import agent, audio, enrichment, interview, sessions, simulation


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

_auth = [Depends(verify_api_key)]
app.include_router(sessions.router, dependencies=_auth)
app.include_router(enrichment.router, dependencies=_auth)
app.include_router(interview.router, dependencies=_auth)
app.include_router(audio.router, dependencies=_auth)
app.include_router(agent.router, dependencies=_auth)
app.include_router(simulation.router, dependencies=_auth)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
