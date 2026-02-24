"""Tests for onboarding report generation prompt, service, and endpoints."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

from app.prompts.agent_generator import SYSTEM_PROMPT, build_prompt
from app.services.agent_generator import (
    _apply_dotted_path_adjustments,
    _apply_sanity_checks,
    generate_onboarding_report,
)


def _sample_company_profile() -> dict:
    return {
        "company_name": "CollectAI",
        "segment": "Tecnologia / Cobrança digital",
        "products_description": "Agentes de cobrança automatizados via WhatsApp",
        "target_audience": "Empresas B2B com carteira de inadimplentes",
        "communication_tone": "profissional e empático",
        "payment_methods_mentioned": "Pix, boleto",
        "collection_relevant_context": "SaaS de cobrança com agentes virtuais",
    }


def _sample_interview_responses() -> list[dict]:
    return [
        {
            "question_id": "core_0",
            "question_text": "Quer dar um nome ao seu agente de cobrança?",
            "answer": "Sofia",
            "source": "text",
        },
        {
            "question_id": "core_1",
            "question_text": "Como funciona o processo de cobrança na sua empresa hoje?",
            "answer": "Mandamos WhatsApp no D+5, ligamos no D+15, cobrança judicial no D+60",
            "source": "text",
        },
        {
            "question_id": "followup_core_1_1",
            "question_text": "Quantas pessoas trabalham na sua operação de cobrança?",
            "answer": "10 pessoas na operação",
            "source": "text",
        },
        {
            "question_id": "core_2",
            "question_text": "Vocês cobram juros por atraso?",
            "answer": "sim",
            "source": "text",
        },
        {
            "question_id": "followup_core_2_1",
            "question_text": "Como funciona a cobrança de juros?",
            "answer": "1% ao mês sobre o valor total",
            "source": "text",
        },
        {
            "question_id": "core_3",
            "question_text": "Vocês oferecem desconto para pagamento?",
            "answer": "sim",
            "source": "text",
        },
        {
            "question_id": "followup_core_3_1",
            "question_text": "Como funciona o desconto?",
            "answer": "Até 10% para pagamento à vista",
            "source": "text",
        },
        {
            "question_id": "core_4",
            "question_text": "Vocês permitem parcelamento da dívida?",
            "answer": "sim",
            "source": "text",
        },
        {
            "question_id": "followup_core_4_1",
            "question_text": "Como funciona o parcelamento?",
            "answer": "Até 12x, parcela mínima de R$50",
            "source": "text",
        },
        {
            "question_id": "core_5",
            "question_text": "Vocês cobram multa por atraso?",
            "answer": "sim",
            "source": "text",
        },
        {
            "question_id": "followup_core_5_1",
            "question_text": "Como funciona a multa?",
            "answer": "2% sobre o valor da parcela vencida",
            "source": "text",
        },
        {
            "question_id": "core_6",
            "question_text": "Tem alguma situação específica em que o agente deve passar a conversa para um atendente humano?",
            "answer": "Quando o cliente e uma empresa parceira estrategica, devemos escalar para o gerente comercial.",
            "source": "text",
        },
    ]


def test_build_prompt():
    """build_prompt with complete data returns a substantial prompt string."""
    prompt = build_prompt(
        _sample_company_profile(),
        _sample_interview_responses(),
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 500
    assert "CollectAI" in prompt
    assert "OnboardingReport" in prompt
    # SYSTEM_PROMPT exists and is non-empty
    assert len(SYSTEM_PROMPT) > 100


def test_prompt_includes_all_sections():
    """Prompt includes all required sections and key interview answers."""
    prompt = build_prompt(
        _sample_company_profile(),
        _sample_interview_responses(),
    )

    # Section 0: Agent identity
    assert "Identidade do Agente" in prompt
    assert "Sofia" in prompt

    # Section headings
    assert "Contexto da Empresa" in prompt
    assert "Modelo de Negócio" in prompt
    assert "Processo de Cobrança" in prompt
    assert "Tom e Comunicação" in prompt
    assert "Políticas de Negociação" in prompt
    assert "Guardrails" in prompt

    # Key interview answers present
    assert "WhatsApp no D+5" in prompt  # core_1 (collection process)
    assert "Juros por atraso" in prompt  # core_2 policy
    assert "Desconto para pagamento" in prompt  # core_3 policy
    assert "Parcelamento" in prompt  # core_4 policy
    assert "Multa por atraso" in prompt  # core_5 policy

    # Default guardrails present
    assert "Nunca ameaçar" in prompt
    assert "Devedor agressivo" in prompt  # default escalation trigger

    # Client-specified escalation (core_6)
    assert "empresa parceira estrategica" in prompt

    # Follow-up answers included
    assert "10 pessoas na operação" in prompt  # followup_core_1_1

    # Mapping hints present
    assert "Dicas de Mapeamento" in prompt

    # JSON Schema present
    assert "Esquema JSON" in prompt
    assert "OnboardingReport" in prompt  # schema reference


def test_prompt_skips_agent_identity_when_declined():
    """When core_0 answer is 'nao', the agent identity section is omitted."""
    responses = _sample_interview_responses()
    # Change core_0 answer to "nao"
    responses[0]["answer"] = "nao"
    prompt = build_prompt(_sample_company_profile(), responses)
    assert "Identidade do Agente" not in prompt


def test_prompt_handles_missing_data():
    """build_prompt works with None enrichment and empty responses."""
    # Completely empty inputs
    prompt = build_prompt(None, [])
    assert isinstance(prompt, str)
    assert len(prompt) > 100
    assert "OnboardingReport" in prompt
    assert "Nenhum dado de enriquecimento" in prompt
    assert "Não respondida" in prompt

    # Partial data: just company_name and 1 answer
    prompt2 = build_prompt(
        {"company_name": "TestCorp"},
        [
            {
                "question_id": "core_1",
                "question_text": "Produtos?",
                "answer": "Roupas femininas",
                "source": "text",
            }
        ],
    )
    assert "TestCorp" in prompt2
    assert "Roupas femininas" in prompt2
    # Other core answers should show as not answered
    assert "Não respondida" in prompt2


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

def _valid_report_dict() -> dict:
    """A valid OnboardingReport dict as the LLM would return it."""
    return {
        "agent_identity": {"name": "Sofia"},
        "company": {
            "name": "CollectAI",
            "segment": "Tecnologia / Cobrança digital",
            "products": "Agentes de cobrança automatizados via WhatsApp",
            "target_audience": "Empresas B2B com carteira de inadimplentes",
            "website": "https://collectai.com.br",
        },
        "enrichment_summary": {
            "website_analysis": "Empresa de tecnologia focada em cobrança digital.",
            "web_research": "Líder em automação de cobrança no Brasil.",
        },
        "collection_profile": {
            "debt_type": "Inadimplência B2B",
            "typical_debtor_profile": "Empresas com atraso de 30-90 dias",
            "business_specific_objections": "Contestação de valores",
            "payment_verification_process": "Integração bancária automática",
            "sector_regulations": "CDC, LGPD, BACEN",
        },
        "collection_policies": {
            "overdue_definition": "A partir de 5 dias após vencimento",
            "discount_policy": "Até 10% de desconto para pagamento à vista",
            "installment_policy": "Parcelamento em até 12x, parcela mínima de R$50",
            "interest_policy": "Juros de 1% ao mês sobre o valor total",
            "penalty_policy": "Multa de 2% sobre o valor da parcela vencida",
            "payment_methods": ["pix", "boleto", "cartao_credito"],
            "escalation_triggers": [
                "Devedor solicita humano",
                "Dívida acima de R$5.000",
                "Comportamento agressivo",
            ],
            "escalation_custom_rules": "Escalar para gerente comercial se parceiro estratégico",
            "collection_flow_description": "D+5 WhatsApp, D+15 ligação, D+60 jurídico",
        },
        "communication": {
            "tone_style": "friendly",
            "prohibited_actions": ["Ameaçar o devedor", "Cobrar fora do horário"],
            "brand_specific_language": "Usar 'pendência' em vez de 'dívida'",
        },
        "guardrails": {
            "never_do": [
                "Ameaçar o devedor",
                "Contatar fora do horário comercial",
            ],
            "never_say": ["SPC", "Serasa", "processo judicial"],
            "must_identify_as_ai": True,
            "follow_up_interval_days": 3,
            "max_attempts_before_stop": 10,
        },
        "expert_recommendations": (
            "A CollectAI atua no segmento de cobrança digital B2B, atendendo empresas "
            "de médio porte com carteiras de inadimplentes. Recomenda-se adotar um tom "
            "amigável mas firme nas comunicações, priorizando a resolução amigável. "
            "O fluxo de cobrança deve começar com contato via WhatsApp no D+5, seguido "
            "de ligação no D+15 e encaminhamento jurídico no D+60. É fundamental "
            "respeitar as normas do CDC e LGPD em todas as interações. Para o segmento "
            "de tecnologia B2B, as principais objeções são contestação de valores e "
            "alegação de não recebimento do serviço. Recomenda-se ter processos claros "
            "de verificação de pagamento via integração bancária."
        ),
        "metadata": {
            "version": 1,
            "generated_at": "2026-02-20T12:00:00+00:00",
            "session_id": "test-session-123",
            "model": "gpt-4.1-mini",
        },
    }


def _mock_openai_response(data: dict) -> MagicMock:
    """Build a mock OpenAI chat completion response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(data, ensure_ascii=False)
    return mock_response


