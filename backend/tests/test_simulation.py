"""Tests for simulation prompt + service (T23)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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
            max_discount_full_payment_pct=10.0,
            max_discount_installment_pct=5.0,
            max_installments=12,
            min_installment_value_brl=50.0,
            discount_strategy="only_when_resisted",
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
    """Prompt should include company name, tone, discount limits, guardrails, and schema."""
    config = _valid_agent_config()
    prompt = build_simulation_prompt(config)

    assert "CollectAI" in prompt
    assert "empathetic" in prompt
    assert "10.0%" in prompt  # max_discount_full_payment_pct
    assert "5.0%" in prompt  # max_discount_installment_pct
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
