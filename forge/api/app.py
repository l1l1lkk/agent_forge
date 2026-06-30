"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from forge.api.middleware import AuthMiddleware
from forge.api.routers import agents, connectors, desktop, projects, schedules, sessions, tasks, ws
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
        version="0.0.16rc1",
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
        return {"status": "ok", "version": "0.0.16rc1"}

    # Register routers
    app.include_router(projects.router, prefix="/api")
    app.include_router(agents.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(schedules.router, prefix="/api")
    app.include_router(connectors.router, prefix="/api")
    app.include_router(desktop.router)
    app.include_router(ws.router, prefix="/api")

    # Serve Web UI static files
    static_dir = Path(__file__).parent.parent / "web" / "static"
    if static_dir.exists() and list(static_dir.glob("index.html")):
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str = ""):
            """Serve the React frontend for non-API routes."""
            # Skip API routes
            if full_path.startswith("api/") or full_path.startswith("ws"):
                from fastapi import HTTPException
                raise HTTPException(status_code=404)

            file_path = static_dir / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))

            # Fall back to index.html for SPA routing
            index = static_dir / "index.html"
            if index.exists():
                return FileResponse(str(index))

            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")

    return app


# Module-level app instance (used by uvicorn)
app = create_app()
