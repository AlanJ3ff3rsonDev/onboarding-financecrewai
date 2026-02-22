"""Tests for simulation prompt + service (T23) and endpoints (T24)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models.schemas import (
    AgentConfig,
    AgentMetadata,
    CompanyContext,
    Guardrails,
    NegotiationPolicies,
    ScenarioResponses,
    SimulationMessage,
    SimulationMetrics,
    SimulationResult,
    SimulationScenario,
    ToneConfig,
)
from app.prompts.simulation import build_simulation_prompt
from app.services.simulation import generate_simulation


def _valid_agent_config() -> AgentConfig:
    """Build a complete, valid AgentConfig for testing."""
    return AgentConfig(
        agent_type="compliant",
        company_context=CompanyContext(
            name="CollectAI",
            segment="Cobrança digital",
            products="Agente de cobrança automatizado via WhatsApp",
            target_audience="Empresas de médio porte com carteira de inadimplentes",
        ),
        system_prompt=(
            "Você é um agente de cobrança digital da CollectAI. "
            "Sua função é negociar dívidas de forma empática e eficiente, "
            "respeitando os limites de desconto e parcelamento configurados. "
            "Sempre se identifique como assistente virtual. "
            "Nunca ameace o devedor ou use linguagem agressiva. "
            "Ofereça opções de pagamento via PIX ou boleto. "
            "Se o devedor ficar agressivo, encerre a conversa educadamente. "
            "Horário de contato: segunda a sexta 08:00-20:00, sábado 08:00-14:00."
        ),
        tone=ToneConfig(
            style="empathetic",
            use_first_name=True,
            prohibited_words=["dívida", "devedor", "inadimplente"],
            preferred_words=["pendência", "valor em aberto", "regularização"],
            opening_message_template=(
                "Olá {first_name}, aqui é a assistente virtual da CollectAI. "
                "Gostaria de conversar sobre uma pendência financeira."
            ),
        ),
        negotiation_policies=NegotiationPolicies(
            discount_policy="Até 10% de desconto para pagamento à vista, apenas quando o devedor resiste",
            installment_policy="Parcelamento em até 12x, parcela mínima de R$50",
            interest_policy="Juros de 1% ao mês sobre o valor total",
            penalty_policy="Multa de 2% sobre o valor da parcela vencida",
            payment_methods=["pix", "boleto"],
            can_generate_payment_link=True,
        ),
        guardrails=Guardrails(
            never_do=[
                "Ameaçar o devedor",
                "Compartilhar dados com terceiros",
            ],
            never_say=["processo", "SPC", "Serasa", "nome sujo"],
            escalation_triggers=[
                "solicita_humano",
                "divida_alta",
                "agressivo",
            ],
            follow_up_interval_days=3,
            max_attempts_before_stop=10,
            must_identify_as_ai=True,
        ),
        scenario_responses=ScenarioResponses(
            already_paid="Peço desculpas. Pode enviar o comprovante?",
            dont_recognize_debt="Entendo. Vou encaminhar para verificação.",
            cant_pay_now="Podemos encontrar uma opção de parcelamento.",
            aggressive_debtor="Entendo sua frustração. Vou encerrar por aqui.",
        ),
        tools=["send_whatsapp_message", "generate_pix_payment_link", "generate_boleto"],
        metadata=AgentMetadata(
            version=1,
            generated_at="2026-02-20T12:00:00Z",
            onboarding_session_id="test-session-123",
            generation_model="gpt-4.1-mini",
        ),
    )


def _mock_simulation_response() -> dict:
    """Build a valid SimulationResult dict for mocking LLM responses."""
    return {
        "scenarios": [
            {
                "scenario_type": "cooperative",
                "debtor_profile": "Maria Silva, 35 anos, professora, dívida de R$1.500",
                "conversation": [
                    {"role": "agent", "content": "Olá Maria, aqui é a assistente virtual da CollectAI."},
                    {"role": "debtor", "content": "Oi, sobre o que é?"},
                    {"role": "agent", "content": "Gostaria de conversar sobre uma pendência de R$1.500."},
                    {"role": "debtor", "content": "Ah sim, eu sei. Posso pagar, mas preciso de um desconto."},
                    {"role": "agent", "content": "Posso oferecer 10% de desconto para pagamento à vista."},
                    {"role": "debtor", "content": "Fechado! Como faço para pagar?"},
                    {"role": "agent", "content": "Vou gerar um link PIX para R$1.350. Um momento."},
                    {"role": "debtor", "content": "Ok, recebi. Vou pagar agora."},
                    {"role": "agent", "content": "Obrigada, Maria! Fico à disposição."},
                ],
                "outcome": "Devedor aceitou desconto de 10% e pagou via PIX.",
                "metrics": {
                    "negotiated_discount_pct": 10.0,
                    "final_installments": None,
                    "payment_method": "pix",
                    "resolution": "full_payment",
                },
            },
            {
                "scenario_type": "resistant",
                "debtor_profile": "João Pereira, 42 anos, autônomo, dívida de R$3.000",
                "conversation": [
                    {"role": "agent", "content": "Olá João, aqui é a assistente virtual da CollectAI."},
                    {"role": "debtor", "content": "Não conheço essa empresa."},
                    {"role": "agent", "content": "Entendo. Vou encaminhar para nossa equipe verificar."},
                    {"role": "debtor", "content": "Não devo nada! Parem de me ligar!"},
                    {"role": "agent", "content": "Entendo sua frustração. Posso verificar os detalhes."},
                    {"role": "debtor", "content": "Vou processar vocês!"},
                    {"role": "agent", "content": "Entendo sua frustração. Vou encaminhar para um atendente."},
                    {"role": "debtor", "content": "Finalmente algo útil."},
                    {"role": "agent", "content": "Um atendente entrará em contato em breve. Obrigado."},
                ],
                "outcome": "Devedor agressivo, conversa escalada para atendente humano.",
                "metrics": {
                    "negotiated_discount_pct": None,
                    "final_installments": None,
                    "payment_method": None,
                    "resolution": "escalated",
                },
            },
        ],
    }


# --- Prompt Tests ---


def test_build_simulation_prompt():
    """Prompt should include company name, tone, policy descriptions, guardrails, and schema."""
    config = _valid_agent_config()
    prompt = build_simulation_prompt(config)

    assert "CollectAI" in prompt
    assert "empathetic" in prompt
    assert "Até 10% de desconto" in prompt  # discount_policy text
    assert "Parcelamento em até 12x" in prompt  # installment_policy text
    assert "Ameaçar o devedor" in prompt  # never_do
    assert "SPC" in prompt  # never_say
    assert "SimulationResult" in prompt  # JSON schema reference


def test_prompt_includes_scenario_instructions():
    """Prompt should include instructions for both cooperative and resistant scenarios."""
    config = _valid_agent_config()
    prompt = build_simulation_prompt(config)

    assert "Cooperativo" in prompt
    assert "Resistente" in prompt
    assert "full_payment" in prompt or "installment_plan" in prompt
    assert "escalated" in prompt or "no_resolution" in prompt


# --- Schema Tests ---


def test_simulation_schema_valid():
    """A valid SimulationResult should be created without errors."""
    data = _mock_simulation_response()
    result = SimulationResult(**data)

    assert len(result.scenarios) == 2
    assert result.scenarios[0].scenario_type == "cooperative"
    assert result.scenarios[1].scenario_type == "resistant"
    assert result.scenarios[0].metrics.resolution == "full_payment"
    assert result.scenarios[1].metrics.resolution == "escalated"


def test_simulation_schema_invalid_resolution():
    """Invalid resolution value should fail validation."""
    data = _mock_simulation_response()
    data["scenarios"][0]["metrics"]["resolution"] = "invalid_value"

    with pytest.raises(ValidationError):
        SimulationResult(**data)


# --- Service Tests ---


@pytest.mark.asyncio
async def test_generate_simulation():
    """Mock LLM returns valid JSON → SimulationResult with 2 scenarios and metadata."""
    config = _valid_agent_config()
    mock_data = _mock_simulation_response()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(mock_data)

    with patch("app.services.simulation.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        result = await generate_simulation(config, session_id="sess-123")

    assert isinstance(result, SimulationResult)
    assert len(result.scenarios) == 2
    assert result.scenarios[0].scenario_type == "cooperative"
    assert result.scenarios[1].scenario_type == "resistant"
    assert result.metadata["onboarding_session_id"] == "sess-123"
    assert result.metadata["generation_model"] == "gpt-4.1-mini"
    assert "generated_at" in result.metadata


@pytest.mark.asyncio
async def test_generate_retries_on_failure():
    """First call fails, second succeeds → returns valid result."""
    config = _valid_agent_config()
    mock_data = _mock_simulation_response()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(mock_data)

    with patch("app.services.simulation.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[Exception("API error"), mock_response]
        )
        mock_openai.return_value = mock_client

        result = await generate_simulation(config)

    assert isinstance(result, SimulationResult)
    assert len(result.scenarios) == 2
    assert mock_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_generate_both_attempts_fail():
    """Both OpenAI calls fail → raises ValueError."""
    config = _valid_agent_config()

    with patch("app.services.simulation.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[Exception("fail 1"), Exception("fail 2")]
        )
        mock_openai.return_value = mock_client

        with pytest.raises(ValueError, match="2 tentativas"):
            await generate_simulation(config)


# ---------------------------------------------------------------------------
# T24: Simulation endpoint tests
# ---------------------------------------------------------------------------


def _create_session(client: TestClient) -> str:
    """Helper: create a session and return its ID."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://testcorp.com"},
    )
    return resp.json()["session_id"]