@pytest.mark.asyncio
async def test_generate_onboarding_report():
    """generate_onboarding_report with valid LLM output returns OnboardingReport."""
    report_dict = _valid_report_dict()
    mock_response = _mock_openai_response(report_dict)

    with patch("app.services.agent_generator.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await generate_onboarding_report(
            _sample_company_profile(),
            _sample_interview_responses(),
            session_id="sess-001",
        )

    assert result.company.name == "CollectAI"
    assert len(result.expert_recommendations) >= 200
    assert result.communication.tone_style == "friendly"
    assert result.collection_policies.discount_policy == "Até 10% de desconto para pagamento à vista"
    assert result.metadata.session_id == "sess-001"
    assert result.metadata.model == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_sanity_check_expert_recommendations_quality():
    """Short expert_recommendations raises ValueError."""
    report_dict = _valid_report_dict()
    report_dict["expert_recommendations"] = "Muito curto"  # < 200 chars
    mock_response = _mock_openai_response(report_dict)

    with patch("app.services.agent_generator.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="200"):
            await generate_onboarding_report(
                _sample_company_profile(),
                _sample_interview_responses(),
            )


@pytest.mark.asyncio
async def test_generate_retries_on_failure():
    """First LLM call fails, second succeeds → returns valid report."""
    report_dict = _valid_report_dict()
    mock_response = _mock_openai_response(report_dict)

    with patch("app.services.agent_generator.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(
            side_effect=[OpenAIError("timeout"), mock_response]
        )

        result = await generate_onboarding_report(
            _sample_company_profile(),
            _sample_interview_responses(),
        )

    assert result.company.name == "CollectAI"
    assert instance.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_generate_both_attempts_fail():
    """Both LLM calls fail → raises ValueError."""
    with patch("app.services.agent_generator.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(
            side_effect=[OpenAIError("fail 1"), OpenAIError("fail 2")]
        )

        with pytest.raises(ValueError, match="2 tentativas"):
            await generate_onboarding_report(
                _sample_company_profile(),
                _sample_interview_responses(),
            )


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


def _create_session(client: TestClient) -> str:
    """Helper: create a session and return its ID."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://testcorp.com"},
    )
    return resp.json()["session_id"]


def _set_session_interviewed(client: TestClient, session_id: str) -> None:
    """Helper: fast-forward session to 'interviewed' status with required data."""
    from app.database import get_db
    from app.main import app
    from app.models.orm import OnboardingSession

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    session = db.get(OnboardingSession, session_id)
    session.status = "interviewed"
    session.enrichment_data = _sample_company_profile()
    session.interview_responses = _sample_interview_responses()
    session.interview_state = {"phase": "complete"}
    db.commit()
    db.close()


@patch("app.routers.agent.generate_onboarding_report", new_callable=AsyncMock)
def test_generate_agent_endpoint(
    mock_generate: AsyncMock,
    client: TestClient,
) -> None:
    """POST generate on interviewed session → 200, report stored, status=generated."""
    from app.models.schemas import OnboardingReport

    report = OnboardingReport(**_valid_report_dict())
    mock_generate.return_value = report

    session_id = _create_session(client)
    _set_session_interviewed(client, session_id)

    # POST generate
    resp = client.post(f"/api/v1/sessions/{session_id}/agent/generate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "generated"
    assert data["onboarding_report"]["company"]["name"] == "CollectAI"

    # GET agent returns stored report
    resp = client.get(f"/api/v1/sessions/{session_id}/agent")
    assert resp.status_code == 200
    assert resp.json()["company"]["name"] == "CollectAI"
    assert resp.json()["communication"]["tone_style"] == "friendly"

    # Session status is now "generated"
    resp = client.get(f"/api/v1/sessions/{session_id}")
    assert resp.json()["status"] == "generated"


def test_generate_before_interview(client: TestClient) -> None:
    """POST generate on a non-interviewed session → 400."""
    session_id = _create_session(client)
    resp = client.post(f"/api/v1/sessions/{session_id}/agent/generate")
    assert resp.status_code == 400
    assert "Interview must be completed" in resp.json()["detail"]


def test_get_agent_not_generated(client: TestClient) -> None:
    """GET agent before generation → 404."""
    session_id = _create_session(client)
    resp = client.get(f"/api/v1/sessions/{session_id}/agent")
    assert resp.status_code == 404
    assert "not generated" in resp.json()["detail"]


def test_generate_session_not_found(client: TestClient) -> None:
    """POST generate on nonexistent session → 404."""
    resp = client.post("/api/v1/sessions/nonexistent-id/agent/generate")
    assert resp.status_code == 404


def test_get_agent_session_not_found(client: TestClient) -> None:
    """GET agent on nonexistent session → 404."""
    resp = client.get("/api/v1/sessions/nonexistent-id/agent")
    assert resp.status_code == 404


@patch("app.routers.agent.generate_onboarding_report", new_callable=AsyncMock)
def test_regenerate_agent(
    mock_generate: AsyncMock,
    client: TestClient,
) -> None:
    """POST generate on already-generated session → succeeds (re-generation)."""
    from app.models.schemas import OnboardingReport

    report = OnboardingReport(**_valid_report_dict())
    mock_generate.return_value = report

    session_id = _create_session(client)
    _set_session_interviewed(client, session_id)

    # First generation
    resp = client.post(f"/api/v1/sessions/{session_id}/agent/generate")
    assert resp.status_code == 200

    # Re-generation should also succeed (status is "generated", which is allowed)
    resp = client.post(f"/api/v1/sessions/{session_id}/agent/generate")
    assert resp.status_code == 200
    assert mock_generate.call_count == 2


# ---------------------------------------------------------------------------
# Adjustment endpoint tests
# ---------------------------------------------------------------------------


def _set_session_generated(client: TestClient, session_id: str) -> None:
    """Helper: fast-forward session to 'generated' status with stored report."""
    from app.database import get_db
    from app.main import app
    from app.models.orm import OnboardingSession

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    session = db.get(OnboardingSession, session_id)
    session.status = "generated"
    session.enrichment_data = _sample_company_profile()
    session.interview_responses = _sample_interview_responses()
    session.interview_state = {"phase": "complete"}
    session.agent_config = _valid_report_dict()
    db.commit()
    db.close()


def test_apply_dotted_path_valid() -> None:
    """Valid dotted paths update nested dict correctly without mutating original."""
    report = _valid_report_dict()
    original_style = report["communication"]["tone_style"]

    updated, summary = _apply_dotted_path_adjustments(
        report,
        {
            "communication.tone_style": "empathetic",
            "collection_policies.discount_policy": "Até 20% para pagamento à vista",
        },
    )

    assert updated["communication"]["tone_style"] == "empathetic"
    assert updated["collection_policies"]["discount_policy"] == "Até 20% para pagamento à vista"
    # Original must not be mutated (deepcopy)
    assert report["communication"]["tone_style"] == original_style
    assert len(summary) == 2


def test_apply_dotted_path_invalid() -> None:
    """Invalid dotted path raises ValueError."""
    report = _valid_report_dict()
    with pytest.raises(ValueError, match="Caminho inválido"):
        _apply_dotted_path_adjustments(report, {"nonexistent.field": "x"})


@patch("app.routers.agent.adjust_onboarding_report", new_callable=AsyncMock)
def test_adjust_tone(
    mock_adjust: AsyncMock,
    client: TestClient,
) -> None:
    """PUT adjust with tone_style change → report returned with new tone."""
    from app.models.schemas import OnboardingReport

    adjusted = _valid_report_dict()
    adjusted["communication"]["tone_style"] = "empathetic"
    adjusted["metadata"]["version"] = 2
    mock_adjust.return_value = OnboardingReport(**adjusted)

    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"communication.tone_style": "empathetic"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "adjusted"
    assert data["onboarding_report"]["communication"]["tone_style"] == "empathetic"

    mock_adjust.assert_called_once()


@patch("app.routers.agent.adjust_onboarding_report", new_callable=AsyncMock)
def test_adjust_discount_policy(
    mock_adjust: AsyncMock,
    client: TestClient,
) -> None:
    """PUT adjust with discount_policy change → collection_policies updated."""
    from app.models.schemas import OnboardingReport

    adjusted = _valid_report_dict()
    adjusted["collection_policies"]["discount_policy"] = "Até 20% para pagamento à vista"
    adjusted["metadata"]["version"] = 2
    mock_adjust.return_value = OnboardingReport(**adjusted)

    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"collection_policies.discount_policy": "Até 20% para pagamento à vista"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarding_report"]["collection_policies"]["discount_policy"] == "Até 20% para pagamento à vista"


@patch("app.routers.agent.adjust_onboarding_report", new_callable=AsyncMock)
def test_adjust_version_incremented(
    mock_adjust: AsyncMock,
    client: TestClient,
) -> None:
    """PUT adjust → version in returned report is 2."""
    from app.models.schemas import OnboardingReport

    adjusted = _valid_report_dict()
    adjusted["metadata"]["version"] = 2
    mock_adjust.return_value = OnboardingReport(**adjusted)

    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"communication.tone_style": "formal"}},
    )
    assert resp.status_code == 200
    assert resp.json()["onboarding_report"]["metadata"]["version"] == 2

    # GET agent also returns the updated version
    resp = client.get(f"/api/v1/sessions/{session_id}/agent")
    assert resp.status_code == 200
    assert resp.json()["metadata"]["version"] == 2


def test_adjust_before_generation(client: TestClient) -> None:
    """PUT adjust on session with no agent_config → 400."""
    session_id = _create_session(client)
    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"communication.tone_style": "formal"}},
    )
    assert resp.status_code == 400
    assert "not generated yet" in resp.json()["detail"]


def test_adjust_session_not_found(client: TestClient) -> None:
    """PUT adjust on nonexistent session → 404."""
    resp = client.put(
        "/api/v1/sessions/nonexistent-id/agent/adjust",
        json={"adjustments": {"communication.tone_style": "formal"}},
    )
    assert resp.status_code == 404


def test_adjust_invalid_path(client: TestClient) -> None:
    """PUT adjust with invalid dotted path → 400."""
    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"nonexistent_section.field": "value"}},
    )
    assert resp.status_code == 400
    assert "Caminho inválido" in resp.json()["detail"]


def test_adjust_empty_adjustments(client: TestClient) -> None:
    """PUT adjust with empty adjustments → 422 (Pydantic min_length=1)."""
    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {}},
    )
    assert resp.status_code == 422
