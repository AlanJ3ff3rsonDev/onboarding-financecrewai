"""Prompt for generating a complete AgentConfig from onboarding data."""

import json

from app.models.schemas import AgentConfig, SmartDefaults

_AGENT_CONFIG_SCHEMA = json.dumps(
    AgentConfig.model_json_schema(), indent=2, ensure_ascii=False
)

SYSTEM_PROMPT = (
    "You are an expert debt collection agent configurator for Brazilian businesses. "
    "You receive structured data about a company (from website analysis and a detailed interview) "
    "and generate a complete AgentConfig JSON that will power an AI collection agent.\n\n"
    "Your most important output is the 'system_prompt' field — this is the detailed instruction set "
    "that the collection agent will follow in every conversation with debtors. It must be:\n"
    "- Comprehensive (at least 300 words)\n"
    "- Segment-specific (reflect the company's industry and context)\n"
    "- Written entirely in Brazilian Portuguese\n"
    "- Cover: tone, negotiation rules, escalation triggers, prohibited actions, scenario handling, "
    "and payment instructions\n\n"
    "Rules:\n"
    "- All text content in the AgentConfig (system_prompt, scenario_responses, "
    "opening_message_template, prohibited_words, preferred_words, never_do, never_say) "
    "must be in Portuguese.\n"
    "- Respect the exact discount limits and installment limits provided — never exceed them.\n"
    "- The agent_type should be 'compliant' unless the interview explicitly indicates otherwise.\n"
    "- Generate realistic, actionable scenario responses based on the company's context.\n"
    "- The tools list should include tools appropriate for the company's payment methods "
    "(e.g. generate_pix_payment_link if PIX is accepted).\n"
    "- Always respond with valid JSON matching the AgentConfig schema exactly."
)

ADJUSTMENT_SYSTEM_PROMPT = (
    "You are an expert debt collection agent configurator for Brazilian businesses. "
    "A user has just adjusted an existing agent configuration. "
    "Your job is to regenerate ONLY two fields to stay consistent with the changes:\n"
    "1. 'system_prompt': The complete instruction set for the collection agent "
    "(minimum 300 words, in Brazilian Portuguese)\n"
    "2. 'scenario_responses': The four scenario response strings (already_paid, "
    "dont_recognize_debt, cant_pay_now, aggressive_debtor) — all in Brazilian Portuguese\n\n"
    "You will receive the FULL updated agent configuration. "
    "Regenerate system_prompt and scenario_responses to reflect ALL current settings "
    "(especially tone, negotiation limits, guardrails, and company context). "
    "Return ONLY a JSON object with exactly two keys: 'system_prompt' (string) and "
    "'scenario_responses' (object with the four scenario keys). "
    "Do NOT return the full AgentConfig — only those two fields."
)


def build_adjustment_prompt(
    adjusted_config: dict,
    adjustments_summary: str,
) -> str:
    """Build user message for regenerating system_prompt + scenario_responses.

    Args:
        adjusted_config: The full agent config dict after applying user adjustments.
        adjustments_summary: Human-readable summary of what was changed.

    Returns:
        The user message to send alongside ADJUSTMENT_SYSTEM_PROMPT.
    """
    config_json = json.dumps(adjusted_config, indent=2, ensure_ascii=False)
    return (
        f"O usuário fez os seguintes ajustes na configuração do agente:\n"
        f"{adjustments_summary}\n\n"
        f"Configuração atual completa (após ajustes):\n"
        f"```json\n{config_json}\n```\n\n"
        f"Regenere o 'system_prompt' e o 'scenario_responses' para refletir "
        f"todas as configurações atuais. Retorne apenas:\n"
        f'{{"system_prompt": "...", "scenario_responses": {{...}}}}'
    )


def _get_answer_by_id(
    responses: list[dict], question_id: str
) -> str:
    """Look up the answer for a given question_id. Returns 'Não respondida' if missing."""
    for r in responses:
        if r.get("question_id") == question_id:
            return r.get("answer", "Não respondida")
    return "Não respondida"


def _get_followups(responses: list[dict], parent_id: str) -> list[dict]:
    """Get all follow-up responses for a parent question (e.g. followup_core_4_1)."""
    prefix = f"followup_{parent_id}_"
    return [r for r in responses if r.get("question_id", "").startswith(prefix)]


def _get_dynamic_responses(responses: list[dict]) -> list[dict]:
    """Get all dynamic question responses."""
    return [r for r in responses if r.get("question_id", "").startswith("dynamic_")]


