"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.url_validation import validate_url_scheme


class WebResearchResult(BaseModel):
    company_description: str = ""
    products_and_services: str = ""
    sector_context: str = ""
    reputation_summary: str = ""
    collection_relevant_insights: str = ""


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
    phase: Literal["core", "dynamic", "follow_up", "review"]
    context_hint: str | None = None


class InterviewReviewRequest(BaseModel):
    confirmed: bool = True
    additional_notes: str | None = Field(None, max_length=5000)


class SubmitAnswerRequest(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=100)
    answer: str = Field(..., min_length=1, max_length=10000)
    source: Literal["text", "audio"] = "text"


class InterviewProgressResponse(BaseModel):
    phase: str
    total_answered: int
    core_answered: int
    core_total: int
    estimated_remaining: int
    is_complete: bool


class TranscriptionResponse(BaseModel):
    text: str
    duration_seconds: float


class CreateSessionRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)
    website: str = Field(..., min_length=1, max_length=2000)
    cnpj: str | None = Field(None, max_length=20)

    @field_validator("website")
    @classmethod
    def validate_website_url(cls, v: str) -> str:
        return validate_url_scheme(v)


class SessionResponse(BaseModel):
    id: str
    status: str
    company_name: str
    company_website: str
    company_cnpj: str | None = None
    enrichment_data: dict[str, Any] | None = None
    interview_state: dict[str, Any] | None = None
    interview_responses: list[Any] | None = None
    agent_config: dict[str, Any] | None = None
    simulation_result: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str


# --- OnboardingReport schemas (replaces AgentConfig) ---


class AgentIdentity(BaseModel):
    name: str = ""


class ReportCompany(BaseModel):
    name: str
    segment: str = ""
    products: str = ""
    target_audience: str = ""
    website: str = ""


class EnrichmentSummary(BaseModel):
    website_analysis: str = ""
    web_research: str = ""


class CollectionProfile(BaseModel):
    debt_type: str = ""
    typical_debtor_profile: str = ""
    business_specific_objections: str = ""
    payment_verification_process: str = ""
    sector_regulations: str = ""


class CollectionPolicies(BaseModel):
    overdue_definition: str = ""
    discount_policy: str = ""
    installment_policy: str = ""
    interest_policy: str = ""
    penalty_policy: str = ""
    payment_methods: list[str] = Field(default_factory=list)
    escalation_triggers: list[str] = Field(default_factory=list)
    escalation_custom_rules: str = ""
    collection_flow_description: str = ""


class Communication(BaseModel):
    tone_style: Literal["formal", "friendly", "empathetic", "assertive"] = "friendly"
    prohibited_actions: list[str] = Field(default_factory=list)
    brand_specific_language: str = ""


class ReportGuardrails(BaseModel):
    never_do: list[str] = Field(default_factory=list)
    never_say: list[str] = Field(default_factory=list)
    must_identify_as_ai: bool = True
    follow_up_interval_days: int = Field(default=3, ge=1)
    max_attempts_before_stop: int = Field(default=10, ge=1)


class ReportMetadata(BaseModel):
    generated_at: str = ""
    session_id: str = ""
    model: str = "gpt-4.1-mini"
    version: int = Field(default=1, ge=1)


class OnboardingReport(BaseModel):
    agent_identity: AgentIdentity = Field(default_factory=AgentIdentity)
    company: ReportCompany
    enrichment_summary: EnrichmentSummary = Field(default_factory=EnrichmentSummary)
    collection_profile: CollectionProfile = Field(default_factory=CollectionProfile)
    collection_policies: CollectionPolicies = Field(default_factory=CollectionPolicies)
    communication: Communication = Field(default_factory=Communication)
    guardrails: ReportGuardrails = Field(default_factory=ReportGuardrails)
    expert_recommendations: str = Field(..., min_length=200)
    metadata: ReportMetadata = Field(default_factory=ReportMetadata)


# --- SimulationResult schemas (T23) ---


class SimulationMessage(BaseModel):
    role: Literal["agent", "debtor"]
    content: str


class SimulationMetrics(BaseModel):
    negotiated_discount_pct: float | None = None
    final_installments: int | None = None
    payment_method: str | None = None
    resolution: Literal[
        "full_payment", "installment_plan", "escalated", "no_resolution"
    ]


class SimulationScenario(BaseModel):
    scenario_type: Literal["cooperative", "resistant"]
    debtor_profile: str
    conversation: list[SimulationMessage]
    outcome: str
    metrics: SimulationMetrics


class SimulationResult(BaseModel):
    scenarios: list[SimulationScenario]
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentAdjustRequest(BaseModel):
    adjustments: dict[str, Any] = Field(
        ...,
        min_length=1,
        description=(
            "Flat dict of dotted-path keys to new values. "
            "Example: {'communication.tone_style': 'empathetic', "
            "'collection_policies.discount_policy': 'Até 20% para pagamento à vista'}"
        ),
    )
