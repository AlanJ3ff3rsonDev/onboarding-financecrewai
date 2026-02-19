"""Interview question flow endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import InterviewQuestion
from app.services.interview_agent import (
    create_interview,
    deserialize_state,
    serialize_state,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["interview"])


@router.get("/{session_id}/interview/next")
async def get_next_question(
    session_id: str,
    db: Session = Depends(get_db),
) -> dict:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.interview_state is None:
        # First call — initialize the interview
        enrichment = session.enrichment_data or {}
        state = await create_interview(enrichment_data=enrichment)
        session.interview_state = serialize_state(state)
        session.status = "interviewing"
        db.commit()
    else:
        state = deserialize_state(session.interview_state)

    if state["phase"] == "complete":
        return {"phase": "complete", "message": "Entrevista completa"}

    current = state.get("current_question")
    if current is None:
        return {"phase": state["phase"], "message": "Nenhuma pergunta disponível"}

    question = InterviewQuestion.model_validate(current)
    return question.model_dump()
