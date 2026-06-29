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
        False, "--tunnel", help="Also start a Cloudflare tunnel for public access"
    ),
):
    """Start the forge-agent daemon (FastAPI + Uvicorn). Optionally with Cloudflare tunnel."""
    import logging

    logger = logging.getLogger("forge.serve")
    logger.info(f"Starting forge-agent daemon on {host}:{port}")

    if tunnel:
        logger.info("Starting Cloudflare tunnel...")
        from forge.services.tunnel_manager import TunnelManager
        import asyncio as aio

        async def _start_tunnel():
            mgr = TunnelManager()
            url = await mgr.start(f"http://{host}:{port}")
            logger.info("Public URL: %s", url)
            print(f"\n  Public URL: {url}\n")

        aio.run(_start_tunnel())

    uvicorn.run(
        "forge.api.app:app",
        host=host,
        port=port,
        log_level=settings.log_level.lower(),
        reload=False,
    )
