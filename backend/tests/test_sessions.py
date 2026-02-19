"""Tests for session model and API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.orm import OnboardingSession


# --- Database model tests (T03) ---


def test_create_session(db_session: Session) -> None:
    session = OnboardingSession(
        company_name="Test Company",
        company_website="https://example.com",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    result = db_session.get(OnboardingSession, session.id)
    assert result is not None
    assert result.company_name == "Test Company"
    assert result.company_website == "https://example.com"
    assert result.status == "created"
    assert result.id is not None
    assert result.created_at is not None


def test_session_json_fields(db_session: Session) -> None:
    enrichment = {"segment": "Tech", "products": ["SaaS"]}
    session = OnboardingSession(
        company_name="JSON Test",
        company_website="https://example.com",
        enrichment_data=enrichment,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    result = db_session.get(OnboardingSession, session.id)
    assert result is not None
    assert result.enrichment_data == enrichment
    assert result.enrichment_data["segment"] == "Tech"
    assert result.enrichment_data["products"] == ["SaaS"]


# --- API endpoint tests (T04) ---


def test_create_session_api(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sessions",
        json={"company_name": "Acme Corp", "website": "https://acme.com"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "created"


def test_get_session_api(client: TestClient) -> None:
    create_resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "Acme Corp", "website": "https://acme.com"},
    )
    session_id = create_resp.json()["session_id"]

    response = client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["company_name"] == "Acme Corp"
    assert data["company_website"] == "https://acme.com"
    assert data["status"] == "created"


def test_get_session_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/nonexistent-id")
    assert response.status_code == 404


def test_create_session_missing_fields(client: TestClient) -> None:
    response = client.post("/api/v1/sessions", json={"website": "https://acme.com"})
    assert response.status_code == 422
