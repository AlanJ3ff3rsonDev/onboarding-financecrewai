"""Web research service using SerpApi + LLM consolidation."""

import asyncio
import json
import logging

import httpx
from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.models.schemas import WebResearchResult
from app.prompts.web_research import CONSOLIDATION_SYSTEM_PROMPT, build_consolidation_prompt

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"


def _build_search_queries(company_name: str, website_url: str) -> list[str]:
    """Generate 3 search queries for the company.

    Args:
        company_name: Company name.
        website_url: Company website (unused for now, reserved for future filtering).

    Returns:
        List of 3 query strings.
    """
    return [
        f'"{company_name}" empresa',
        f'"{company_name}" Reclame Aqui OR avaliação OR review',
        f'"{company_name}" cobrança OR pagamento OR serviços',
    ]


async def _run_search_query(query: str) -> list[dict]:
    """Execute a single SerpApi search query.

    Args:
        query: Search query string.

    Returns:
        List of dicts with keys: title, link, snippet. Empty list on failure.
    """
    params = {
        "q": query,
        "api_key": settings.SEARCH_API_KEY,
        "engine": "google",
        "gl": "br",
        "hl": "pt-br",
        "num": 5,
    }

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(SERPAPI_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("organic_results", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            return results
        except (httpx.HTTPError, json.JSONDecodeError, Exception) as exc:
            logger.warning("Search query attempt %d failed for '%s': %s", attempt + 1, query, exc)
            if attempt == 0:
                continue
            return []


async def _consolidate_snippets(company_name: str, snippets: list[dict]) -> dict:
    """Consolidate search snippets into a WebResearchResult via LLM.

    Args:
        company_name: Company name.
        snippets: Deduplicated list of snippet dicts.

    Returns:
        WebResearchResult as dict. Returns empty-fields dict on failure.
    """
    if not snippets:
        return WebResearchResult().model_dump()

    user_message = build_consolidation_prompt(company_name, snippets)

    for attempt in range(2):
        try:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": CONSOLIDATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content)
            result = WebResearchResult(**data)
            return result.model_dump()
        except (OpenAIError, json.JSONDecodeError, Exception) as exc:
            logger.warning("Consolidation attempt %d failed: %s", attempt + 1, exc)
            if attempt == 0:
                continue
            return WebResearchResult().model_dump()


async def search_company(company_name: str, website_url: str) -> dict | None:
    """Orchestrate web research: search, deduplicate, consolidate.

    Args:
        company_name: Company name to search for.
        website_url: Company website URL.

    Returns:
        WebResearchResult dict with 5 fields, or None if no API key or all searches fail.
    """
    if not settings.SEARCH_API_KEY:
        logger.info("SEARCH_API_KEY not set, skipping web research")
        return None

    queries = _build_search_queries(company_name, website_url)

    # Run all 3 queries in parallel
    results = await asyncio.gather(
        *[_run_search_query(q) for q in queries],
        return_exceptions=True,
    )

    # Flatten and deduplicate by URL
    all_snippets: list[dict] = []
    seen_links: set[str] = set()
    for result in results:
        if isinstance(result, Exception):
            logger.warning("Search query returned exception: %s", result)
            continue
        for snippet in result:
            link = snippet.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                all_snippets.append(snippet)

    if not all_snippets:
        logger.warning("All search queries returned empty results")
        return None

    return await _consolidate_snippets(company_name, all_snippets)
