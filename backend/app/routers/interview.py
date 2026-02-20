"""Interview question flow endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import InterviewQuestion, SubmitAnswerRequest
from app.services.interview_agent import (
    create_interview,
    deserialize_state,
    generate_dynamic_question,
    serialize_state,
    submit_answer,
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

    if state["phase"] == "defaults":
        return {"phase": "defaults", "message": "Fase de perguntas concluída. Confirme os padrões."}

    current = state.get("current_question")

    # Dynamic phase with no current question: generate one
    if current is None and state["phase"] == "dynamic":
        question, new_state = await generate_dynamic_question(state)
        if question is not None:
            session.interview_state = serialize_state(new_state)
            db.commit()
            return question.model_dump()
        # Generation failed or max reached — transitioned to defaults
        session.interview_state = serialize_state(new_state)
        db.commit()
        return {"phase": new_state["phase"], "message": "Fase de perguntas concluída. Confirme os padrões."}

    if current is None:
        return {"phase": state["phase"], "message": "Nenhuma pergunta disponível"}

    question = InterviewQuestion.model_validate(current)
    return question.model_dump()


@router.post("/{session_id}/interview/answer")
async def post_submit_answer(
    session_id: str,
    body: SubmitAnswerRequest,
    db: Session = Depends(get_db),
) -> dict:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.interview_state is None:
        raise HTTPException(status_code=400, detail="Interview not started")

    state = deserialize_state(session.interview_state)

    if state["phase"] == "complete":
        raise HTTPException(status_code=400, detail="Interview already complete")

    try:
        next_question, new_state = await submit_answer(
            state, body.question_id, body.answer, body.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Persist answer in interview_responses (clean list for agent generation)
    responses = list(session.interview_responses or [])
    responses.append({
        "question_id": body.question_id,
        "answer": body.answer,
        "source": body.source,
    })
    session.interview_responses = responses
    session.interview_state = serialize_state(new_state)
    db.commit()

    if next_question is not None:
        result: dict = {"received": True, "next_question": next_question.model_dump()}
        if new_state.get("needs_follow_up"):
            result["follow_up"] = next_question.model_dump()
        return result

    phase = new_state["phase"]
    if phase == "defaults":
        message = "Entrevista concluída. Prossiga para confirmação dos padrões."
    else:
        message = "Nenhuma próxima pergunta disponível."
    return {
        "received": True,
        "next_question": None,
        "phase": phase,
        "message": message,
    }
