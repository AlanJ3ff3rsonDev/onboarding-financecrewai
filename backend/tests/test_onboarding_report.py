"""Tests for OnboardingReport Pydantic schema."""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    AgentIdentity,
    CollectionPolicies,
    CollectionProfile,
    Communication,
    EnrichmentSummary,
    OnboardingReport,
    ReportCompany,
    ReportGuardrails,
    ReportMetadata,
)


def _valid_onboarding_report() -> OnboardingReport:
    """Build a complete, valid OnboardingReport for testing."""
    return OnboardingReport(
        agent_identity=AgentIdentity(name="Sofia"),
        company=ReportCompany(
            name="CollectAI",
            segment="Cobrança digital",
            products="Agente de cobrança automatizado via WhatsApp",
            target_audience="Empresas de médio porte com carteira de inadimplentes",
            website="https://collectai.com.br",
        ),
        enrichment_summary=EnrichmentSummary(
            website_analysis="Empresa de tecnologia focada em cobrança digital via WhatsApp.",
            web_research="CollectAI é líder em automação de cobrança no Brasil.",
        ),
        collection_profile=CollectionProfile(
            debt_type="Inadimplência B2B em serviços digitais",
            typical_debtor_profile="Empresas de médio porte com atraso de 30-90 dias",
            business_specific_objections="Contestação de valores, alegação de não recebimento do serviço",
            payment_verification_process="Verificação automática via integração bancária",
            sector_regulations="CDC, LGPD, normas do BACEN sobre cobrança",
        ),
        collection_policies=CollectionPolicies(
            overdue_definition="A partir de 5 dias após o vencimento",
            discount_policy="Até 15% de desconto para pagamento à vista",
            installment_policy="Parcelamento em até 12x, parcela mínima de R$50",
            interest_policy="Juros de 1% ao mês sobre o valor total",
            penalty_policy="Multa de 2% sobre o valor da parcela vencida",
            payment_methods=["pix", "boleto"],
            escalation_triggers=["solicita_humano", "divida_alta", "agressivo"],
            escalation_custom_rules="Escalar para gerente comercial se cliente é parceiro estratégico",
            collection_flow_description="D+5 WhatsApp, D+15 ligação, D+60 jurídico",
        ),
        communication=Communication(
            tone_style="empathetic",
            prohibited_actions=["Ameaçar o devedor", "Cobrar fora do horário"],
            brand_specific_language="Usar 'pendência' em vez de 'dívida'",
        ),
        guardrails=ReportGuardrails(
            never_do=[
                "Ameaçar o devedor",
                "Compartilhar dados com terceiros",
                "Cobrar fora do horário permitido",
            ],
            never_say=["processo", "SPC", "Serasa", "nome sujo"],
            must_identify_as_ai=True,
            follow_up_interval_days=3,
            max_attempts_before_stop=10,
        ),
        expert_recommendations=(
            "A CollectAI atua no segmento de cobrança digital B2B, atendendo empresas "
            "de médio porte com carteiras de inadimplentes. Recomenda-se adotar um tom "
            "empático mas firme nas comunicações, priorizando a resolução amigável. "
            "O fluxo de cobrança deve começar com contato via WhatsApp no D+5, seguido "
            "de ligação no D+15 e encaminhamento jurídico no D+60. É fundamental "
            "respeitar as normas do CDC e LGPD em todas as interações. Para o segmento "
            "de tecnologia B2B, as principais objeções são contestação de valores e "
            "alegação de não recebimento do serviço. Recomenda-se ter processos claros "
            "de verificação de pagamento via integração bancária."
        ),
        metadata=ReportMetadata(
            generated_at="2026-02-20T12:00:00Z",
            session_id="abc-123",
            model="gpt-4.1-mini",
            version=1,
        ),
    )


def test_onboarding_report_valid():
    """A complete, valid OnboardingReport should be created without errors."""
    report = _valid_onboarding_report()
    assert report.agent_identity.name == "Sofia"
    assert report.company.name == "CollectAI"
    assert report.communication.tone_style == "empathetic"
    assert report.collection_policies.discount_policy.startswith("Até 15%")
    assert report.guardrails.follow_up_interval_days == 3
    assert len(report.expert_recommendations) >= 200
    assert report.metadata.version == 1


def test_onboarding_report_collection_policies_text_based():
    """CollectionPolicies accepts text-based policy descriptions."""
    policies = CollectionPolicies(
        discount_policy="Não oferecemos desconto",
        installment_policy="Não oferecemos parcelamento",
        interest_policy="Não cobramos juros",
        penalty_policy="Não cobramos multa",
        payment_methods=["pix"],
    )
    assert policies.discount_policy == "Não oferecemos desconto"
    assert policies.payment_methods == ["pix"]


def test_onboarding_report_json_schema():
    """OnboardingReport.model_json_schema() should return a valid JSON Schema dict."""
    schema = OnboardingReport.model_json_schema()
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    assert "properties" in schema

    # All top-level fields present
    props = schema["properties"]
    expected_keys = {
        "agent_identity",
        "company",
        "enrichment_summary",
        "collection_profile",
        "collection_policies",
        "communication",
        "guardrails",
        "expert_recommendations",
        "metadata",
    }
    assert expected_keys == set(props.keys())

    # Nested schemas referenced via $defs
    assert "$defs" in schema
    defs = schema["$defs"]
    expected_defs = {
        "AgentIdentity",
        "ReportCompany",
        "EnrichmentSummary",
        "CollectionProfile",
        "CollectionPolicies",
        "Communication",
        "ReportGuardrails",
        "ReportMetadata",
    }
    assert expected_defs == set(defs.keys())
