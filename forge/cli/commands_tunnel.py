"""Tunnel CLI commands — Cloudflare Tunnel for public access."""

import asyncio
import typer
from rich.console import Console
from forge.services.tunnel_manager import TunnelManager

tunnel_app = typer.Typer(name="tunnel", help="Manage Cloudflare tunnels")
console = Console()


@tunnel_app.command("start")
def tunnel_start(
    url: str = typer.Option("http://127.0.0.1:8765", "--url", "-u", help="Local URL to expose"),
):
    """Start a Cloudflare tunnel for public access."""
    mgr = TunnelManager()

    async def _run():
        console.print(f"[dim]Starting Cloudflare tunnel for {url}...[/dim]")
        try:
            public = await mgr.start(url)
            console.print(f"\n[bold green]Public URL:[/bold green] {public}")
            console.print("\n[dim]Press Ctrl+C to stop...[/dim]")
            while mgr.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            console.print(f"[red]Tunnel error:[/red] {e}")
        finally:
            await mgr.stop()

    asyncio.run(_run())