def _set_session_generated(client: TestClient, session_id: str) -> None:
    """Helper: fast-forward session to 'generated' status with stored agent_config."""
    from app.database import get_db
    from app.main import app
    from app.models.orm import OnboardingSession

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    session = db.get(OnboardingSession, session_id)
    session.status = "generated"
    session.agent_config = _valid_agent_config().model_dump()
    db.commit()
    db.close()


@patch("app.routers.simulation.generate_simulation", new_callable=AsyncMock)
def test_generate_simulation_endpoint(
    mock_generate: AsyncMock,
    client: TestClient,
) -> None:
    """POST simulate on generated session → 200, simulation stored, status=completed."""
    mock_data = _mock_simulation_response()
    mock_generate.return_value = SimulationResult(**mock_data)

    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    # POST generate simulation
    resp = client.post(f"/api/v1/sessions/{session_id}/simulation/generate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert len(data["simulation_result"]["scenarios"]) == 2
    assert data["simulation_result"]["scenarios"][0]["scenario_type"] == "cooperative"

    # GET simulation returns stored result
    resp = client.get(f"/api/v1/sessions/{session_id}/simulation")
    assert resp.status_code == 200
    assert len(resp.json()["scenarios"]) == 2

    # Session status is now "completed"
    resp = client.get(f"/api/v1/sessions/{session_id}")
    assert resp.json()["status"] == "completed"


def test_simulate_before_agent(client: TestClient) -> None:
    """POST simulate without agent config → 400."""
    session_id = _create_session(client)
    resp = client.post(f"/api/v1/sessions/{session_id}/simulation/generate")
    assert resp.status_code == 400
    assert "not generated yet" in resp.json()["detail"]


def test_simulate_session_not_found(client: TestClient) -> None:
    """POST/GET simulate on nonexistent session → 404."""
    resp = client.post("/api/v1/sessions/nonexistent-id/simulation/generate")
    assert resp.status_code == 404

    resp = client.get("/api/v1/sessions/nonexistent-id/simulation")
    assert resp.status_code == 404


def test_get_simulation_not_generated(client: TestClient) -> None:
    """GET simulation before generation → 404."""
    session_id = _create_session(client)
    resp = client.get(f"/api/v1/sessions/{session_id}/simulation")
    assert resp.status_code == 404
    assert "not generated" in resp.json()["detail"]


@patch("app.routers.simulation.generate_simulation", new_callable=AsyncMock)
def test_re_simulate(
    mock_generate: AsyncMock,
    client: TestClient,
) -> None:
    """POST simulate twice → second overwrites first, both succeed."""
    mock_data = _mock_simulation_response()
    mock_generate.return_value = SimulationResult(**mock_data)

    session_id = _create_session(client)
    _set_session_generated(client, session_id)

    # First simulation
    resp = client.post(f"/api/v1/sessions/{session_id}/simulation/generate")
    assert resp.status_code == 200

    # Re-simulation should also succeed (status is "completed", which is allowed)
    resp = client.post(f"/api/v1/sessions/{session_id}/simulation/generate")
    assert resp.status_code == 200
    assert mock_generate.call_count == 2
