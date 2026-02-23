"""Tests for web research service (Serper API + LLM consolidation)."""

import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.schemas import WebResearchResult
from app.prompts.web_research import build_consolidation_prompt
from app.services.web_research import (
    _build_search_queries,
    _consolidate_snippets,
    _run_search_query,
    search_company,
)


# --- Schema tests ---


def test_web_research_result_schema():
    """WebResearchResult has 5 string fields, all default to empty."""
    result = WebResearchResult()
    assert result.company_description == ""
    assert result.products_and_services == ""
    assert result.sector_context == ""
    assert result.reputation_summary == ""
    assert result.collection_relevant_insights == ""

    # With data
    result = WebResearchResult(
        company_description="Empresa X",
        products_and_services="Software",
        sector_context="Tecnologia",
        reputation_summary="Boa reputacao",
        collection_relevant_insights="Alta inadimplencia no setor",
    )
    assert result.company_description == "Empresa X"
    assert result.collection_relevant_insights == "Alta inadimplencia no setor"


# --- Query builder tests ---


def test_build_search_queries():
    """Generates 3 queries containing the company name."""
    queries = _build_search_queries("Empresa ABC", "https://empresaabc.com.br")
    assert len(queries) == 3
    for q in queries:
        assert "Empresa ABC" in q


# --- Search query tests ---


@pytest.mark.asyncio
@patch("app.services.web_research.httpx.AsyncClient")
async def test_run_search_query_success(mock_client_cls: MagicMock):
    """Successful Serper query extracts title/link/snippet from organic results."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "organic": [
            {"title": "Result 1", "link": "https://example.com/1", "snippet": "Snippet 1"},
            {"title": "Result 2", "link": "https://example.com/2", "snippet": "Snippet 2"},
        ]
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    with patch("app.services.web_research.settings") as mock_settings:
        mock_settings.SEARCH_API_KEY = "test-key"
        results = await _run_search_query('"Test Company" empresa')

    assert len(results) == 2
    assert results[0]["title"] == "Result 1"
    assert results[0]["link"] == "https://example.com/1"
    assert results[0]["snippet"] == "Snippet 1"


@pytest.mark.asyncio
@patch("app.services.web_research.httpx.AsyncClient")
async def test_run_search_query_empty_results(mock_client_cls: MagicMock):
    """Serper query with no organic results returns empty list."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"organic": []}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    with patch("app.services.web_research.settings") as mock_settings:
        mock_settings.SEARCH_API_KEY = "test-key"
        results = await _run_search_query('"Test" empresa')

    assert results == []


# --- Consolidation tests ---


@pytest.mark.asyncio
@patch("app.services.web_research.AsyncOpenAI")
async def test_consolidate_snippets(mock_openai_cls: MagicMock):
    """LLM consolidation parses response into WebResearchResult fields."""
    consolidation_data = {
        "company_description": "Empresa de tecnologia",
        "products_and_services": "Software de gestao",
        "sector_context": "Setor de SaaS B2B",
        "reputation_summary": "4.5 estrelas no Google",
        "collection_relevant_insights": "Clientes PME com alta rotatividade",
    }

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(consolidation_data)
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai_cls.return_value = mock_client

    snippets = [
        {"title": "Test", "link": "https://test.com", "snippet": "Info about company"},
    ]
    result = await _consolidate_snippets("TestCorp", snippets)

    assert result["company_description"] == "Empresa de tecnologia"
    assert result["products_and_services"] == "Software de gestao"
    assert result["sector_context"] == "Setor de SaaS B2B"
    assert result["reputation_summary"] == "4.5 estrelas no Google"
    assert result["collection_relevant_insights"] == "Clientes PME com alta rotatividade"


# --- Integration: search_company orchestrator ---


