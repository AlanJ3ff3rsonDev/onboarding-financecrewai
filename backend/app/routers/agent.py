"""Agent generation and retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import AgentConfig
from app.services.agent_generator import generate_agent_config

router = APIRouter(prefix="/api/v1/sessions", tags=["agent"])


@router.post("/{session_id}/agent/generate")
async def generate_agent(
    session_id: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status not in ("interviewed", "generated"):
        raise HTTPException(
            status_code=400,
            detail="Interview must be completed before generating agent config",
        )

    session.status = "generating"
    db.commit()

    try:
        config = await generate_agent_config(
            company_profile=session.enrichment_data,
            interview_responses=session.interview_responses or [],
            smart_defaults=session.smart_defaults,
            session_id=session_id,
        )
    except ValueError as exc:
        session.status = "interviewed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session.agent_config = config.model_dump()
    session.status = "generated"
    db.commit()

    return {"status": "generated", "agent_config": config.model_dump()}


@router.get("/{session_id}/agent", response_model=AgentConfig)
async def get_agent(
    session_id: str,
    db: Session = Depends(get_db),
) -> AgentConfig:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.agent_config is None:
        raise HTTPException(status_code=404, detail="Agent config not generated yet")

    return AgentConfig(**session.agent_config)
