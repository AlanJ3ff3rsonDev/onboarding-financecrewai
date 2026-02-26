"""FastAPI application initialization."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import Base, engine
from app.dependencies import verify_api_key
from app.limiter import limiter
from app.models import orm as _orm  # noqa: F401 — register models with Base
from app.routers import agent, audio, enrichment, interview, sessions, simulation


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    Base.metadata.create_all(bind=engine)
    yield


_is_production = settings.ENVIRONMENT == "production"

app = FastAPI(
    title="CollectAI Onboarding API",
    description="Self-service onboarding backend for collection agent configuration",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."},
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-API-Key"],
)

_auth = [Depends(verify_api_key)]
app.include_router(sessions.router, dependencies=_auth)
app.include_router(enrichment.router, dependencies=_auth)
app.include_router(interview.router, dependencies=_auth)
app.include_router(audio.router, dependencies=_auth)
app.include_router(agent.router, dependencies=_auth)
app.include_router(simulation.router, dependencies=_auth)


@app.get("/health")
@limiter.exempt
async def health_check(request: Request) -> dict[str, str]:
    return {"status": "ok"}
