"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    company_name: str
    segment: str = ""
    products_description: str = ""
    target_audience: str = ""
    communication_tone: str = ""
    payment_methods_mentioned: str = ""
    collection_relevant_context: str = ""


class QuestionOption(BaseModel):
    value: str
    label: str


class SliderOptions(BaseModel):
    min: int
    max: int
    step: int
    unit: str
    default: int


class InterviewQuestion(BaseModel):
    question_id: str
    question_text: str
    question_type: Literal["text", "select", "multiselect", "slider"]
    options: list[QuestionOption] | SliderOptions | None = None
    pre_filled_value: str | None = None
    is_required: bool = True
    supports_audio: bool = True
    phase: Literal["core", "dynamic", "follow_up", "defaults"]
    context_hint: str | None = None


class SmartDefaults(BaseModel):
    contact_hours_weekday: str = "08:00-20:00"
    contact_hours_saturday: str = "08:00-14:00"
    contact_sunday: bool = False
    follow_up_interval_days: int = Field(default=3, ge=1)
    max_contact_attempts: int = Field(default=10, ge=1)
    use_first_name: bool = True
    identify_as_ai: bool = True
    min_installment_value: float = Field(default=50.0, ge=0)
    discount_strategy: Literal["only_when_resisted", "proactive", "escalating"] = "only_when_resisted"
    payment_link_generation: bool = True
    max_discount_installment_pct: float = Field(default=5.0, ge=0, le=50)


class CreateSessionRequest(BaseModel):
    company_name: str = Field(..., min_length=1)
    website: str = Field(..., min_length=1)
    cnpj: str | None = None


class SessionResponse(BaseModel):
    id: str
    status: str
    company_name: str
    company_website: str
    company_cnpj: str | None = None
    enrichment_data: dict[str, Any] | None = None
    interview_state: dict[str, Any] | None = None
    interview_responses: list[Any] | None = None
    smart_defaults: dict[str, Any] | None = None
    agent_config: dict[str, Any] | None = None
    simulation_result: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str
