"""Prompt for generating a complete OnboardingReport from onboarding data."""

import json

from app.models.schemas import OnboardingReport
from app.prompts.interview import (
    DEFAULT_ESCALATION_TRIGGERS,
    DEFAULT_GUARDRAILS,
    DEFAULT_TONE,
)

_REPORT_SCHEMA = json.dumps(
    OnboardingReport.model_json_schema(), indent=2, ensure_ascii=False
)

SYSTEM_PROMPT = (
    "You are an expert debt collection consultant for Brazilian businesses. "
    "You receive structured data about a company (from website analysis and a detailed interview) "
    "and generate a complete OnboardingReport JSON — a structured SOP document that captures "
    "everything about the company's collection operation.\n\n"
    "IMPORTANT: You are NOT generating a system_prompt or agent instructions. "
    "You are generating a structured report that a downstream platform will use "
    "to configure a collection agent. The report must be factual and comprehensive.\n\n"
    "Your most important output is the 'expert_recommendations' field — this is your expert "
    "analysis and recommendations for the company's collection operation. It must be:\n"
    "- CRITICAL: At least 300 words\n"
    "- Written entirely in Brazilian Portuguese\n"
    "- Cover: análise do segmento, recomendações de tom, estratégias de negociação, "
    "riscos do setor, melhores práticas adaptadas ao perfil da empresa\n"
    "- Be specific to the company's industry and context, not generic advice\n\n"
    "The 'collection_profile' section requires expert inference based on the company's segment, "
    "products, and interview answers. Infer debt_type, typical_debtor_profile, "
    "business_specific_objections, payment_verification_process, and sector_regulations "
    "from context.\n\n"
    "Rules:\n"
    "- All text content in the OnboardingReport must be in Portuguese.\n"
    "- The collection_policies fields (discount_policy, installment_policy, interest_policy, "
    "penalty_policy) are text descriptions of the company's methodology.\n"
    "- communication.tone_style: use 'friendly' as default. "
    "Map detected tones: 'formal' → 'formal', 'empático' → 'empathetic', "
    "'direto/assertivo' → 'assertive'.\n"
    "- Always respond with valid JSON matching the OnboardingReport schema exactly."
)

ADJUSTMENT_SYSTEM_PROMPT = (
    "You are an expert debt collection consultant for Brazilian businesses. "
    "A user has just adjusted an existing onboarding report. "
    "Your job is to regenerate ONLY the 'expert_recommendations' field "
    "to stay consistent with the changes.\n\n"
    "You will receive the FULL updated report. "
    "Regenerate expert_recommendations to reflect ALL current settings "
    "(especially communication tone, collection policies, guardrails, and company context). "
    "The expert_recommendations must be at least 300 words, in Brazilian Portuguese, "
    "and specific to the company.\n\n"
    "Return ONLY a JSON object with exactly one key: "
    '{"expert_recommendations": "..."}. '
    "Do NOT return the full OnboardingReport — only that one field."
)


