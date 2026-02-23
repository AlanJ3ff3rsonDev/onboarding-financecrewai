"""Prompts for web research consolidation."""

CONSOLIDATION_SYSTEM_PROMPT = (
    "Voce e um analista de pesquisa empresarial. Recebe trechos de resultados de busca "
    "sobre uma empresa brasileira e deve consolidar as informacoes em um JSON estruturado.\n\n"
    "Regras:\n"
    "- Escreva TUDO em portugues brasileiro.\n"
    "- Baseie-se APENAS nos trechos fornecidos. Nao invente informacoes.\n"
    "- Se nao houver informacao suficiente para um campo, deixe-o como string vazia.\n"
    "- Retorne EXATAMENTE um JSON com estes 5 campos (todos strings):\n"
    '  - "company_description": descricao geral da empresa (o que faz, porte, historia)\n'
    '  - "products_and_services": produtos ou servicos oferecidos\n'
    '  - "sector_context": contexto do setor/mercado em que atua\n'
    '  - "reputation_summary": reputacao online (avaliacoes, Reclame Aqui, reviews)\n'
    '  - "collection_relevant_insights": informacoes relevantes para cobranca '
    "(ex: inadimplencia no setor, perfil de clientes, metodos de pagamento)"
)


def build_consolidation_prompt(company_name: str, snippets: list[dict]) -> str:
    """Format search snippets into a consolidation prompt.

    Args:
        company_name: Name of the company being researched.
        snippets: List of dicts with keys title, link, snippet.

    Returns:
        User message for the consolidation LLM call.
    """
    lines = [f"Empresa pesquisada: {company_name}\n", "Trechos encontrados na web:\n"]
    for i, s in enumerate(snippets, 1):
        lines.append(
            f"{i}. [{s.get('title', '')}]({s.get('link', '')})\n"
            f"   {s.get('snippet', '')}\n"
        )
    lines.append(
        "\nConsolide as informacoes acima em um JSON com exatamente 5 campos: "
        "company_description, products_and_services, sector_context, "
        "reputation_summary, collection_relevant_insights."
    )
    return "\n".join(lines)
