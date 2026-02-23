"""Tests for avatar upload endpoint (T31)."""

import io
from unittest.mock import patch

from fastapi.testclient import TestClient


def _create_session(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCo", "website": "https://test.com"},
    )
    return resp.json()["session_id"]


def _fake_image_bytes(size: int = 100) -> bytes:
    """Return minimal bytes to simulate an image file."""
    return b"\x89PNG" + b"\x00" * (size - 4)


class TestAvatarUpload:
    def test_upload_avatar_png_success(self, client: TestClient) -> None:
        session_id = _create_session(client)
        file_bytes = _fake_image_bytes()

        resp = client.post(
            f"/api/v1/sessions/{session_id}/agent/avatar/upload",
            files={"file": ("avatar.png", io.BytesIO(file_bytes), "image/png")},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "avatar_url" in data
        assert data["avatar_url"] == f"/uploads/avatars/{session_id}.png"

        # Verify persisted in DB
        session_resp = client.get(f"/api/v1/sessions/{session_id}")
        assert session_resp.json()["agent_avatar_path"] == data["avatar_url"]

    def test_upload_avatar_jpg_success(self, client: TestClient) -> None:
        session_id = _create_session(client)
        file_bytes = _fake_image_bytes()

        resp = client.post(
            f"/api/v1/sessions/{session_id}/agent/avatar/upload",
            files={"file": ("photo.jpg", io.BytesIO(file_bytes), "image/jpeg")},
        )

        assert resp.status_code == 200
        assert resp.json()["avatar_url"].endswith(".jpg")

    def test_upload_avatar_webp_success(self, client: TestClient) -> None:
        session_id = _create_session(client)
        file_bytes = _fake_image_bytes()

        resp = client.post(
            f"/api/v1/sessions/{session_id}/agent/avatar/upload",
            files={"file": ("img.webp", io.BytesIO(file_bytes), "image/webp")},
        )

        assert resp.status_code == 200
        assert resp.json()["avatar_url"].endswith(".webp")

    def test_upload_avatar_invalid_format(self, client: TestClient) -> None:
        session_id = _create_session(client)

        resp = client.post(
            f"/api/v1/sessions/{session_id}/agent/avatar/upload",
            files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
        )

        assert resp.status_code == 400
        assert "Formato não suportado" in resp.json()["detail"]

    def test_upload_avatar_too_large(self, client: TestClient) -> None:
        session_id = _create_session(client)
        large_bytes = b"\x00" * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte

        resp = client.post(
            f"/api/v1/sessions/{session_id}/agent/avatar/upload",
            files={"file": ("big.png", io.BytesIO(large_bytes), "image/png")},
        )

        assert resp.status_code == 400
        assert "5 MB" in resp.json()["detail"]

    def test_upload_avatar_session_not_found(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/sessions/nonexistent-id/agent/avatar/upload",
            files={"file": ("a.png", io.BytesIO(b"\x89PNG"), "image/png")},
        )

        assert resp.status_code == 404
        assert "Session not found" in resp.json()["detail"]

    def test_upload_avatar_overwrites(self, client: TestClient) -> None:
        session_id = _create_session(client)

        # First upload (PNG)
        resp1 = client.post(
            f"/api/v1/sessions/{session_id}/agent/avatar/upload",
            files={"file": ("v1.png", io.BytesIO(_fake_image_bytes()), "image/png")},
        )
        assert resp1.status_code == 200
        assert resp1.json()["avatar_url"].endswith(".png")

        # Second upload (JPG) — overwrites
        resp2 = client.post(
            f"/api/v1/sessions/{session_id}/agent/avatar/upload",
            files={
                "file": ("v2.jpg", io.BytesIO(_fake_image_bytes()), "image/jpeg")
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["avatar_url"].endswith(".jpg")

        # DB reflects latest upload
        session_resp = client.get(f"/api/v1/sessions/{session_id}")
        assert session_resp.json()["agent_avatar_path"] == resp2.json()["avatar_url"]
