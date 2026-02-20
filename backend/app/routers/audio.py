"""Audio upload and transcription endpoint."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import TranscriptionResponse
from app.services.transcription import transcribe_audio

router = APIRouter(prefix="/api/v1/sessions", tags=["audio"])


@router.post("/{session_id}/audio/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_endpoint(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> TranscriptionResponse:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    file_bytes = await file.read()
    content_type = file.content_type or ""

    try:
        result = await transcribe_audio(file_bytes, content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TranscriptionResponse(**result)
