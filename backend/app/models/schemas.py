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


class SubmitAnswerRequest(BaseModel):
    question_id: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    source: Literal["text", "audio"] = "text"


class InterviewProgressResponse(BaseModel):
    phase: str
    total_answered: int
    core_answered: int
    core_total: int
    dynamic_answered: int
    estimated_remaining: int
    is_complete: bool


class TranscriptionResponse(BaseModel):
    text: str
    duration_seconds: float


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


# --- AgentConfig schemas (T18) ---


class CompanyContext(BaseModel):
    name: str
    segment: str
    products: str
    target_audience: str


class ContactHours(BaseModel):
    weekday: str = Field(..., description="HH:MM-HH:MM format, e.g. '08:00-20:00'")
    saturday: str = Field(..., description="HH:MM-HH:MM format, e.g. '08:00-14:00'")
    sunday: str | None = Field(default=None, description="null if no Sunday contact")


class ToneConfig(BaseModel):
    style: Literal["formal", "friendly", "empathetic", "assertive"]
    use_first_name: bool
    prohibited_words: list[str] = Field(default_factory=list)
    preferred_words: list[str] = Field(default_factory=list)
    opening_message_template: str


class NegotiationPolicies(BaseModel):
    max_discount_full_payment_pct: float = Field(..., ge=0, le=100)
    max_discount_installment_pct: float = Field(..., ge=0, le=50)
    max_installments: int = Field(..., ge=0, le=48)
    min_installment_value_brl: float = Field(..., ge=0)
    discount_strategy: Literal["only_when_resisted", "proactive", "escalating"]
    payment_methods: list[str]
    can_generate_payment_link: bool


class Guardrails(BaseModel):
    never_do: list[str]
    never_say: list[str]
    escalation_triggers: list[str]
    contact_hours: ContactHours
    follow_up_interval_days: int = Field(..., ge=1)
    max_attempts_before_stop: int = Field(..., ge=1)
    must_identify_as_ai: bool


class ScenarioResponses(BaseModel):
    already_paid: str
    dont_recognize_debt: str
    cant_pay_now: str
    aggressive_debtor: str


class AgentMetadata(BaseModel):
    version: int = Field(default=1, ge=1)
    generated_at: str
    onboarding_session_id: str
    generation_model: str = "gpt-4.1-mini"


class AgentConfig(BaseModel):
    agent_type: Literal["compliant", "non_compliant"]
    company_context: CompanyContext
    system_prompt: str = Field(..., min_length=200)
    tone: ToneConfig
    negotiation_policies: NegotiationPolicies
    guardrails: Guardrails
    scenario_responses: ScenarioResponses
    tools: list[str]
    metadata: AgentMetadata
