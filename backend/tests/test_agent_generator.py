"""Tests for agent generation prompt (T19)."""

from app.prompts.agent_generator import SYSTEM_PROMPT, build_prompt


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
            "question_text": "Desconto para pagamento integral?",
            "answer": "10",
            "source": "text",
        },
        {
            "question_id": "core_7",
            "question_text": "Parcelamento máximo?",
            "answer": "12",
            "source": "text",
        },
        {
            "question_id": "core_8",
            "question_text": "Juros por atraso?",
            "answer": "1_mes",
            "source": "text",
        },
        {
            "question_id": "core_9",
            "question_text": "Multa por atraso?",
            "answer": "2",
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


def _sample_smart_defaults() -> dict:
    return {
        "follow_up_interval_days": 3,
        "max_contact_attempts": 10,
        "use_first_name": True,
        "identify_as_ai": True,
        "min_installment_value": 50.0,
        "discount_strategy": "only_when_resisted",
        "payment_link_generation": True,
        "max_discount_installment_pct": 5.0,
    }


def test_build_prompt():
    """build_prompt with complete data returns a substantial prompt string."""
    prompt = build_prompt(
        _sample_company_profile(),
        _sample_interview_responses(),
        _sample_smart_defaults(),
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 500
    assert "CollectAI" in prompt
    assert "AgentConfig" in prompt
    # SYSTEM_PROMPT exists and is non-empty
    assert len(SYSTEM_PROMPT) > 100


def test_prompt_includes_all_sections():
    """Prompt includes all 8 required sections and key interview answers."""
    prompt = build_prompt(
        _sample_company_profile(),
        _sample_interview_responses(),
        _sample_smart_defaults(),
    )

    # All 8 section headings
    assert "Contexto da Empresa" in prompt
    assert "Modelo de Negócio" in prompt
    assert "Perfil do Devedor" in prompt
    assert "Processo de Cobrança" in prompt
    assert "Tom e Comunicação" in prompt
    assert "Regras de Negociação" in prompt
    assert "Guardrails" in prompt
    assert "Cenários" in prompt

    # Key interview answers present
    assert "Software de cobrança automatizada" in prompt  # core_1
    assert "amigavel_firme" in prompt  # core_5
    assert "Nunca ameaçar" in prompt  # core_11
    assert "solicita_humano" in prompt  # core_10
    assert "já paguei" in prompt  # core_12

    # Smart defaults present
    assert "follow_up" in prompt.lower() or "follow-up" in prompt.lower()
    assert "50.0" in prompt or "50,0" in prompt  # min_installment_value

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
    """build_prompt works with None enrichment, empty responses, and None defaults."""
    # Completely empty inputs
    prompt = build_prompt(None, [], None)
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
        None,
    )
    assert "TestCorp" in prompt2
    assert "Roupas femininas" in prompt2
    # Other core answers should show as not answered
    assert "Não respondida" in prompt2
    # Defaults should fall back to SmartDefaults() values
    assert "3 dias" in prompt2  # follow_up_interval_days default
