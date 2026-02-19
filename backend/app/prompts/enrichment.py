"""Prompts for company data extraction from website text."""

SYSTEM_PROMPT = (
    "You are an expert at extracting structured company information from website text. "
    "You always respond with valid JSON matching the requested schema. "
    "If a piece of information is not found in the text, return an empty string for that field. "
    "Preserve the original language of the content — if the website is in Portuguese, "
    "write field values in Portuguese."
)


def build_prompt(company_name: str, website_text: str) -> str:
    """Build the user message for company profile extraction."""
    return (
        f"Extract structured company information for \"{company_name}\" from the website text below.\n"
        "\n"
        "Return a JSON object with exactly these fields:\n"
        "- \"company_name\": the company's name\n"
        "- \"segment\": industry or market segment (e.g. \"Tecnologia\", \"Saúde\", \"Varejo\")\n"
        "- \"products_description\": what products or services they offer\n"
        "- \"target_audience\": who their customers are (B2B, B2C, or both, with details)\n"
        "- \"communication_tone\": the tone/voice used on the website (e.g. \"formal\", \"casual\", \"técnico\")\n"
        "- \"payment_methods_mentioned\": any payment methods mentioned (e.g. \"Pix, cartão, boleto\")\n"
        "- \"collection_relevant_context\": any information relevant to debt collection "
        "(billing model, subscription, SaaS, recurring payments, etc.)\n"
        "\n"
        "If a field's information is not present in the text, return an empty string for that field.\n"
        "\n"
        "--- WEBSITE TEXT ---\n"
        f"{website_text}\n"
        "--- END ---"
    )
