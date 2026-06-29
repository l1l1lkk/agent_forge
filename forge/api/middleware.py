"""Auth middleware for FastAPI.

Protects API routes with optional token-based authentication.
In local dev (no FORGE_AUTH_TOKEN set), all requests pass through.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from forge.core.config import settings

# Public paths that don't require auth
PUBLIC_PATHS: set[str] = {"/api/health"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates Bearer tokens on protected routes."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth if not configured or path is public
        if settings.auth_token is None or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Check Authorization header
        auth = request.headers.get("Authorization", "")
        if not auth:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header required"},
            )

        scheme, _, token = auth.partition(" ")
        if scheme.lower() != "bearer" or token != settings.auth_token:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid or missing token"},
            )

        return await call_next(request)
