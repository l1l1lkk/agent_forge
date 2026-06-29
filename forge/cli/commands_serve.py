"""Serve command — start the forge-agent daemon."""

from __future__ import annotations

import typer
import uvicorn

from forge.core.config import settings

serve_app = typer.Typer(name="serve", help="Start the forge-agent daemon")


@serve_app.callback(invoke_without_command=True)
def serve(
    host: str = typer.Option(
        settings.host, "--host", "-h", help="Bind address"
    ),
    port: int = typer.Option(
        settings.port, "--port", "-p", help="Bind port"
    ),
    tunnel: bool = typer.Option(
        False, "--tunnel", help="Also start a Cloudflare tunnel (not yet implemented)"
    ),
):
    """Start the forge-agent daemon (FastAPI + Uvicorn)."""
    import logging

    logger = logging.getLogger("forge.serve")
    logger.info(f"Starting forge-agent daemon on {host}:{port}")

    if tunnel:
        logger.warning("Cloudflare tunnel not yet implemented (Milestone 8)")

    uvicorn.run(
        "forge.api.app:app",
        host=host,
        port=port,
        log_level=settings.log_level.lower(),
        reload=False,
    )
