"""Prompt for generating simulated debt collection conversations."""

import json

from app.models.schemas import OnboardingReport, SimulationResult

_SIMULATION_SCHEMA = json.dumps(
    SimulationResult.model_json_schema(), indent=2, ensure_ascii=False
)

SYSTEM_PROMPT = (
    "You are an expert simulator of WhatsApp-based debt collection conversations "
    "for Brazilian businesses. You receive a complete onboarding report (OnboardingReport) "
    "and generate 2 realistic simulated conversations in Brazilian Portuguese.\n\n"
    "## Context: How WhatsApp Collection Works\n"
    "The agent contacts debtors via WhatsApp. When a payment agreement is reached, "
    "the agent generates a payment link and sends it directly in the WhatsApp conversation "
    "(NOT by email). The conversation should feel natural — like a real WhatsApp chat, "
    "with short messages, natural greetings, and empathetic tone.\n\n"
    "## Rules\n"
    "- Generate exactly 2 scenarios: one 'cooperative' debtor and one 'resistant' debtor.\n"
    "- CRITICAL: Each conversation MUST have between 10 and 15 messages (minimum 10). "
    "Short conversations with fewer than 10 messages are NOT acceptable. "
    "Build a realistic back-and-forth: the debtor asks questions, raises objections, "
    "the agent responds, proposes solutions, and the conversation evolves naturally.\n"
    "- The agent MUST strictly follow the configured tone, guardrails, "
    "and collection policies.\n"
    "- The agent must NEVER say or do anything listed in never_say or never_do.\n"
    "- If must_identify_as_ai is true, the agent must identify as AI in the conversation.\n"
    "- All conversation content must be in natural Brazilian Portuguese.\n"
    "- Debtor names should be realistic Brazilian names (e.g., Carlos, Maria, João).\n"
    "- Include realistic monetary values in BRL.\n"
    "- The cooperative scenario should end with a successful resolution "
    "(full payment or installment plan).\n"
    "- The resistant scenario should test the agent's guardrails and escalation triggers, "
    "ending in either a partial resolution or escalation to a human.\n"
    "- Always respond with valid JSON matching the SimulationResult schema exactly.\n\n"
    "## CRITICAL: When to Mention Policies in Conversation\n"
    "Follow these rules carefully — they define what a good collection agent does:\n\n"
    "### Discounts and Installments (benefits the agent GIVES to the client)\n"
    "- If the company OFFERS discounts or installments: the agent SHOULD proactively "
    "mention them as a negotiation tool (e.g., 'Posso te oferecer um desconto de X%').\n"
    "- If the company does NOT offer discounts or installments: the agent must NEVER "
    "bring this up unprompted. Do NOT say 'infelizmente não oferecemos desconto' or "
    "'não temos parcelamento'. Only address it if the debtor explicitly asks.\n\n"
    "### Fines and Interest (NOT charging is a benefit for the client)\n"
    "- If the company does NOT charge fines or interest: the agent SHOULD proactively "
    "mention this as an incentive (e.g., 'Não estamos cobrando multa nem juros, "
    "então seria ótimo resolver agora').\n"
    "- If the company DOES charge fines or interest: the agent must NOT bring this up "
    "unless the debtor asks about it. Only explain if directly questioned.\n\n"
    "The principle: only proactively mention things that BENEFIT the client. "
    "Never volunteer information that could discourage them or create friction."
)


