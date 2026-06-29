"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from forge.api.middleware import AuthMiddleware
from forge.api.routers import agents, projects, sessions, ws
from forge.db.base import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init database. Shutdown: close connections."""
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="forge-agent",
        version="0.0.1rc1",
        description="AI Coding CLI Workbench API",
        lifespan=lifespan,
    )

    # CORS — allow all origins in dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth middleware
    app.add_middleware(AuthMiddleware)

    # Health check
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.0.1rc1"}

    # Register routers
    app.include_router(projects.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(ws.router, prefix="/api")

    return app


# Module-level app instance (used by uvicorn)
app = create_app()
