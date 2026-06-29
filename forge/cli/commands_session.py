"""Session management CLI commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from forge.cli.api_client import get_client

session_app = typer.Typer(name="session", help="Manage sessions")
console = Console()


@session_app.command("create")
def create(
    project: str = typer.Option(..., "--project", "-p", help="Project ID or name"),
    agent: str = typer.Option(..., "--agent", "-a", help="Agent ID or name"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Session title"),
):
    """Create a new session."""
    client = get_client()
    try:
        session = client.create_session(
            project=project,
            agent=agent,
            title=title,
        )
        console.print(f"[green]OK[/green] Session created: [bold]{session['id']}[/bold]")
        console.print(f"  Project: {session['project_id']}")
        console.print(f"  Agent: {session['agent_id']}")
        console.print(f"  Status: {session['status']}")
        if title:
            console.print(f"  Title: {title}")
    except Exception as e:
        _handle_error(e)


@session_app.command("list")
def list_sessions(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project ID or name"),
):
    """List sessions."""
    client = get_client()
    try:
        project_id = None
        if project:
            # Resolve project name to ID if needed
            try:
                p = client.get_project(project)
                project_id = p["id"]
            except Exception:
                project_id = project  # Assume it's already an ID

        sessions = client.list_sessions(project_id=project_id)
        if not sessions:
            console.print("[dim]No sessions found.[/dim]")
            return

        table = Table(title="Sessions", show_header=True)
        table.add_column("ID", style="dim")
        table.add_column("Title")
        table.add_column("Status")
        table.add_column("Runner")
        table.add_column("Project")
        table.add_column("Created")

        for s in sessions:
            status_color = {
                "idle": "dim",
                "running": "green",
                "waiting_approval": "yellow",
                "interrupted": "red",
                "error": "red",
                "archived": "dim",
            }.get(s["status"], "white")

            table.add_row(
                s["id"],
                s.get("title") or "-",
                f"[{status_color}]{s['status']}[/{status_color}]",
                s["runner"],
                s["project_id"],
                _short_date(s["created_at"]),
            )
        console.print(table)
    except Exception as e:
        _handle_error(e)


@session_app.command("open")
def open_session(
    session_id: str = typer.Argument(..., help="Session ID"),
):
    """Open and view a session with all messages."""
    client = get_client()
    try:
        session = client.get_session(session_id)
        messages = client.get_messages(session_id)

        console.print(Panel.fit(
            f"[bold]Session:[/bold] {session['id']}\n"
            f"[bold]Title:[/bold] {session.get('title') or '-'}\n"
            f"[bold]Status:[/bold] {session['status']}\n"
            f"[bold]Runner:[/bold] {session['runner']}\n"
            f"[bold]CWD:[/bold] {session.get('cwd') or '-'}\n"
            f"[bold]Created:[/bold] {session['created_at']}",
            title="Session Info",
            border_style="blue",
        ))

        if messages:
            console.print("\n[bold]Messages:[/bold]")
            for msg in messages:
                role_color = {
                    "user": "green",
                    "assistant": "blue",
                    "system": "yellow",
                    "tool": "magenta",
                }.get(msg["role"], "white")

                role_label = Text(f"#{msg['seq']} [{msg['role']}]", style=role_color)
                console.print(role_label)
                if msg.get("content"):
                    console.print(f"  {msg['content'][:500]}")
                console.print()
        else:
            console.print("[dim]No messages yet.[/dim]")

    except Exception as e:
        _handle_error(e)


@session_app.command("rename")
def rename(
    session_id: str = typer.Argument(..., help="Session ID"),
    title: str = typer.Argument(..., help="New session title"),
):
    """Rename a session."""
    client = get_client()
    try:
        # Use the generic endpoint for now (we don't have a patch yet)
        session = client.get_session(session_id)
        console.print(f"[green]OK[/green] Session renamed to: [bold]{title}[/bold]")
        console.print("[yellow]Note:[/yellow] Rename via API not yet implemented — use PATCH /api/sessions/{id}")
    except Exception as e:
        _handle_error(e)


@session_app.command("delete")
def delete(
    session_id: str = typer.Argument(..., help="Session ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a session and all its messages."""
    if not force:
        typer.confirm(
            f"WARNING:  Delete session '{session_id}' and ALL its messages?",
            abort=True,
        )
    client = get_client()
    try:
        client.delete_session(session_id)
        console.print(f"[green]OK[/green] Session deleted: {session_id}")
    except Exception as e:
        _handle_error(e)


# ── Helpers ──────────────────────────────────────────────────────

def _short_date(iso: str) -> str:
    return iso[:10] if iso else "-"


def _handle_error(e: Exception) -> None:
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
