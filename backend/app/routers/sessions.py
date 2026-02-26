"""Session creation and retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.models.orm import OnboardingSession
from app.models.schemas import CreateSessionRequest, CreateSessionResponse, SessionPublicResponse

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=CreateSessionResponse, status_code=201)
@limiter.limit("60/minute")
async def create_session(
    request: Request,
    body: CreateSessionRequest,
    db: Session = Depends(get_db),
) -> CreateSessionResponse:
    session = OnboardingSession(
        company_name=body.company_name,
        company_website=body.website,
        company_cnpj=body.cnpj,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return CreateSessionResponse(session_id=session.id, status=session.status)


@router.get("/{session_id}", response_model=SessionPublicResponse)
@limiter.limit("60/minute")
async def get_session(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionPublicResponse:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionPublicResponse.model_validate(session)
