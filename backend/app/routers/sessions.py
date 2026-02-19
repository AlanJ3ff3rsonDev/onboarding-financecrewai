"""Session creation and retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import CreateSessionRequest, CreateSessionResponse, SessionResponse

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=CreateSessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
) -> CreateSessionResponse:
    session = OnboardingSession(
        company_name=request.company_name,
        company_website=request.website,
        company_cnpj=request.cnpj,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return CreateSessionResponse(session_id=session.id, status=session.status)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionResponse:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.model_validate(session)
