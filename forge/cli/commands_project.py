"""Project management CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forge.cli.api_client import get_client

project_app = typer.Typer(name="project", help="Manage projects")
console = Console()


@project_app.command("add")
def add(
    path: str = typer.Argument(..., help="Path to the project directory"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name (defaults to directory name)"),
    runner: Optional[str] = typer.Option(None, "--runner", "-r", help="Default runner type"),
):
    """Add a project workspace."""
    client = get_client()
    try:
        project = client.create_project(
            root_path=path,
            name=name,
            default_runner=runner,
        )
        console.print(f"[green][OK][/green] Project created: [bold]{project['name']}[/bold] ({project['id']})")
        console.print(f"  Root: {project['root_path']}")
    except Exception as e:
        _handle_error(e)


@project_app.command("list")
def list_projects():
    """List all projects."""
    client = get_client()
    try:
        projects = client.list_projects()
        if not projects:
            console.print("[dim]No projects registered.[/dim]")
            return

        table = Table(title="Projects", show_header=True)
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Root Path")
        table.add_column("Runner")
        table.add_column("Created")

        for p in projects:
            table.add_row(
                p["id"],
                p["name"],
                p["root_path"],
                p.get("default_runner") or "-",
                _short_date(p["created_at"]),
            )
        console.print(table)
    except Exception as e:
        _handle_error(e)


@project_app.command("show")
def show(
    identifier: str = typer.Argument(..., help="Project ID or name"),
):
    """Show project details."""
    client = get_client()
    try:
        p = client.get_project(identifier)
        panel = Panel.fit(
            f"[bold]Name:[/bold] {p['name']}\n"
            f"[bold]ID:[/bold] {p['id']}\n"
            f"[bold]Root Path:[/bold] {p['root_path']}\n"
            f"[bold]Default Runner:[/bold] {p.get('default_runner') or '-'}\n"
            f"[bold]Default Agent:[/bold] {p.get('default_agent_id') or '-'}\n"
            f"[bold]Allowed Paths:[/bold] {p.get('allowed_paths') or '-'}\n"
            f"[bold]Env:[/bold] {p.get('env_json') or '-'}\n"
            f"[bold]Created:[/bold] {p['created_at']}\n"
            f"[bold]Updated:[/bold] {p['updated_at']}",
            title=f"Project: {p['name']}",
            border_style="blue",
        )
        console.print(panel)
    except Exception as e:
        _handle_error(e)


@project_app.command("remove")
def remove(
    identifier: str = typer.Argument(..., help="Project ID or name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a project and all associated data."""
    if not force:
        typer.confirm(
            f"WARNING:  This will delete project '{identifier}' and ALL its sessions/messages. Continue?",
            abort=True,
        )
    client = get_client()
    try:
        client.delete_project(identifier)
        console.print(f"[green]OK[/green] Project deleted: {identifier}")
    except Exception as e:
        _handle_error(e)


@project_app.command("env")
def env(
    identifier: str = typer.Argument(..., help="Project ID or name"),
    set_vars: Optional[list[str]] = typer.Option(
        None, "--set", "-s", help="Set env vars in KEY=VALUE format"
    ),
):
    """View or set project environment variables."""
    client = get_client()
    try:
        if set_vars:
            env_dict = {}
            for item in set_vars:
                if "=" in item:
                    k, v = item.split("=", 1)
                    env_dict[k.strip()] = v.strip()
            if env_dict:
                import json
                client.update_project(identifier, env_json=json.dumps(env_dict))
                console.print(f"[green]OK[/green] Environment variables set for {identifier}")
        else:
            p = client.get_project(identifier)
            if p.get("env_json"):
                console.print(f"[bold]Environment for {p['name']}:[/bold]")
                console.print(p["env_json"])
            else:
                console.print("[dim]No environment variables set.[/dim]")
    except Exception as e:
        _handle_error(e)


# ── Helpers ──────────────────────────────────────────────────────

def _short_date(iso: str) -> str:
    """Return just the date portion of an ISO timestamp."""
    return iso[:10] if iso else "-"


def _handle_error(e: Exception) -> None:
    """Pretty-print API errors."""
    import httpx
    if isinstance(e, httpx.HTTPStatusError):
        try:
            detail = e.response.json().get("detail", {})
            if isinstance(detail, dict):
                msg = detail.get("message", str(e))
            else:
                msg = str(detail)
        except Exception:
            msg = str(e)
        console.print(f"[red]X Error:[/red] {msg}")
    else:
        console.print(f"[red]X Error:[/red] {e}")
    raise typer.Exit(1)
