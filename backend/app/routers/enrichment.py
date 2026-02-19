"""Enrichment trigger and results endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import OnboardingSession
from app.models.schemas import CompanyProfile
from app.services.enrichment import extract_company_profile, scrape_website

router = APIRouter(prefix="/api/v1/sessions", tags=["enrichment"])


@router.post("/{session_id}/enrich")
async def enrich_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.enrichment_data is not None:
        raise HTTPException(status_code=409, detail="Session already enriched")

    session.status = "enriching"
    db.commit()

    website_text = await scrape_website(session.company_website)
    profile = await extract_company_profile(session.company_name, website_text)

    session.enrichment_data = profile.model_dump()
    session.status = "enriched"
    db.commit()

    return {"status": "enriched", "enrichment_data": profile.model_dump()}


@router.get("/{session_id}/enrichment", response_model=CompanyProfile)
async def get_enrichment(
    session_id: str,
    db: Session = Depends(get_db),
) -> CompanyProfile:
    session = db.get(OnboardingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.enrichment_data is None:
        raise HTTPException(status_code=404, detail="Session not enriched yet")

    return CompanyProfile(**session.enrichment_data)
