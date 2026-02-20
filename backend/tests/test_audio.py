"""Tests for T16: Audio transcription service + T17: Audio upload endpoint."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import OpenAIError

from app.services.transcription import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    transcribe_audio,
)


def _mock_transcription_response(text: str = "Olá, tudo bem?", duration: float = 2.5):
    """Create a mock OpenAI transcription response."""
    response = MagicMock()
    response.text = text
    response.duration = duration
    return response


@pytest.mark.asyncio
async def test_transcribe_valid_audio():
    """Valid audio bytes with supported content type returns text + duration."""
    mock_response = _mock_transcription_response("Nós vendemos software de gestão.", 3.2)

    with patch("app.services.transcription.AsyncOpenAI") as mock_openai_cls:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        result = await transcribe_audio(b"\x00" * 1024, "audio/webm")

    assert result["text"] == "Nós vendemos software de gestão."
    assert result["duration_seconds"] == 3.2

    # Verify API call args
    call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini-transcribe"
    assert call_kwargs["language"] == "pt"
    assert call_kwargs["file"] == ("audio.webm", b"\x00" * 1024)


@pytest.mark.asyncio
async def test_transcribe_invalid_format():
    """Unsupported content type raises ValueError."""
    with pytest.raises(ValueError, match="Formato não suportado"):
        await transcribe_audio(b"\x00" * 100, "text/plain")


@pytest.mark.asyncio
async def test_transcribe_too_large():
    """File exceeding 25 MB raises ValueError."""
    oversized = b"\x00" * (MAX_FILE_SIZE + 1)
    with pytest.raises(ValueError, match="excede o limite de 25 MB"):
        await transcribe_audio(oversized, "audio/mpeg")


@pytest.mark.asyncio
async def test_transcribe_empty_bytes():
    """Empty file bytes raises ValueError."""
    with pytest.raises(ValueError, match="vazio"):
        await transcribe_audio(b"", "audio/wav")


@pytest.mark.asyncio
async def test_transcribe_api_error_retries():
    """First API call fails, second succeeds — returns text."""
    mock_response = _mock_transcription_response("Resposta após retry.", 1.5)

    with patch("app.services.transcription.AsyncOpenAI") as mock_openai_cls:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create.side_effect = [
            OpenAIError("rate limit"),
            mock_response,
        ]
        mock_openai_cls.return_value = mock_client

        result = await transcribe_audio(b"\x00" * 512, "audio/mp4")

    assert result["text"] == "Resposta após retry."
    assert result["duration_seconds"] == 1.5
    assert mock_client.audio.transcriptions.create.call_count == 2


@pytest.mark.asyncio
async def test_transcribe_api_error_exhausted():
    """Both API attempts fail — raises ValueError with user-friendly message."""
    with patch("app.services.transcription.AsyncOpenAI") as mock_openai_cls:
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create.side_effect = OpenAIError("server error")
        mock_openai_cls.return_value = mock_client

        with pytest.raises(ValueError, match="Falha na transcrição"):
            await transcribe_audio(b"\x00" * 512, "audio/wav")

    assert mock_client.audio.transcriptions.create.call_count == 2


@pytest.mark.asyncio
async def test_transcribe_all_content_types():
    """All allowed content types are accepted without validation error."""
    mock_response = _mock_transcription_response()

    for content_type, ext in ALLOWED_CONTENT_TYPES.items():
        with patch("app.services.transcription.AsyncOpenAI") as mock_openai_cls:
            mock_client = AsyncMock()
            mock_client.audio.transcriptions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            result = await transcribe_audio(b"\x00" * 100, content_type)
            assert result["text"] == "Olá, tudo bem?"

            call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
            assert call_kwargs["file"][0] == f"audio{ext}"


# ---------------------------------------------------------------------------
# T17: Audio upload endpoint tests
# ---------------------------------------------------------------------------


def _create_session(client):
    """Helper: create a session and return its ID."""
    resp = client.post(
        "/api/v1/sessions",
        json={"company_name": "TestCo", "website": "https://test.com"},
    )
    return resp.json()["session_id"]


@patch("app.routers.audio.transcribe_audio", new_callable=AsyncMock)
def test_transcribe_endpoint(mock_transcribe: AsyncMock, client):
    """Upload valid audio file → 200 + transcription returned."""
    mock_transcribe.return_value = {"text": "Olá, tudo bem?", "duration_seconds": 2.5}

    session_id = _create_session(client)
    resp = client.post(
        f"/api/v1/sessions/{session_id}/audio/transcribe",
        files={"file": ("audio.webm", b"\x00" * 512, "audio/webm")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["text"] == "Olá, tudo bem?"
    assert data["duration_seconds"] == 2.5
    mock_transcribe.assert_awaited_once()


@patch("app.routers.audio.transcribe_audio", new_callable=AsyncMock)
def test_transcribe_bad_format(mock_transcribe: AsyncMock, client):
    """Upload unsupported file type → 400 error."""
    mock_transcribe.side_effect = ValueError("Formato não suportado: text/plain")

    session_id = _create_session(client)
    resp = client.post(
        f"/api/v1/sessions/{session_id}/audio/transcribe",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )

    assert resp.status_code == 400
    assert "Formato não suportado" in resp.json()["detail"]


def test_transcribe_no_file(client):
    """POST without file → 422 validation error."""
    session_id = _create_session(client)
    resp = client.post(f"/api/v1/sessions/{session_id}/audio/transcribe")
    assert resp.status_code == 422


def test_transcribe_session_not_found(client):
    """POST to non-existent session → 404."""
    resp = client.post(
        "/api/v1/sessions/nonexistent-id/audio/transcribe",
        files={"file": ("audio.webm", b"\x00" * 100, "audio/webm")},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Session not found"
