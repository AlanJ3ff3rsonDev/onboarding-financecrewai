"""Tests for rate limiting on API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.limiter import limiter
from app.main import app


@pytest.fixture
def rate_limited_client(setup_db):
    """Client with rate limiting enabled."""
    from collections.abc import Generator

    from sqlalchemy.orm import Session

    from app.database import get_db
    from app.dependencies import verify_api_key

    from tests.conftest import TestSessionLocal

    def _override_get_db() -> Generator[Session, None, None]:
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[verify_api_key] = lambda: None

    limiter.enabled = True
    limiter.reset()
    try:
        yield TestClient(app)
    finally:
        limiter.enabled = False
        app.dependency_overrides.clear()


def test_health_exempt_from_rate_limit(rate_limited_client: TestClient) -> None:
    """GET /health should never be rate limited."""
    for _ in range(100):
        resp = rate_limited_client.get("/health")
        assert resp.status_code == 200


def test_heavy_endpoint_rate_limited(rate_limited_client: TestClient) -> None:
    """POST /enrich (heavy tier, 5/min) should return 429 after 5 requests."""
    # Create a session first
    resp = rate_limited_client.post(
        "/api/v1/sessions",
        json={"company_name": "Test Corp", "website": "https://example.com"},
    )
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]

    url = f"/api/v1/sessions/{session_id}/enrich"
    statuses = []
    for _ in range(7):
        r = rate_limited_client.post(url)
        statuses.append(r.status_code)

    # First 5 should succeed (409 = already enriched, but not 429)
    assert 429 not in statuses[:5]
    # At least one of 6th/7th should be 429
    assert 429 in statuses[5:]


def test_light_endpoint_allows_60(rate_limited_client: TestClient) -> None:
    """Light endpoints (60/min) should allow 60 requests before 429."""
    # Create a session first
    resp = rate_limited_client.post(
        "/api/v1/sessions",
        json={"company_name": "Test Corp", "website": "https://example.com"},
    )
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]

    url = f"/api/v1/sessions/{session_id}"
    for i in range(60):
        r = rate_limited_client.get(url)
        assert r.status_code != 429, f"Rate limited too early on request {i+1}"

    # 61st request should be rate limited
    r = rate_limited_client.get(url)
    assert r.status_code == 429


def test_429_response_body_format(rate_limited_client: TestClient) -> None:
    """429 response should contain a detail message."""
    resp = rate_limited_client.post(
        "/api/v1/sessions",
        json={"company_name": "Test Corp", "website": "https://example.com"},
    )
    session_id = resp.json()["session_id"]

    url = f"/api/v1/sessions/{session_id}/enrich"
    # Exhaust the limit
    for _ in range(6):
        r = rate_limited_client.post(url)

    # Find a 429 response
    r = rate_limited_client.post(url)
    if r.status_code == 429:
        body = r.json()
        assert "detail" in body
        assert body["detail"] == "Rate limit exceeded. Try again later."
