"""FastAPI application initialization."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.models import orm as _orm  # noqa: F401 — register models with Base
from app.routers import enrichment, interview, sessions


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


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
