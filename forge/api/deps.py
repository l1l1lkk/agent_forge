"""FastAPI dependencies."""

from __future__ import annotations

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.config import settings
from forge.db.session import get_db as _get_db


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yields an async database session."""
    async for session in _get_db():
        yield session


async def get_auth_token(
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """Extract and validate the auth token from the Authorization header.

    If FORGE_AUTH_TOKEN is configured, the request must include it.
    Otherwise, auth is skipped (local dev mode).
    """
    expected = settings.auth_token
    if expected is None:
        return None  # Auth disabled

    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token required")

    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")

    return token
