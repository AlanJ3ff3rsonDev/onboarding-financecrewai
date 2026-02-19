"""Tests for the enrichment scraping, LLM extraction, and API endpoints."""

import json

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from app.models.schemas import CompanyProfile
from app.services.enrichment import scrape_website, extract_company_profile


# --- Scraping tests (from T05) ---


@pytest.mark.asyncio
async def test_scrape_real_website():
    """Scrape example.com and verify text is returned."""
    text = await scrape_website("https://example.com")
    assert len(text) > 0
    assert "Example Domain" in text


@pytest.mark.asyncio
async def test_scrape_invalid_url():
    """Invalid URL returns empty string without raising."""
    text = await scrape_website("not-a-valid-url")
    assert text == ""


@pytest.mark.asyncio
async def test_scrape_timeout():
    """Timeout during navigation returns empty string."""
    with patch("app.services.enrichment.async_playwright") as mock_pw:
        # Set up the mock chain: async_playwright() -> context manager -> chromium.launch() -> page
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.goto.side_effect = TimeoutError("Navigation timeout")
        mock_browser.new_page.return_value = mock_page

        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw_instance = AsyncMock()
        mock_pw_instance.chromium = mock_chromium

        mock_pw.return_value.__aenter__.return_value = mock_pw_instance

        text = await scrape_website("https://example.com")
        assert text == ""


# --- LLM extraction tests (T06) ---


@pytest.mark.asyncio
async def test_extract_profile_empty_content():
    """Empty website text returns minimal profile without calling LLM."""
    profile = await extract_company_profile("TestCorp", "")
    assert profile.company_name == "TestCorp"
    assert profile.segment == ""
    assert profile.products_description == ""
    assert profile.target_audience == ""
    assert profile.communication_tone == ""
    assert profile.payment_methods_mentioned == ""
    assert profile.collection_relevant_context == ""


@pytest.mark.asyncio
async def test_extract_profile_with_content():
    """Given website text, LLM returns a populated CompanyProfile."""
    mock_response_data = {
        "company_name": "CollectAI",
        "segment": "Tecnologia / Cobrança",
        "products_description": "Agentes de cobrança automatizados com IA",
        "target_audience": "B2B — empresas com carteira de inadimplência",
        "communication_tone": "profissional e empático",
        "payment_methods_mentioned": "Pix, boleto",
        "collection_relevant_context": "SaaS de cobrança com agentes virtuais",
    }

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(mock_response_data)
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("app.services.enrichment.AsyncOpenAI") as mock_openai_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        profile = await extract_company_profile(
            "CollectAI", "Somos uma empresa de cobrança com IA..."
        )

    assert profile.company_name == "CollectAI"
    assert profile.segment == "Tecnologia / Cobrança"
    assert profile.products_description == "Agentes de cobrança automatizados com IA"
    assert profile.target_audience == "B2B — empresas com carteira de inadimplência"
    assert profile.communication_tone == "profissional e empático"
    assert profile.payment_methods_mentioned == "Pix, boleto"
    assert profile.collection_relevant_context == "SaaS de cobrança com agentes virtuais"


def test_profile_schema_validation():
    """CompanyProfile validates correct data and enforces required fields."""
    # Valid profile
    profile = CompanyProfile(
        company_name="TestCorp",
        segment="Varejo",
        products_description="Roupas femininas",
        target_audience="B2C",
        communication_tone="casual",
        payment_methods_mentioned="Pix, cartão",
        collection_relevant_context="Vendas parceladas no cartão",
    )
    assert profile.company_name == "TestCorp"
    assert profile.segment == "Varejo"

    # Minimal profile — only company_name required
    minimal = CompanyProfile(company_name="MinCorp")
    assert minimal.company_name == "MinCorp"
    assert minimal.segment == ""

    # Missing company_name raises ValidationError
    with pytest.raises(Exception):
        CompanyProfile()


# --- API endpoint tests (T07) ---

MOCK_PROFILE = CompanyProfile(
    company_name="TestCorp",
    segment="Tecnologia",
    products_description="Software de cobrança",
    target_audience="B2B",
    communication_tone="profissional",
    payment_methods_mentioned="Pix, boleto",
    collection_relevant_context="SaaS de cobrança",
)


def _create_session(client: TestClient) -> str:
    """Helper: create a session and return its ID."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCorp", "website": "https://testcorp.com"},
    )
    return resp.json()["session_id"]


@patch("app.routers.enrichment.extract_company_profile", new_callable=AsyncMock)
@patch("app.routers.enrichment.scrape_website", new_callable=AsyncMock)
def test_enrich_session(
    mock_scrape: AsyncMock,
    mock_extract: AsyncMock,
    client: TestClient,
) -> None:
    """POST enrich → status enriched, GET enrichment returns CompanyProfile."""
    mock_scrape.return_value = "Some website text"
    mock_extract.return_value = MOCK_PROFILE

    session_id = _create_session(client)

    # Trigger enrichment
    resp = client.post(f"/api/v1/sessions/{session_id}/enrich")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "enriched"
    assert data["enrichment_data"]["company_name"] == "TestCorp"

    # Verify via GET enrichment
    resp = client.get(f"/api/v1/sessions/{session_id}/enrichment")
    assert resp.status_code == 200
    profile = resp.json()
    assert profile["company_name"] == "TestCorp"
    assert profile["segment"] == "Tecnologia"

    # Verify session status changed
    resp = client.get(f"/api/v1/sessions/{session_id}")
    assert resp.json()["status"] == "enriched"


def test_enrich_not_found(client: TestClient) -> None:
    """POST enrich for non-existent session returns 404."""
    resp = client.post("/api/v1/sessions/nonexistent-id/enrich")
    assert resp.status_code == 404


@patch("app.routers.enrichment.extract_company_profile", new_callable=AsyncMock)
@patch("app.routers.enrichment.scrape_website", new_callable=AsyncMock)
def test_enrich_already_done(
    mock_scrape: AsyncMock,
    mock_extract: AsyncMock,
    client: TestClient,
) -> None:
    """POST enrich twice returns 409 on second call."""
    mock_scrape.return_value = "Some text"
    mock_extract.return_value = MOCK_PROFILE

    session_id = _create_session(client)

    # First call succeeds
    resp = client.post(f"/api/v1/sessions/{session_id}/enrich")
    assert resp.status_code == 200

    # Second call returns 409
    resp = client.post(f"/api/v1/sessions/{session_id}/enrich")
    assert resp.status_code == 409


def test_get_enrichment_not_enriched(client: TestClient) -> None:
    """GET enrichment before enriching returns 404."""
    session_id = _create_session(client)
    resp = client.get(f"/api/v1/sessions/{session_id}/enrichment")
    assert resp.status_code == 404


def test_get_enrichment_session_not_found(client: TestClient) -> None:
    """GET enrichment for non-existent session returns 404."""
    resp = client.get("/api/v1/sessions/nonexistent-id/enrichment")
    assert resp.status_code == 404
