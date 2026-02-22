"""Tests for AgentConfig Pydantic schema (T18)."""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    AgentConfig,
    AgentMetadata,
    CompanyContext,
    Guardrails,
    NegotiationPolicies,
    ScenarioResponses,
    ToneConfig,
)


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
            discount_policy="Até 15% de desconto para pagamento à vista, apenas quando o devedor resiste",
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
                "Cobrar fora do horário permitido",
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
            already_paid="Peço desculpas pelo contato. Pode me enviar o comprovante para verificação?",
            dont_recognize_debt="Entendo. Vou encaminhar para nossa equipe verificar os detalhes.",
            cant_pay_now="Compreendo. Podemos encontrar uma opção de parcelamento que caiba no seu orçamento.",
            aggressive_debtor="Entendo sua frustração. Vou encerrar por aqui e entraremos em contato em outro momento.",
        ),
        tools=[
            "send_whatsapp_message",
            "generate_pix_payment_link",
            "generate_boleto",
            "check_payment_status",
            "escalate_to_human",
            "schedule_follow_up",
        ],
        metadata=AgentMetadata(
            version=1,
            generated_at="2026-02-20T12:00:00Z",
            onboarding_session_id="abc-123",
            generation_model="gpt-4.1-mini",
        ),
    )


def test_agent_config_valid():
    """A complete, valid AgentConfig should be created without errors."""
    config = _valid_agent_config()
    assert config.agent_type == "compliant"
    assert config.company_context.name == "CollectAI"
    assert config.tone.style == "empathetic"
    assert config.negotiation_policies.discount_policy.startswith("Até 15%")
    assert config.guardrails.follow_up_interval_days == 3
    assert config.scenario_responses.already_paid.startswith("Peço desculpas")
    assert len(config.tools) == 6
    assert config.metadata.version == 1


def test_agent_config_negotiation_policies_text_based():
    """NegotiationPolicies accepts text-based policy descriptions."""
    policies = NegotiationPolicies(
        discount_policy="Não oferecemos desconto",
        installment_policy="Não oferecemos parcelamento",
        interest_policy="Não cobramos juros",
        penalty_policy="Não cobramos multa",
        payment_methods=["pix"],
        can_generate_payment_link=False,
    )
    assert policies.discount_policy == "Não oferecemos desconto"
    assert policies.payment_methods == ["pix"]
    assert policies.can_generate_payment_link is False


def test_agent_config_json_schema():
    """AgentConfig.model_json_schema() should return a valid JSON Schema dict."""
    schema = AgentConfig.model_json_schema()
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    assert "properties" in schema

    # All top-level fields present
    props = schema["properties"]
    expected_keys = {
        "agent_type",
        "company_context",
        "system_prompt",
        "tone",
        "negotiation_policies",
        "guardrails",
        "scenario_responses",
        "tools",
        "metadata",
    }
    assert expected_keys == set(props.keys())

    # Nested schemas referenced via $defs
    assert "$defs" in schema
    defs = schema["$defs"]
    expected_defs = {
        "CompanyContext",
        "ToneConfig",
        "NegotiationPolicies",
        "Guardrails",
        "ScenarioResponses",
        "AgentMetadata",
    }
    assert expected_defs == set(defs.keys())