def _format_answer_with_followups(
    responses: list[dict], question_id: str, label: str
) -> str:
    """Format a core answer plus any follow-up answers beneath it."""
    answer = _get_answer_by_id(responses, question_id)
    lines = [f"- {label}: {answer}"]
    for fu in _get_followups(responses, question_id):
        q_text = fu.get("question_text", "Pergunta de aprofundamento")
        fu_answer = fu.get("answer", "")
        lines.append(f"  - (Aprofundamento) {q_text}: {fu_answer}")
    return "\n".join(lines)


def _build_company_section(company_profile: dict | None) -> str:
    """Format enrichment data into the company context section."""
    if not company_profile:
        return (
            "## 1. Contexto da Empresa (dados extraídos do site)\n"
            "Nenhum dado de enriquecimento disponível. "
            "Use as respostas da entrevista como fonte principal."
        )

    field_labels = {
        "company_name": "Nome",
        "segment": "Segmento",
        "products_description": "Produtos/Serviços",
        "target_audience": "Público-alvo",
        "communication_tone": "Tom de comunicação do site",
        "payment_methods_mentioned": "Métodos de pagamento mencionados",
        "collection_relevant_context": "Contexto relevante para cobrança",
    }

    lines = ["## 1. Contexto da Empresa (dados extraídos do site)"]
    for field, label in field_labels.items():
        value = company_profile.get(field, "") or "Não informado"
        lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def _build_defaults_section(smart_defaults: dict | None) -> str:
    """Format smart defaults into labeled text."""
    defaults = smart_defaults or SmartDefaults().model_dump()

    strategy_labels = {
        "only_when_resisted": "Só quando o devedor resistir",
        "proactive": "Oferecer proativamente",
        "escalating": "Escalar gradualmente",
    }

    lines = []
    lines.append(
        f"- Estratégia de desconto: "
        f"{strategy_labels.get(defaults.get('discount_strategy', ''), defaults.get('discount_strategy', ''))}"
    )
    lines.append(
        f"- Valor mínimo da parcela: R${defaults.get('min_installment_value', 50.0):.2f}"
    )
    lines.append(
        f"- Desconto máximo em parcelamento: {defaults.get('max_discount_installment_pct', 5.0)}%"
    )
    lines.append(
        f"- Geração de link de pagamento: "
        f"{'Sim' if defaults.get('payment_link_generation', True) else 'Não'}"
    )
    lines.append(
        f"- Intervalo entre follow-ups: {defaults.get('follow_up_interval_days', 3)} dias"
    )
    lines.append(
        f"- Máximo de tentativas: {defaults.get('max_contact_attempts', 10)}"
    )
    lines.append(
        f"- Usar primeiro nome: {'Sim' if defaults.get('use_first_name', True) else 'Não'}"
    )
    lines.append(
        f"- Identificar-se como IA: {'Sim' if defaults.get('identify_as_ai', True) else 'Não'}"
    )
    return "\n".join(lines)


