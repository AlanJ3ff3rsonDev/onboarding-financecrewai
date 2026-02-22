"""Tests for agent generation prompt (T19), service (T20), and endpoints (T21)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from openai import OpenAIError

from app.prompts.agent_generator import SYSTEM_PROMPT, build_prompt
from app.services.agent_generator import (
    _apply_dotted_path_adjustments,
    _apply_sanity_checks,
    generate_agent_config,
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
            "question_id": "core_1",
            "question_text": "O que sua empresa vende ou oferece?",
            "answer": "Software de cobrança automatizada via WhatsApp",
            "source": "text",
        },
        {
            "question_id": "core_2",
            "question_text": "Como seus clientes normalmente pagam?",
            "answer": "pix,boleto,cartao_credito",
            "source": "text",
        },
        {
            "question_id": "core_3",
            "question_text": "Quando você considera uma conta vencida?",
            "answer": "d5",
            "source": "text",
        },
        {
            "question_id": "core_4",
            "question_text": "Descreva seu fluxo de cobrança atual",
            "answer": "Mandamos WhatsApp no D+5, ligamos no D+15, cobrança judicial no D+60",
            "source": "text",
        },
        {
            "question_id": "followup_core_4_1",
            "question_text": "Quantas pessoas trabalham na sua operação de cobrança?",
            "answer": "10 pessoas na operação",
            "source": "text",
        },
        {
            "question_id": "core_5",
            "question_text": "Qual tom o agente deve usar?",
            "answer": "amigavel_firme",
            "source": "text",
        },
        {
            "question_id": "core_6",
            "question_text": "Vocês oferecem desconto para pagamento? Se sim, como funciona?",
            "answer": "Oferecemos até 10% de desconto para pagamento à vista, apenas quando o devedor resiste",
            "source": "text",
        },
        {
            "question_id": "core_7",
            "question_text": "Vocês oferecem parcelamento? Se sim, como funciona?",
            "answer": "Parcelamos em até 12x, com parcela mínima de R$50",
            "source": "text",
        },
        {
            "question_id": "core_8",
            "question_text": "Vocês cobram juros por atraso? Se sim, como funciona o cálculo?",
            "answer": "Juros de 1% ao mês sobre o valor total da dívida",
            "source": "text",
        },
        {
            "question_id": "core_9",
            "question_text": "Vocês cobram multa por atraso? Se sim, como funciona?",
            "answer": "Multa de 2% sobre o valor da parcela vencida",
            "source": "text",
        },
        {
            "question_id": "core_10",
            "question_text": "Quando escalar para humano?",
            "answer": "solicita_humano,divida_alta,agressivo",
            "source": "text",
        },
        {
            "question_id": "core_11",
            "question_text": "O que nunca fazer/dizer?",
            "answer": "Nunca ameaçar, nunca mencionar SPC/Serasa, nunca ligar fora do horário",
            "source": "text",
        },
        {
            "question_id": "core_12",
            "question_text": "Razões comuns para não pagar?",
            "answer": "já paguei, não reconheço, não tenho dinheiro, vou pagar semana que vem",
            "source": "text",
        },
        {
            "question_id": "dynamic_1",
            "question_text": "Qual o ticket médio das dívidas cobradas?",
            "answer": "Entre R$500 e R$5.000",
            "source": "text",
        },
        {
            "question_id": "followup_dynamic_1_1",
            "question_text": "Há diferença de abordagem por faixa de valor?",
            "answer": "Sim, acima de R$2.000 oferecemos mais parcelas",
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
    assert "AgentConfig" in prompt
    # SYSTEM_PROMPT exists and is non-empty
    assert len(SYSTEM_PROMPT) > 100


def test_prompt_includes_all_sections():
    """Prompt includes all required sections and key interview answers."""
    prompt = build_prompt(
        _sample_company_profile(),
        _sample_interview_responses(),
    )

    # Section headings
    assert "Contexto da Empresa" in prompt
    assert "Modelo de Negócio" in prompt
    assert "Perfil do Devedor" in prompt
    assert "Processo de Cobrança" in prompt
    assert "Tom e Comunicação" in prompt
    assert "Políticas de Negociação" in prompt
    assert "Guardrails" in prompt
    assert "Cenários" in prompt

    # Key interview answers present
    assert "Software de cobrança automatizada" in prompt  # core_1
    assert "amigavel_firme" in prompt  # core_5
    assert "Nunca ameaçar" in prompt  # core_11
    assert "solicita_humano" in prompt  # core_10
    assert "já paguei" in prompt  # core_12

    # Financial policy answers (now text-based)
    assert "10% de desconto" in prompt  # core_6 text answer
    assert "12x" in prompt  # core_7 text answer

    # Follow-up answers included
    assert "10 pessoas na operação" in prompt  # followup_core_4_1

    # Dynamic questions included
    assert "ticket médio" in prompt  # dynamic_1
    assert "R$500" in prompt  # dynamic_1 answer
    assert "Aprofundamento" in prompt  # follow-up on dynamic_1

    # Mapping hints present
    assert "Dicas de Mapeamento" in prompt

    # JSON Schema present
    assert "Esquema JSON" in prompt
    assert "system_prompt" in prompt  # schema field


def test_prompt_handles_missing_data():
    """build_prompt works with None enrichment and empty responses."""
    # Completely empty inputs
    prompt = build_prompt(None, [])
    assert isinstance(prompt, str)
    assert len(prompt) > 100
    assert "AgentConfig" in prompt
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
# T20: Agent generation service tests
# ---------------------------------------------------------------------------

def _valid_agent_config_dict() -> dict:
    """A valid AgentConfig dict as the LLM would return it."""
    return {
        "agent_type": "compliant",
        "company_context": {
            "name": "CollectAI",
            "segment": "Tecnologia / Cobrança digital",
            "products": "Agentes de cobrança automatizados via WhatsApp",
            "target_audience": "Empresas B2B com carteira de inadimplentes",
        },
        "system_prompt": (
            "Você é um agente de cobrança virtual da CollectAI, especializado em "
            "recuperação de crédito para empresas B2B. Sua comunicação deve ser "
            "amigável, porém firme, sempre tratando o devedor pelo primeiro nome. "
            "Nunca ameace o devedor, nunca mencione SPC ou Serasa, e nunca entre "
            "em contato fora do horário comercial. Quando o devedor solicitar falar "
            "com um humano, apresentar dívida de alto valor, ou comportamento "
            "agressivo, escale imediatamente para um atendente humano. "
            "Ao negociar, ofereça desconto apenas quando houver resistência, "
            "até o máximo de 10% para pagamento integral. O parcelamento pode ser "
            "feito em até 12 vezes, com valor mínimo de R$50 por parcela. "
            "Aceite pagamentos via Pix, boleto ou cartão de crédito. "
            "Sempre se identifique como inteligência artificial no início da conversa."
        ),
        "tone": {
            "style": "friendly",
            "use_first_name": True,
            "prohibited_words": ["SPC", "Serasa", "processo", "ameaça"],
            "preferred_words": ["acordo", "solução", "facilidade"],
            "opening_message_template": (
                "Olá {nome}, aqui é a assistente virtual da CollectAI. "
                "Gostaria de conversar sobre uma pendência financeira."
            ),
        },
        "negotiation_policies": {
            "discount_policy": "Até 10% de desconto para pagamento à vista, apenas quando o devedor resiste",
            "installment_policy": "Parcelamento em até 12x, parcela mínima de R$50",
            "interest_policy": "Juros de 1% ao mês sobre o valor total",
            "penalty_policy": "Multa de 2% sobre o valor da parcela vencida",
            "payment_methods": ["pix", "boleto", "cartao_credito"],
            "can_generate_payment_link": True,
        },
        "guardrails": {
            "never_do": [
                "Ameaçar o devedor",
                "Contatar fora do horário comercial",
            ],
            "never_say": ["SPC", "Serasa", "processo judicial"],
            "escalation_triggers": [
                "Devedor solicita humano",
                "Dívida acima de R$5.000",
                "Comportamento agressivo",
            ],
            "follow_up_interval_days": 3,
            "max_attempts_before_stop": 10,
            "must_identify_as_ai": True,
        },
        "scenario_responses": {
            "already_paid": (
                "Entendo! Pode me enviar o comprovante de pagamento para "
                "que eu possa verificar e atualizar nosso sistema?"
            ),
            "dont_recognize_debt": (
                "Sem problemas. Vou encaminhar os detalhes da cobrança para "
                "que você possa verificar. Posso enviar por e-mail ou WhatsApp?"
            ),
            "cant_pay_now": (
                "Compreendo a situação. Podemos encontrar uma solução que "
                "caiba no seu orçamento. Que tal parcelarmos o valor?"
            ),
            "aggressive_debtor": (
                "Entendo sua frustração. Vou transferir você para um dos "
                "nossos especialistas que poderá ajudá-lo melhor."
            ),
        },
        "tools": [
            "send_whatsapp_message",
            "generate_pix_payment_link",
            "generate_boleto",
            "check_payment_status",
            "escalate_to_human",
            "schedule_follow_up",
        ],
        "metadata": {
            "version": 1,
            "generated_at": "2026-02-20T12:00:00+00:00",
            "onboarding_session_id": "test-session-123",
            "generation_model": "gpt-4.1-mini",
        },
    }


def _mock_openai_response(data: dict) -> MagicMock:
    """Build a mock OpenAI chat completion response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(data, ensure_ascii=False)
    return mock_response


