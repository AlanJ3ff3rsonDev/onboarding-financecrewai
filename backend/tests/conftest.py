"""Test fixtures: test client, test DB, mock OpenAI."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import orm as _orm  # noqa: F401 — register models

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(setup_db: None) -> Generator[Session, None, None]:
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(setup_db: None) -> TestClient:
    def _override_get_db() -> Generator[Session, None, None]:
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)  # type: ignore[misc]
    app.dependency_overrides.clear()
