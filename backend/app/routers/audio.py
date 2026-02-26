"""Audio upload and transcription endpoint."""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.models.orm import OnboardingSession
from app.models.schemas import TranscriptionResponse
from app.services.transcription import transcribe_audio

router = APIRouter(prefix="/api/v1/sessions", tags=["audio"])


@router.post("/{session_id}/audio/transcribe", response_model=TranscriptionResponse)
@limiter.limit("5/minute")
async def transcribe_audio_endpoint(
    request: Request,
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> TranscriptionResponse:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    max_size = 25 * 1024 * 1024  # 25 MB
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(8192):
        total += len(chunk)
        if total > max_size:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 25 MB.")
        chunks.append(chunk)
    file_bytes = b"".join(chunks)
    content_type = file.content_type or ""

    try:
        result = await transcribe_audio(file_bytes, content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TranscriptionResponse(**result)