@pytest.mark.asyncio
async def test_generate_agent_config():
    """generate_agent_config with valid LLM output returns AgentConfig."""
    config_dict = _valid_agent_config_dict()
    mock_response = _mock_openai_response(config_dict)

    with patch("app.services.agent_generator.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await generate_agent_config(
            _sample_company_profile(),
            _sample_interview_responses(),
            session_id="sess-001",
        )

    assert result.agent_type == "compliant"
    assert result.company_context.name == "CollectAI"
    assert len(result.system_prompt) >= 200
    assert result.tone.style == "friendly"
    assert result.negotiation_policies.discount_policy == "Até 10% de desconto para pagamento à vista, apenas quando o devedor resiste"
    assert result.metadata.onboarding_session_id == "sess-001"
    assert result.metadata.generation_model == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_sanity_check_system_prompt_quality():
    """Short system_prompt raises ValueError."""
    config_dict = _valid_agent_config_dict()
    config_dict["system_prompt"] = "Muito curto"  # < 200 chars
    mock_response = _mock_openai_response(config_dict)

    with patch("app.services.agent_generator.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="200"):
            await generate_agent_config(
                _sample_company_profile(),
                _sample_interview_responses(),
            )


@pytest.mark.asyncio
async def test_generate_retries_on_failure():
    """First LLM call fails, second succeeds → returns valid config."""
    config_dict = _valid_agent_config_dict()
    mock_response = _mock_openai_response(config_dict)

    with patch("app.services.agent_generator.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(
            side_effect=[OpenAIError("timeout"), mock_response]
        )

        result = await generate_agent_config(
            _sample_company_profile(),
            _sample_interview_responses(),
        )

    assert result.agent_type == "compliant"
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
            await generate_agent_config(
                _sample_company_profile(),
                _sample_interview_responses(),
            )


# ---------------------------------------------------------------------------
# T21: Agent generation endpoint tests
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


@patch("app.routers.agent.generate_agent_config", new_callable=AsyncMock)
def test_generate_agent_endpoint(
    mock_generate: AsyncMock,
    client: TestClient,
) -> None:
    """POST generate on interviewed session → 200, agent_config stored, status=generated."""
    from app.models.schemas import AgentConfig

    config = AgentConfig(**_valid_agent_config_dict())
    mock_generate.return_value = config

    session_id = _create_session(client)
    _set_session_interviewed(client, session_id)

    # POST generate
    resp = client.post(f"/api/v1/sessions/{session_id}/agent/generate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "generated"
    assert data["agent_config"]["company_context"]["name"] == "CollectAI"

    # GET agent returns stored config
    resp = client.get(f"/api/v1/sessions/{session_id}/agent")
    assert resp.status_code == 200
    assert resp.json()["company_context"]["name"] == "CollectAI"
    assert resp.json()["agent_type"] == "compliant"

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


@patch("app.routers.agent.generate_agent_config", new_callable=AsyncMock)
def test_regenerate_agent(
    mock_generate: AsyncMock,
    client: TestClient,
) -> None:
    """POST generate on already-generated session → succeeds (re-generation)."""
    from app.models.schemas import AgentConfig

    config = AgentConfig(**_valid_agent_config_dict())
    mock_generate.return_value = config

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
# T22: Agent adjustment endpoint tests
# ---------------------------------------------------------------------------


def _set_session_generated(client: TestClient, session_id: str) -> None:
    """Helper: fast-forward session to 'generated' status with stored agent_config."""
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
    session.agent_config = _valid_agent_config_dict()
    db.commit()
    db.close()


def test_apply_dotted_path_valid() -> None:
    """Valid dotted paths update nested dict correctly without mutating original."""
    config = _valid_agent_config_dict()
    original_style = config["tone"]["style"]

    updated, summary = _apply_dotted_path_adjustments(
        config,
        {
            "tone.style": "empathetic",
            "negotiation_policies.discount_policy": "Até 20% para pagamento à vista",
        },
    )

    assert updated["tone"]["style"] == "empathetic"
    assert updated["negotiation_policies"]["discount_policy"] == "Até 20% para pagamento à vista"
    # Original must not be mutated (deepcopy)
    assert config["tone"]["style"] == original_style
    assert len(summary) == 2


def test_apply_dotted_path_invalid() -> None:
    """Invalid dotted path raises ValueError."""
    config = _valid_agent_config_dict()
    with pytest.raises(ValueError, match="Caminho inválido"):
        _apply_dotted_path_adjustments(config, {"nonexistent.field": "x"})


@patch("app.routers.agent.adjust_agent_config", new_callable=AsyncMock)
def test_adjust_tone(
    mock_adjust: AsyncMock,
    client: TestClient,
) -> None:
    """PUT adjust with tone.style change → config returned with new tone."""
    from app.models.schemas import AgentConfig

    adjusted = _valid_agent_config_dict()
    adjusted["tone"]["style"] = "empathetic"
    adjusted["metadata"]["version"] = 2
    mock_adjust.return_value = AgentConfig(**adjusted)

    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"tone.style": "empathetic"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "adjusted"
    assert data["agent_config"]["tone"]["style"] == "empathetic"

    mock_adjust.assert_called_once()


@patch("app.routers.agent.adjust_agent_config", new_callable=AsyncMock)
def test_adjust_discount_policy(
    mock_adjust: AsyncMock,
    client: TestClient,
) -> None:
    """PUT adjust with discount_policy change → negotiation_policies updated."""
    from app.models.schemas import AgentConfig

    adjusted = _valid_agent_config_dict()
    adjusted["negotiation_policies"]["discount_policy"] = "Até 20% para pagamento à vista"
    adjusted["metadata"]["version"] = 2
    mock_adjust.return_value = AgentConfig(**adjusted)

    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"negotiation_policies.discount_policy": "Até 20% para pagamento à vista"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_config"]["negotiation_policies"]["discount_policy"] == "Até 20% para pagamento à vista"


@patch("app.routers.agent.adjust_agent_config", new_callable=AsyncMock)
def test_adjust_version_incremented(
    mock_adjust: AsyncMock,
    client: TestClient,
) -> None:
    """PUT adjust → version in returned config is 2."""
    from app.models.schemas import AgentConfig

    adjusted = _valid_agent_config_dict()
    adjusted["metadata"]["version"] = 2
    mock_adjust.return_value = AgentConfig(**adjusted)

    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"tone.style": "formal"}},
    )
    assert resp.status_code == 200
    assert resp.json()["agent_config"]["metadata"]["version"] == 2

    # GET agent also returns the updated version
    resp = client.get(f"/api/v1/sessions/{session_id}/agent")
    assert resp.status_code == 200
    assert resp.json()["metadata"]["version"] == 2


def test_adjust_before_generation(client: TestClient) -> None:
    """PUT adjust on session with no agent_config → 400."""
    session_id = _create_session(client)
    resp = client.put(
        f"/api/v1/sessions/{session_id}/agent/adjust",
        json={"adjustments": {"tone.style": "formal"}},
    )
    assert resp.status_code == 400
    assert "not generated yet" in resp.json()["detail"]


def test_adjust_session_not_found(client: TestClient) -> None:
    """PUT adjust on nonexistent session → 404."""
    resp = client.put(
        "/api/v1/sessions/nonexistent-id/agent/adjust",
        json={"adjustments": {"tone.style": "formal"}},
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
