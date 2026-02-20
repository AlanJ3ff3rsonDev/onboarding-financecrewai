"""Prompt for generating simulated debt collection conversations."""

import json

from app.models.schemas import AgentConfig, SimulationResult

_SIMULATION_SCHEMA = json.dumps(
    SimulationResult.model_json_schema(), indent=2, ensure_ascii=False
)

SYSTEM_PROMPT = (
    "You are an expert simulator of debt collection conversations for Brazilian businesses. "
    "You receive a complete agent configuration (AgentConfig) and generate 2 realistic "
    "simulated conversations in Brazilian Portuguese.\n\n"
    "Rules:\n"
    "- Generate exactly 2 scenarios: one 'cooperative' debtor and one 'resistant' debtor.\n"
    "- CRITICAL: Each conversation MUST have between 10 and 15 messages (minimum 10). "
    "Short conversations with fewer than 10 messages are NOT acceptable. "
    "Build a realistic back-and-forth: the debtor asks questions, raises objections, "
    "the agent responds, proposes solutions, and the conversation evolves naturally.\n"
    "- The agent MUST strictly follow the configured tone, discount limits, guardrails, "
    "and scenario response templates.\n"
    "- The agent must NEVER offer discounts above the configured max_discount_full_payment_pct "
    "or max_discount_installment_pct.\n"
    "- The agent must NEVER say or do anything listed in never_say or never_do.\n"
    "- If must_identify_as_ai is true, the agent must identify as AI in the conversation.\n"
    "- All conversation content must be in natural Brazilian Portuguese.\n"
    "- Debtor names should be realistic Brazilian names (e.g., Carlos, Maria, João).\n"
    "- Include realistic monetary values in BRL.\n"
    "- The cooperative scenario should end with a successful resolution "
    "(full payment or installment plan).\n"
    "- The resistant scenario should test the agent's guardrails and escalation triggers, "
    "ending in either a partial resolution or escalation to a human.\n"
    "- Always respond with valid JSON matching the SimulationResult schema exactly."
)


def build_simulation_prompt(agent_config: AgentConfig) -> str:
    """Assemble the AgentConfig data into a structured prompt for simulation generation.

    Args:
        agent_config: The complete AgentConfig to simulate conversations for.

    Returns:
        The full user message to send to the LLM alongside SYSTEM_PROMPT.
    """
    sections: list[str] = []

    sections.append(
        "Gere 2 conversas simuladas de cobrança com base na configuração do agente abaixo."
    )

    # Section 1: Agent System Prompt
    sections.append(
        "## System Prompt do Agente\n"
        "O agente segue exatamente estas instruções:\n\n"
        f"{agent_config.system_prompt}"
    )

    # Section 2: Company Context
    ctx = agent_config.company_context
    sections.append(
        "## Contexto da Empresa\n"
        f"- Nome: {ctx.name}\n"
        f"- Segmento: {ctx.segment}\n"
        f"- Produtos/Serviços: {ctx.products}\n"
        f"- Público-alvo: {ctx.target_audience}"
    )

    # Section 3: Tone
    tone = agent_config.tone
    prohibited = ", ".join(tone.prohibited_words) if tone.prohibited_words else "Nenhuma"
    preferred = ", ".join(tone.preferred_words) if tone.preferred_words else "Nenhuma"
    sections.append(
        "## Tom da Comunicação\n"
        f"- Estilo: {tone.style}\n"
        f"- Usar primeiro nome: {'Sim' if tone.use_first_name else 'Não'}\n"
        f"- Palavras proibidas: {prohibited}\n"
        f"- Palavras preferidas: {preferred}\n"
        f"- Template de abertura: {tone.opening_message_template}"
    )

    # Section 4: Negotiation Policies
    neg = agent_config.negotiation_policies
    methods = ", ".join(neg.payment_methods) if neg.payment_methods else "Nenhum"
    strategy_labels = {
        "only_when_resisted": "Só quando o devedor resistir",
        "proactive": "Oferecer proativamente",
        "escalating": "Escalar gradualmente",
    }
    sections.append(
        "## Políticas de Negociação\n"
        f"- Desconto máximo (pagamento integral): {neg.max_discount_full_payment_pct}%\n"
        f"- Desconto máximo (parcelamento): {neg.max_discount_installment_pct}%\n"
        f"- Máximo de parcelas: {neg.max_installments}\n"
        f"- Valor mínimo da parcela: R${neg.min_installment_value_brl:.2f}\n"
        f"- Estratégia de desconto: {strategy_labels.get(neg.discount_strategy, neg.discount_strategy)}\n"
        f"- Métodos de pagamento: {methods}\n"
        f"- Pode gerar link de pagamento: {'Sim' if neg.can_generate_payment_link else 'Não'}"
    )

    # Section 5: Guardrails
    guard = agent_config.guardrails
    never_do = "; ".join(guard.never_do) if guard.never_do else "Nenhum"
    never_say = "; ".join(guard.never_say) if guard.never_say else "Nenhum"
    escalation = "; ".join(guard.escalation_triggers) if guard.escalation_triggers else "Nenhum"
    sections.append(
        "## Guardrails\n"
        f"- Nunca fazer: {never_do}\n"
        f"- Nunca dizer: {never_say}\n"
        f"- Gatilhos de escalação: {escalation}\n"
        f"- Identificar-se como IA: {'Sim' if guard.must_identify_as_ai else 'Não'}"
    )

    # Section 6: Scenario Response Templates
    sr = agent_config.scenario_responses
    sections.append(
        "## Templates de Resposta para Cenários\n"
        f"- Já pagou: {sr.already_paid}\n"
        f"- Não reconhece a dívida: {sr.dont_recognize_debt}\n"
        f"- Não pode pagar agora: {sr.cant_pay_now}\n"
        f"- Devedor agressivo: {sr.aggressive_debtor}"
    )

    # Section 7: Scenario Instructions
    sections.append(
        "## Instruções dos Cenários\n\n"
        "### Cenário 1: Devedor Cooperativo (mínimo 10 mensagens)\n"
        "- O devedor quer pagar, mas precisa de condições (desconto ou parcelamento)\n"
        "- O agente se apresenta, explica o motivo do contato, e inicia negociação\n"
        "- O devedor faz perguntas sobre valores, prazos e formas de pagamento\n"
        "- O agente negocia dentro dos limites configurados, propondo opções\n"
        "- O devedor considera, talvez peça outra opção, e aceita uma proposta\n"
        "- O agente confirma o acordo e gera o link de pagamento\n"
        "- Resolução esperada: 'full_payment' ou 'installment_plan'\n"
        "- Dívida sugerida: entre R$500 e R$5.000\n\n"
        "### Cenário 2: Devedor Resistente (mínimo 10 mensagens)\n"
        "- O devedor contesta a dívida, desconfia, ou fica agressivo\n"
        "- O agente mantém a calma, segue os guardrails e templates de cenário\n"
        "- O devedor testa os limites: pede descontos absurdos, questiona legitimidade, ameaça\n"
        "- O agente tenta negociar, mas o devedor se recusa ou escala a agressividade\n"
        "- O agente identifica gatilho de escalação e encerra educadamente\n"
        "- Resolução esperada: 'escalated' ou 'no_resolution'\n"
        "- Dívida sugerida: entre R$1.000 e R$10.000"
    )

    # Section 8: Output Schema
    sections.append(
        "## Esquema JSON de Saída (SimulationResult)\n"
        "Gere EXATAMENTE um JSON válido que se encaixe neste schema:\n\n"
        f"```json\n{_SIMULATION_SCHEMA}\n```"
    )

    return "\n\n".join(sections)
