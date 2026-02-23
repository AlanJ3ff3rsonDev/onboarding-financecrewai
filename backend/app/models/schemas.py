"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


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
    additional_notes: str | None = None


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


class ToneConfig(BaseModel):
    style: Literal["formal", "friendly", "empathetic", "assertive"]
    use_first_name: bool
    prohibited_words: list[str] = Field(default_factory=list)
    preferred_words: list[str] = Field(default_factory=list)
    opening_message_template: str


class NegotiationPolicies(BaseModel):
    discount_policy: str
    installment_policy: str
    interest_policy: str
    penalty_policy: str
    payment_methods: list[str]
    can_generate_payment_link: bool


class Guardrails(BaseModel):
    never_do: list[str]
    never_say: list[str]
    escalation_triggers: list[str]
    follow_up_interval_days: int = Field(default=3, ge=1)
    max_attempts_before_stop: int = Field(default=10, ge=1)
    must_identify_as_ai: bool = True


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
            "Example: {'tone.style': 'empathetic', "
            "'negotiation_policies.discount_policy': 'Até 20% para pagamento à vista'}"
        ),
    )
