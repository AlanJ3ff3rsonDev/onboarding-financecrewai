"""Simulation generation and retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.models.orm import OnboardingSession
from app.models.schemas import OnboardingReport, SimulationResult
from app.services.simulation import generate_simulation

router = APIRouter(prefix="/api/v1/sessions", tags=["simulation"])


@router.post("/{session_id}/simulation/generate")
@limiter.limit("5/minute")
async def generate_simulation_endpoint(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.agent_config is None:
        raise HTTPException(
            status_code=400,
            detail="Agent config not generated yet. Call POST /agent/generate first.",
        )

    if session.status not in ("generated", "completed"):
        raise HTTPException(
            status_code=400,
            detail="Agent config must be generated before running simulation",
        )

    session.status = "simulating"
    db.commit()

    try:
        report = OnboardingReport(**session.agent_config)
        result = await generate_simulation(report, session_id=session_id)
    except ValueError as exc:
        session.status = "generated"
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session.simulation_result = result.model_dump()
    session.status = "completed"
    db.commit()

    return {"status": "completed", "simulation_result": result.model_dump()}


@router.get("/{session_id}/simulation", response_model=SimulationResult)
@limiter.limit("60/minute")
async def get_simulation(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
) -> SimulationResult:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.simulation_result is None:
        raise HTTPException(status_code=404, detail="Simulation not generated yet")

    return SimulationResult(**session.simulation_result)