def build_prompt(
    company_profile: dict | None,
    interview_responses: list[dict],
    smart_defaults: dict | None,
) -> str:
    """Assemble all onboarding data into a structured prompt for AgentConfig generation.

    Args:
        company_profile: CompanyProfile dict from enrichment (or None).
        interview_responses: List of answer dicts, each with question_id,
            question_text, answer, source.
        smart_defaults: SmartDefaults dict confirmed by user (or None for defaults).

    Returns:
        The full user message to send to the LLM alongside SYSTEM_PROMPT.
    """
    sections: list[str] = []

    # Intro
    sections.append(
        "Gere um AgentConfig JSON completo para configurar um agente de cobrança "
        "com base nos dados abaixo."
    )

    # Section 1: Company Context
    sections.append(_build_company_section(company_profile))

    # Section 2: Business Model and Billing
    s2_lines = ["## 2. Modelo de Negócio e Faturamento"]
    s2_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_1", "Produtos/serviços oferecidos"
        )
    )
    s2_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_2", "Métodos de pagamento aceitos"
        )
    )
    s2_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_3", "Definição de vencimento"
        )
    )
    sections.append("\n".join(s2_lines))

    # Section 3: Debtor Profile
    s3_lines = ["## 3. Perfil do Devedor"]
    s3_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_12", "Objeções comuns dos devedores"
        )
    )
    sections.append("\n".join(s3_lines))

    # Section 4: Collection Process
    s4_lines = ["## 4. Processo de Cobrança Atual"]
    s4_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_4", "Fluxo descrito pelo cliente"
        )
    )
    sections.append("\n".join(s4_lines))

    # Section 5: Tone and Communication
    s5_lines = ["## 5. Tom e Comunicação"]
    s5_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_5", "Tom escolhido"
        )
    )
    s5_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_11",
            "O que nunca fazer/dizer (segundo o cliente)"
        )
    )
    sections.append("\n".join(s5_lines))

    # Section 6: Negotiation Rules
    s6_lines = ["## 6. Regras de Negociação"]
    s6_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_6",
            "Desconto máximo para pagamento integral"
        )
    )
    s6_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_7", "Parcelamento máximo"
        )
    )
    s6_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_8", "Juros por atraso"
        )
    )
    s6_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_9", "Multa por atraso"
        )
    )
    s6_lines.append("### Padrões confirmados pelo cliente")
    s6_lines.append(_build_defaults_section(smart_defaults))
    sections.append("\n".join(s6_lines))

    # Section 7: Guardrails and Escalation
    s7_lines = ["## 7. Guardrails e Escalação"]
    s7_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_10", "Gatilhos de escalação"
        )
    )
    s7_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_11",
            "O que nunca fazer/dizer"
        )
    )
    defaults = smart_defaults or SmartDefaults().model_dump()
    s7_lines.append("### Padrões de operação")
    s7_lines.append(
        f"- Intervalo entre follow-ups: {defaults.get('follow_up_interval_days', 3)} dias"
    )
    s7_lines.append(
        f"- Máximo de tentativas: {defaults.get('max_contact_attempts', 10)}"
    )
    s7_lines.append(
        f"- Usar primeiro nome: {'Sim' if defaults.get('use_first_name', True) else 'Não'}"
    )
    s7_lines.append(
        f"- Identificar-se como IA: {'Sim' if defaults.get('identify_as_ai', True) else 'Não'}"
    )
    sections.append("\n".join(s7_lines))

    # Section 8: Scenario Handling
    s8_lines = ["## 8. Tratamento de Cenários"]
    s8_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_12",
            "Objeções comuns relatadas pelo cliente"
        )
    )
    sections.append("\n".join(s8_lines))

    # Additional Context: dynamic questions + remaining follow-ups
    dynamic_responses = _get_dynamic_responses(interview_responses)
    if dynamic_responses:
        dyn_lines = [
            "## Contexto Adicional (perguntas dinâmicas geradas pela IA)"
        ]
        for dr in dynamic_responses:
            q_text = dr.get("question_text", "Pergunta dinâmica")
            answer = dr.get("answer", "")
            dyn_lines.append(f"- {q_text}: {answer}")
            # Include follow-ups on dynamic questions
            for fu in _get_followups(interview_responses, dr["question_id"]):
                fu_q = fu.get("question_text", "Aprofundamento")
                fu_a = fu.get("answer", "")
                dyn_lines.append(f"  - (Aprofundamento) {fu_q}: {fu_a}")
        sections.append("\n".join(dyn_lines))

    # Mapping hints
    sections.append(
        "## Dicas de Mapeamento\n"
        "Use estas correspondências ao preencher o JSON:\n"
        '- core_5: "formal" → tone.style "formal", '
        '"amigavel_firme" → "friendly", '
        '"empatico" → "empathetic", '
        '"direto_assertivo" → "assertive"\n'
        '- core_6: "nenhum" → max_discount_full_payment_pct = 0, '
        '"5" → 5, "10" → 10, "15" → 15, "20" → 20, "30" → 30, "50" → 50\n'
        '- core_7: "nenhum" → max_installments = 0, '
        '"2" → 2, "3" → 3, etc.\n'
        '- core_8/core_9: "nenhum" → mencione no system_prompt que a empresa '
        "não cobra juros/multa\n"
        '- agent_type: use "compliant" por padrão\n'
        "- tools: inclua send_whatsapp_message, check_payment_status, "
        "escalate_to_human, schedule_follow_up como base. "
        "Adicione generate_pix_payment_link se PIX aceito, "
        "generate_boleto se boleto aceito."
    )

    # JSON Schema
    sections.append(
        "## Esquema JSON de Saída (AgentConfig)\n"
        "Gere EXATAMENTE um JSON válido que se encaixe neste schema:\n\n"
        f"```json\n{_AGENT_CONFIG_SCHEMA}\n```"
    )

    return "\n\n".join(sections)
