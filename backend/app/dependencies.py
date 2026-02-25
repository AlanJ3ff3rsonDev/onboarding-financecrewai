"""Shared FastAPI dependencies."""

import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> None:
    """Reject requests without a valid API key."""
    if (
        not api_key
        or not settings.API_KEY
        or not secrets.compare_digest(api_key, settings.API_KEY)
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
