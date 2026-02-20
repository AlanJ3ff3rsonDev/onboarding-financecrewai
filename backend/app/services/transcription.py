"""Whisper audio transcription service."""

import logging

from openai import AsyncOpenAI, OpenAIError

from app.config import settings

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

# Map content-type → file extension for the OpenAI SDK filename
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "audio/webm": ".webm",
    "audio/mp4": ".mp4",
    "video/mp4": ".mp4",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
}


async def transcribe_audio(file_bytes: bytes, content_type: str) -> dict:
    """Transcribe audio bytes to text using OpenAI's transcription API.

    Args:
        file_bytes: Raw audio file bytes.
        content_type: MIME type of the audio file.

    Returns:
        Dict with ``text`` (str) and ``duration_seconds`` (float).

    Raises:
        ValueError: If file is empty, too large, or has an unsupported format.
    """
    if not file_bytes:
        raise ValueError("Arquivo de áudio vazio.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(
            f"Arquivo excede o limite de 25 MB ({len(file_bytes) / (1024 * 1024):.1f} MB)."
        )

    extension = ALLOWED_CONTENT_TYPES.get(content_type)
    if extension is None:
        raise ValueError(
            f"Formato não suportado: {content_type}. "
            f"Formatos aceitos: webm, mp4, wav, mpeg."
        )

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    filename = f"audio{extension}"

    for attempt in range(2):
        try:
            response = await client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=(filename, file_bytes),
                language="pt",
            )
            text = response.text.strip() if response.text else ""
            duration = getattr(response, "duration", 0.0) or 0.0
            return {"text": text, "duration_seconds": float(duration)}
        except OpenAIError as exc:
            logger.warning("Transcription attempt %d failed: %s", attempt + 1, exc)
            if attempt == 0:
                continue
            raise ValueError(
                "Falha na transcrição do áudio. Tente novamente ou digite sua resposta."
            ) from exc
