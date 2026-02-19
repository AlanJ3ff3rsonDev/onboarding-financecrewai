"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    status: Mapped[str] = mapped_column(String(50), default="created")
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    company_website: Mapped[str] = mapped_column(Text, nullable=False)
    company_cnpj: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrichment_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interview_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interview_responses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    smart_defaults: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    agent_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    simulation_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
