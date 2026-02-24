"""Interview question flow endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import (
    InterviewProgressResponse,
    InterviewQuestion,
    InterviewReviewRequest,
    SubmitAnswerRequest,
)
from app.prompts.interview import CORE_QUESTIONS
from app.services.interview_agent import (
    create_interview,
    deserialize_state,
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

    if state["phase"] == "review":
        return {"phase": "review", "message": "Fase de perguntas concluída. Revise as respostas e confirme."}

    current = state.get("current_question")

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
    if phase == "review":
        message = "Entrevista concluída. Prossiga para revisão das respostas."
    else:
        message = "Nenhuma próxima pergunta disponível."
    return {
        "received": True,
        "next_question": None,
        "phase": phase,
        "message": message,
    }


@router.get("/{session_id}/interview/progress")
async def get_interview_progress(
    session_id: str,
    db: Session = Depends(get_db),
) -> InterviewProgressResponse:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.interview_state is None:
        return InterviewProgressResponse(
            phase="not_started",
            total_answered=0,
            core_answered=0,
            core_total=len(CORE_QUESTIONS),
            estimated_remaining=len(CORE_QUESTIONS),
            is_complete=False,
        )

    state = deserialize_state(session.interview_state)
    phase = state["phase"]
    core_total = len(CORE_QUESTIONS)
    core_answered = core_total - len(state["core_questions_remaining"])
    # current_question is already popped from remaining, so subtract 1 if it's a core
    # question being displayed but not yet answered (follow-ups don't count)
    current = state.get("current_question")
    if phase == "core" and current and current.get("question_id", "").startswith("core_"):
        core_answered -= 1
    total_answered = len(state["answers"])

    if phase == "core":
        estimated_remaining = core_total - core_answered
    else:
        estimated_remaining = 0

    is_complete = phase in ("review", "complete")

    if is_complete and session.status != "interviewed":
        session.status = "interviewed"
        db.commit()

    return InterviewProgressResponse(
        phase=phase,
        total_answered=total_answered,
        core_answered=core_answered,
        core_total=core_total,
        estimated_remaining=estimated_remaining,
        is_complete=is_complete,
    )


@router.get("/{session_id}/interview/review")
async def get_interview_review(
    session_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Return a summary of all collected answers for user review."""
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.interview_state is None:
        raise HTTPException(status_code=400, detail="Interview not started")

    state = deserialize_state(session.interview_state)

    # Check if already confirmed (phase == "complete")
    confirmed = state["phase"] == "complete"

    return {
        "answers": session.interview_responses or [],
        "enrichment": session.enrichment_data or {},
        "confirmed": confirmed,
    }


@router.post("/{session_id}/interview/review")
async def confirm_interview_review(
    session_id: str,
    body: InterviewReviewRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Confirm the review, optionally add notes. Transition to complete."""
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.interview_state is None:
        raise HTTPException(status_code=400, detail="Interview not started")

    state = deserialize_state(session.interview_state)
    if state["phase"] not in ("review", "complete"):
        raise HTTPException(
            status_code=400,
            detail="Entrevista ainda não concluída. Finalize as perguntas antes de confirmar.",
        )

    # Store additional notes as a special entry in interview_responses
    if body.additional_notes and body.additional_notes.strip():
        responses = list(session.interview_responses or [])
        responses.append({
            "question_id": "review_notes",
            "answer": body.additional_notes.strip(),
            "source": "text",
        })
        session.interview_responses = responses

    state["phase"] = "complete"
    session.interview_state = serialize_state(state)
    if session.status != "interviewed":
        session.status = "interviewed"
    db.commit()

    return {
        "confirmed": True,
        "phase": "complete",
    }
