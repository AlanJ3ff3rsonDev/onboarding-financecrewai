"""Agent generation, retrieval, and avatar upload endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import AgentAdjustRequest, AgentConfig
from app.services.agent_generator import adjust_agent_config, generate_agent_config

ALLOWED_AVATAR_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "avatars"

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
        config = await adjust_agent_config(
            current_config=session.agent_config,
            adjustments=request.adjustments,
            session_id=session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session.agent_config = config.model_dump()
    db.commit()

    return {"status": "adjusted", "agent_config": config.model_dump()}


@router.post("/{session_id}/agent/avatar/upload")
async def upload_avatar(
    session_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Use PNG, JPG ou WebP.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Arquivo excede o limite de 5 MB.",
        )

    ext = ALLOWED_AVATAR_TYPES[content_type]
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOADS_DIR / f"{session_id}.{ext}"

    # Remove previous avatar if exists with a different extension
    for old_file in UPLOADS_DIR.glob(f"{session_id}.*"):
        old_file.unlink()

    file_path.write_bytes(file_bytes)

    avatar_url = f"/uploads/avatars/{session_id}.{ext}"
    session.agent_avatar_path = avatar_url
    db.commit()

    return {"avatar_url": avatar_url}