def build_adjustment_prompt(
    adjusted_report: dict,
    adjustments_summary: str,
) -> str:
    """Build user message for regenerating expert_recommendations.

    Args:
        adjusted_report: The full report dict after applying user adjustments.
        adjustments_summary: Human-readable summary of what was changed.

    Returns:
        The user message to send alongside ADJUSTMENT_SYSTEM_PROMPT.
    """
    report_json = json.dumps(adjusted_report, indent=2, ensure_ascii=False)
    return (
        f"O usuário fez os seguintes ajustes no relatório:\n"
        f"{adjustments_summary}\n\n"
        f"Relatório atual completo (após ajustes):\n"
        f"```json\n{report_json}\n```\n\n"
        f"Regenere o 'expert_recommendations' para refletir "
        f"todas as configurações atuais. Retorne apenas:\n"
        f'{{"expert_recommendations": "..."}}'
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
    """Get all follow-up responses for a parent question (e.g. followup_core_1_1)."""
    prefix = f"followup_{parent_id}_"
    return [r for r in responses if r.get("question_id", "").startswith(prefix)]


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

    # Append web research data if available
    web_research = company_profile.get("web_research")
    if web_research and isinstance(web_research, dict):
        wr_labels = {
            "company_description": "Descrição da empresa",
            "products_and_services": "Produtos/Serviços (pesquisa web)",
            "sector_context": "Contexto do setor",
            "reputation_summary": "Reputação online",
            "collection_relevant_insights": "Insights relevantes para cobrança",
        }
        wr_lines = []
        for field, label in wr_labels.items():
            value = web_research.get(field, "")
            if value and isinstance(value, str) and value.strip():
                wr_lines.append(f"- {label}: {value.strip()}")
        if wr_lines:
            lines.append("\n### Pesquisa Web Adicional")
            lines.extend(wr_lines)

    return "\n".join(lines)


def _format_policy_answer(responses: list[dict], question_id: str, policy_name: str) -> str:
    """Format a yes/no policy answer with its follow-up detail."""
    answer = _get_answer_by_id(responses, question_id)
    answer_normalized = answer.strip().lower()
    followups = _get_followups(responses, question_id)

    if answer_normalized == "sim":
        if followups:
            detail = followups[0].get("answer", "Sem detalhes")
            return f"- {policy_name}: Sim — {detail}"
        return f"- {policy_name}: Sim (sem detalhes fornecidos)"
    if answer_normalized == "nao":
        return f"- {policy_name}: Não"
    return f"- {policy_name}: {answer}"


def build_prompt(
    company_profile: dict | None,
    interview_responses: list[dict],
) -> str:
    """Assemble all onboarding data into a structured prompt for OnboardingReport generation.

    Args:
        company_profile: CompanyProfile dict from enrichment (or None).
        interview_responses: List of answer dicts, each with question_id,
            question_text, answer, source.

    Returns:
        The full user message to send to the LLM alongside SYSTEM_PROMPT.
    """
    sections: list[str] = []

    # Intro
    sections.append(
        "Gere um OnboardingReport JSON completo para documentar a operação de cobrança "
        "com base nos dados abaixo."
    )

    # Section 0: Agent Identity (conditional — only if client named the agent)
    agent_name = _get_answer_by_id(interview_responses, "core_0")
    skip_names = {"nao", "não", "passo", "n", "nao respondida", "não respondida"}
    if agent_name.strip() and agent_name.strip().lower() not in skip_names:
        sections.append(
            f"## 0. Identidade do Agente\n"
            f"- Nome escolhido para o agente: {agent_name}"
        )

    # Section 1: Company Context (enrichment)
    sections.append(_build_company_section(company_profile))

    # Section 2: Modelo de Negócio (from enrichment only)
    s2_lines = ["## 2. Modelo de Negócio (extraído do site/pesquisa web)"]
    if company_profile:
        products = company_profile.get("products_description", "Não informado")
        audience = company_profile.get("target_audience", "Não informado")
        payments = company_profile.get("payment_methods_mentioned", "Não informado")
        s2_lines.append(f"- Produtos/Serviços: {products}")
        s2_lines.append(f"- Público-alvo: {audience}")
        s2_lines.append(f"- Métodos de pagamento: {payments}")
    else:
        s2_lines.append("- Dados não disponíveis. Inferir a partir do contexto geral.")
    sections.append("\n".join(s2_lines))

    # Section 3: Processo de Cobrança (new core_1)
    s3_lines = ["## 3. Processo de Cobrança"]
    s3_lines.append(
        _format_answer_with_followups(
            interview_responses, "core_1", "Fluxo descrito pelo cliente"
        )
    )
    sections.append("\n".join(s3_lines))

    # Section 4: Tom e Comunicação (default + enrichment override)
    s4_lines = ["## 4. Tom e Comunicação"]
    tone = DEFAULT_TONE
    if company_profile and company_profile.get("communication_tone"):
        detected_tone = company_profile["communication_tone"].strip()
        s4_lines.append(f"- Tom detectado no site: {detected_tone}")
        s4_lines.append(f"- Tom padrão: {DEFAULT_TONE}")
        s4_lines.append("- Use o tom detectado no site se disponível, senão use o padrão.")
    else:
        s4_lines.append(f"- Tom padrão: {tone}")
    sections.append("\n".join(s4_lines))

    # Section 5: Políticas de Negociação (core_2-5 + follow-ups)
    s5_lines = ["## 5. Políticas de Negociação"]
    s5_lines.append(_format_policy_answer(interview_responses, "core_2", "Juros por atraso"))
    s5_lines.append(_format_policy_answer(interview_responses, "core_3", "Desconto para pagamento"))
    s5_lines.append(_format_policy_answer(interview_responses, "core_4", "Parcelamento"))
    s5_lines.append(_format_policy_answer(interview_responses, "core_5", "Multa por atraso"))
    sections.append("\n".join(s5_lines))

    # Section 6: Guardrails e Escalação (defaults + core_6 optional text)
    s6_lines = ["## 6. Guardrails e Escalação"]
    s6_lines.append("### Gatilhos de escalação (padrão)")
    for trigger in DEFAULT_ESCALATION_TRIGGERS:
        s6_lines.append(f"- {trigger}")
    # Add client-specified escalation triggers if provided
    core_6_answer = _get_answer_by_id(interview_responses, "core_6")
    skip_answers = {"nao", "não", "nao respondida", "não respondida", "n", "passo"}
    if core_6_answer.strip() and core_6_answer.strip().lower() not in skip_answers:
        s6_lines.append(f"- Situação adicional indicada pelo cliente: {core_6_answer}")
    s6_lines.append("\n### O que o agente NUNCA deve fazer (padrão)")
    for guardrail in DEFAULT_GUARDRAILS:
        s6_lines.append(f"- {guardrail}")
    sections.append("\n".join(s6_lines))

    # Review notes (if user added any during review step)
    review_notes = _get_answer_by_id(interview_responses, "review_notes")
    if review_notes != "Não respondida":
        sections.append(
            "## Notas adicionais do cliente (revisão)\n"
            f"{review_notes}"
        )

    # Mapping hints
    sections.append(
        "## Dicas de Mapeamento\n"
        "Use estas correspondências ao preencher o JSON:\n"
        '- communication.tone_style: use "friendly" como padrão (amigável mas firme). '
        'Se enrichment detectar tom diferente, mapear: '
        '"formal" → "formal", "empático" → "empathetic", '
        '"direto/assertivo" → "assertive"\n'
        "- collection_profile: infira debt_type, typical_debtor_profile, "
        "business_specific_objections, payment_verification_process e "
        "sector_regulations com base no segmento e contexto da empresa\n"
        "- collection_policies.collection_flow_description: resuma o fluxo de cobrança "
        "descrito pelo cliente na entrevista"
    )

    # JSON Schema
    sections.append(
        "## Esquema JSON de Saída (OnboardingReport)\n"
        "Gere EXATAMENTE um JSON válido que se encaixe neste schema:\n\n"
        f"```json\n{_REPORT_SCHEMA}\n```"
    )

    return "\n\n".join(sections)