def build_simulation_prompt(report: OnboardingReport) -> str:
    """Assemble the OnboardingReport data into a structured prompt for simulation generation.

    Args:
        report: The complete OnboardingReport to simulate conversations for.

    Returns:
        The full user message to send to the LLM alongside SYSTEM_PROMPT.
    """
    sections: list[str] = []

    sections.append(
        "Gere 2 conversas simuladas de cobrança com base no relatório do agente abaixo."
    )

    # Section 1: Expert Recommendations
    sections.append(
        "## Recomendações do Especialista\n"
        "O agente deve seguir estas recomendações:\n\n"
        f"{report.expert_recommendations}"
    )

    # Section 2: Company
    company = report.company
    sections.append(
        "## Empresa\n"
        f"- Nome: {company.name}\n"
        f"- Segmento: {company.segment}\n"
        f"- Produtos/Serviços: {company.products}\n"
        f"- Público-alvo: {company.target_audience}"
    )

    # Section 3: Communication
    comm = report.communication
    prohibited = ", ".join(comm.prohibited_actions) if comm.prohibited_actions else "Nenhuma"
    sections.append(
        "## Comunicação\n"
        f"- Estilo: {comm.tone_style}\n"
        f"- Ações proibidas: {prohibited}\n"
        f"- Linguagem da marca: {comm.brand_specific_language or 'Não definida'}"
    )

    # Section 4: Collection Policies
    pol = report.collection_policies
    methods = ", ".join(pol.payment_methods) if pol.payment_methods else "Nenhum"
    escalation = ", ".join(pol.escalation_triggers) if pol.escalation_triggers else "Nenhum"
    sections.append(
        "## Políticas de Cobrança\n"
        f"- Definição de atraso: {pol.overdue_definition or 'Não definida'}\n"
        f"- Política de desconto: {pol.discount_policy}\n"
        f"- Política de parcelamento: {pol.installment_policy}\n"
        f"- Política de juros: {pol.interest_policy}\n"
        f"- Política de multa: {pol.penalty_policy}\n"
        f"- Métodos de pagamento: {methods}\n"
        f"- Gatilhos de escalação: {escalation}\n"
        f"- Regras customizadas de escalação: {pol.escalation_custom_rules or 'Nenhuma'}\n"
        f"- Fluxo de cobrança: {pol.collection_flow_description or 'Não descrito'}"
    )

    # Section 5: Guardrails
    guard = report.guardrails
    never_do = "; ".join(guard.never_do) if guard.never_do else "Nenhum"
    never_say = "; ".join(guard.never_say) if guard.never_say else "Nenhum"
    sections.append(
        "## Guardrails\n"
        f"- Nunca fazer: {never_do}\n"
        f"- Nunca dizer: {never_say}\n"
        f"- Identificar-se como IA: {'Sim' if guard.must_identify_as_ai else 'Não'}"
    )

    # Section 6: Collection Profile
    prof = report.collection_profile
    sections.append(
        "## Perfil de Cobrança\n"
        f"- Tipo de dívida: {prof.debt_type or 'Não especificado'}\n"
        f"- Perfil típico do devedor: {prof.typical_debtor_profile or 'Não especificado'}\n"
        f"- Objeções específicas do negócio: {prof.business_specific_objections or 'Não especificado'}\n"
        f"- Processo de verificação de pagamento: {prof.payment_verification_process or 'Não especificado'}\n"
        f"- Regulamentações do setor: {prof.sector_regulations or 'Não especificado'}"
    )

    # Section 7: Scenario Instructions
    sections.append(
        "## Instruções dos Cenários\n\n"
        "### Cenário 1: Devedor Cooperativo (mínimo 10 mensagens)\n"
        "- O devedor quer pagar, pode precisar de condições\n"
        "- O agente se apresenta, explica o motivo do contato, e inicia negociação\n"
        "- O devedor faz perguntas sobre valores, prazos e formas de pagamento\n"
        "- O agente negocia seguindo as políticas configuradas\n"
        "- IMPORTANTE: só mencione desconto/parcelamento SE a empresa oferecer. "
        "Só mencione ausência de multa/juros SE a empresa não cobra. "
        "Siga as regras de 'quando mencionar políticas' do system prompt.\n"
        "- O devedor considera e aceita uma proposta\n"
        "- O agente confirma o acordo e envia o link de pagamento pelo WhatsApp\n"
        "- Resolução esperada: 'full_payment' ou 'installment_plan'\n"
        "- Dívida sugerida: entre R$500 e R$5.000\n\n"
        "### Cenário 2: Devedor Resistente (mínimo 10 mensagens)\n"
        "- O devedor contesta a dívida, desconfia, ou fica agressivo\n"
        "- O agente mantém a calma, segue os guardrails e as recomendações do especialista\n"
        "- O devedor testa os limites: questiona legitimidade, ignora mensagens, ameaça\n"
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