@pytest.mark.asyncio
@patch("app.services.web_research._consolidate_snippets", new_callable=AsyncMock)
@patch("app.services.web_research._run_search_query", new_callable=AsyncMock)
async def test_search_company_returns_result(
    mock_search: AsyncMock, mock_consolidate: AsyncMock
):
    """Happy path: search_company returns dict with 5 fields."""
    mock_search.return_value = [
        {"title": "R1", "link": "https://a.com", "snippet": "S1"},
        {"title": "R2", "link": "https://b.com", "snippet": "S2"},
    ]
    mock_consolidate.return_value = {
        "company_description": "Desc",
        "products_and_services": "Prod",
        "sector_context": "Sector",
        "reputation_summary": "Rep",
        "collection_relevant_insights": "Insights",
    }

    with patch("app.services.web_research.settings") as mock_settings:
        mock_settings.SEARCH_API_KEY = "test-key"
        result = await search_company("TestCorp", "https://testcorp.com")

    assert result is not None
    assert result["company_description"] == "Desc"
    assert result["products_and_services"] == "Prod"
    assert result["sector_context"] == "Sector"
    assert result["reputation_summary"] == "Rep"
    assert result["collection_relevant_insights"] == "Insights"
    assert mock_search.call_count == 3  # 3 parallel queries


@pytest.mark.asyncio
async def test_search_company_no_api_key():
    """Returns None when SEARCH_API_KEY is not set."""
    with patch("app.services.web_research.settings") as mock_settings:
        mock_settings.SEARCH_API_KEY = ""
        result = await search_company("TestCorp", "https://testcorp.com")

    assert result is None


@pytest.mark.asyncio
@patch("app.services.web_research._run_search_query", new_callable=AsyncMock)
async def test_search_company_search_failure(mock_search: AsyncMock):
    """Returns None when all search queries fail (empty results)."""
    mock_search.return_value = []

    with patch("app.services.web_research.settings") as mock_settings:
        mock_settings.SEARCH_API_KEY = "test-key"
        result = await search_company("TestCorp", "https://testcorp.com")

    assert result is None


@pytest.mark.asyncio
@patch("app.services.web_research.AsyncOpenAI")
@patch("app.services.web_research._run_search_query", new_callable=AsyncMock)
async def test_search_company_llm_failure(
    mock_search: AsyncMock, mock_openai_cls: MagicMock
):
    """Returns empty-fields dict when LLM consolidation fails."""
    mock_search.return_value = [
        {"title": "R1", "link": "https://a.com", "snippet": "S1"},
    ]

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("LLM error")
    mock_openai_cls.return_value = mock_client

    with patch("app.services.web_research.settings") as mock_settings:
        mock_settings.SEARCH_API_KEY = "test-key"
        mock_settings.OPENAI_API_KEY = "test-openai-key"
        result = await search_company("TestCorp", "https://testcorp.com")

    assert result is not None
    assert result["company_description"] == ""
    assert result["products_and_services"] == ""


@pytest.mark.asyncio
@patch("app.services.web_research._consolidate_snippets", new_callable=AsyncMock)
@patch("app.services.web_research._run_search_query", new_callable=AsyncMock)
async def test_snippets_deduplicated_by_link(
    mock_search: AsyncMock, mock_consolidate: AsyncMock
):
    """Duplicate URLs across queries are deduplicated before consolidation."""
    # All 3 queries return the same URL
    mock_search.return_value = [
        {"title": "Same", "link": "https://same.com", "snippet": "Same snippet"},
    ]
    mock_consolidate.return_value = WebResearchResult().model_dump()

    with patch("app.services.web_research.settings") as mock_settings:
        mock_settings.SEARCH_API_KEY = "test-key"
        await search_company("TestCorp", "https://testcorp.com")

    # Consolidation should receive only 1 unique snippet, not 3
    call_args = mock_consolidate.call_args
    snippets_passed = call_args[0][1]
    assert len(snippets_passed) == 1


# --- Prompt builder tests ---


def test_build_consolidation_prompt():
    """Consolidation prompt includes company name and all snippets."""
    snippets = [
        {"title": "Title 1", "link": "https://a.com", "snippet": "Snippet 1"},
        {"title": "Title 2", "link": "https://b.com", "snippet": "Snippet 2"},
    ]
    prompt = build_consolidation_prompt("Empresa X", snippets)
    assert "Empresa X" in prompt
    assert "Title 1" in prompt
    assert "Title 2" in prompt
    assert "Snippet 1" in prompt
    assert "Snippet 2" in prompt
