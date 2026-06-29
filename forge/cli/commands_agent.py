"""Agent management CLI commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forge.cli.api_client import get_client

agent_app = typer.Typer(name="agent", help="Manage agents")
console = Console()


@agent_app.command("create")
def create(
    name: str = typer.Argument(..., help="Unique agent name"),
    runner: str = typer.Option(..., "--runner", "-r", help="Runner type: codex, claude, openai-compatible, etc."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model identifier"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", "-s", help="System prompt"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Sampling temperature (0.0-2.0)"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Max output tokens"),
):
    """Create a new AI agent."""
    client = get_client()
    try:
        agent = client.create_agent(
            name=name,
            runner=runner,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        console.print(f"[green]OK[/green] Agent created: [bold]{agent['name']}[/bold] ({agent['id']})")
        console.print(f"  Runner: {agent['runner']}")
        if agent.get("model"):
            console.print(f"  Model: {agent['model']}")
        if agent.get("system_prompt"):
            console.print(f"  System Prompt: {agent['system_prompt'][:100]}...")
    except Exception as e:
        _handle_error(e)


@agent_app.command("list")
def list_agents():
    """List all agents."""
    client = get_client()
    try:
        agents = client.list_agents()
        if not agents:
            console.print("[dim]No agents configured.[/dim]")
            return

        table = Table(title="Agents", show_header=True)
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Runner")
        table.add_column("Model")
        table.add_column("Temperature")
        table.add_column("Created")

        for a in agents:
            table.add_row(
                a["id"],
                a["name"],
                a["runner"],
                a.get("model") or "-",
                str(a.get("temperature")) if a.get("temperature") is not None else "-",
                _short_date(a["created_at"]),
            )
        console.print(table)
    except Exception as e:
        _handle_error(e)


@agent_app.command("show")
def show(
    identifier: str = typer.Argument(..., help="Agent ID or name"),
):
    """Show agent details."""
    client = get_client()
    try:
        a = client.get_agent(identifier)
        panel = Panel.fit(
            f"[bold]Name:[/bold] {a['name']}\n"
            f"[bold]ID:[/bold] {a['id']}\n"
            f"[bold]Runner:[/bold] {a['runner']}\n"
            f"[bold]Model:[/bold] {a.get('model') or '-'}\n"
            f"[bold]System Prompt:[/bold]\n{a.get('system_prompt') or '(none)'}\n"
            f"[bold]Temperature:[/bold] {a.get('temperature', '-')}\n"
            f"[bold]Max Tokens:[/bold] {a.get('max_tokens', '-')}\n"
            f"[bold]Created:[/bold] {a['created_at']}\n"
            f"[bold]Updated:[/bold] {a['updated_at']}",
            title=f"Agent: {a['name']}",
            border_style="blue",
        )
        console.print(panel)
    except Exception as e:
        _handle_error(e)


@agent_app.command("edit")
def edit(
    identifier: str = typer.Argument(..., help="Agent ID or name"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New name"),
    runner: Optional[str] = typer.Option(None, "--runner", "-r", help="New runner type"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="New model"),
    system_prompt: Optional[str] = typer.Option(None, "--system-prompt", "-s", help="New system prompt"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="New temperature"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="New max tokens"),
):
    """Edit an existing agent."""
    client = get_client()
    updates = {}
    if name is not None:
        updates["name"] = name
    if runner is not None:
        updates["runner"] = runner
    if model is not None:
        updates["model"] = model
    if system_prompt is not None:
        updates["system_prompt"] = system_prompt
    if temperature is not None:
        updates["temperature"] = temperature
    if max_tokens is not None:
        updates["max_tokens"] = max_tokens

    if not updates:
        console.print("[yellow]No changes specified.[/yellow]")
        raise typer.Exit(0)

    try:
        agent = client.update_agent(identifier, **updates)
        console.print(f"[green]OK[/green] Agent updated: [bold]{agent['name']}[/bold]")
    except Exception as e:
        _handle_error(e)


@agent_app.command("delete")
def delete(
    identifier: str = typer.Argument(..., help="Agent ID or name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete an agent."""
    if not force:
        typer.confirm(
            f"WARNING:  Delete agent '{identifier}'?",
            abort=True,
        )
    client = get_client()
    try:
        client.delete_agent(identifier)
        console.print(f"[green]OK[/green] Agent deleted: {identifier}")
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
