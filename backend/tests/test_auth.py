"""Tests for X-API-Key authentication."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import orm as _orm  # noqa: F401

TEST_API_KEY = "test-secret-key-12345"

test_engine = create_engine(
    "sqlite:///./test.db", connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture
def unauth_client(setup_db, monkeypatch):
    """Client WITHOUT auth override — tests real auth behaviour."""
    monkeypatch.setattr("app.config.settings.API_KEY", TEST_API_KEY)

    def _override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    # Do NOT override verify_api_key
    app.dependency_overrides.pop(
        __import__("app.dependencies", fromlist=["verify_api_key"]).verify_api_key,
        None,
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_missing_key_returns_401(unauth_client: TestClient):
    resp = unauth_client.post(
        "/api/v1/sessions",
        json={"company_name": "Test", "website": "https://example.com"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or missing API key"


def test_wrong_key_returns_401(unauth_client: TestClient):
    resp = unauth_client.post(
        "/api/v1/sessions",
        json={"company_name": "Test", "website": "https://example.com"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_empty_key_returns_401(unauth_client: TestClient):
    resp = unauth_client.post(
        "/api/v1/sessions",
        json={"company_name": "Test", "website": "https://example.com"},
        headers={"X-API-Key": ""},
    )
    assert resp.status_code == 401


def test_valid_key_creates_session(unauth_client: TestClient):
    resp = unauth_client.post(
        "/api/v1/sessions",
        json={"company_name": "Test", "website": "https://example.com"},
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code == 201


def test_health_requires_no_key(unauth_client: TestClient):
    resp = unauth_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_with_valid_key_passes_auth(unauth_client: TestClient):
    """GET on a nonexistent session returns 404 (not 401) — auth passed."""
    resp = unauth_client.get(
        "/api/v1/sessions/nonexistent-id",
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code != 401
