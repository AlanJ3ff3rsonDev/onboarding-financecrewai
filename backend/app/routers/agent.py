"""Agent generation, retrieval, and adjustment endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import AgentAdjustRequest, OnboardingReport
from app.services.agent_generator import adjust_onboarding_report, generate_onboarding_report

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
        report = await generate_onboarding_report(
            company_profile=session.enrichment_data,
            interview_responses=session.interview_responses or [],
            session_id=session_id,
        )
    except ValueError as exc:
        session.status = "interviewed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session.agent_config = report.model_dump()
    session.status = "generated"
    db.commit()

    return {"status": "generated", "onboarding_report": report.model_dump()}


@router.get("/{session_id}/agent", response_model=OnboardingReport)
async def get_agent(
    session_id: str,
    db: Session = Depends(get_db),
) -> OnboardingReport:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.agent_config is None:
        raise HTTPException(status_code=404, detail="Agent config not generated yet")

    return OnboardingReport(**session.agent_config)


@router.put("/{session_id}/agent/adjust")
async def adjust_agent(
    session_id: str,
    request: AgentAdjustRequest,
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

    try:
        report = await adjust_onboarding_report(
            current_report=session.agent_config,
            adjustments=request.adjustments,
            session_id=session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session.agent_config = report.model_dump()
    db.commit()

    return {"status": "adjusted", "onboarding_report": report.model_dump()}
