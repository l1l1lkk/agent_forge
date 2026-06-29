"""Schedule management CLI commands."""

import typer
from rich.console import Console
from rich.table import Table
from forge.cli.api_client import get_client

schedule_app = typer.Typer(name="schedule", help="Manage scheduled tasks")
console = Console()


@schedule_app.command("create")
def create(
    name: str = typer.Option(..., "--name", "-n"),
    project: str = typer.Option(..., "--project", "-p"),
    agent: str = typer.Option(..., "--agent", "-a"),
    cron: str = typer.Option(..., "--cron", "-c"),
    prompt: str = typer.Option(..., "--prompt", "-m"),
):
    client = get_client()
    try:
        p = client.get_project(project)
        a = client.get_agent(agent)
        client._make_post("/api/schedules", {
            "name": name, "project_id": p["id"], "agent_id": a["id"],
            "cron": cron, "prompt": prompt,
        })
        console.print(f"[green]Schedule created:[/green] {name}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@schedule_app.command("list")
def list_schedules():
    client = get_client()
    try:
        r = client._make_get("/api/schedules")
        items = r.get("schedules", [])
        if not items:
            console.print("[dim]No schedules.[/dim]")
            return
        table = Table(title="Schedules")
        table.add_column("Name"); table.add_column("Cron"); table.add_column("Enabled"); table.add_column("Prompt")
        for s in items:
            table.add_row(s["name"], s["cron"], "Yes" if s["enabled"] else "No", s["prompt"][:60])
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@schedule_app.command("pause")
def pause(name: str = typer.Argument(...)):
    client = get_client()
    try:
        client._make_post(f"/api/schedules/{name}/pause")
        console.print(f"[green]Paused:[/green] {name}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@schedule_app.command("resume")
def resume(name: str = typer.Argument(...)):
    client = get_client()
    try:
        client._make_post(f"/api/schedules/{name}/resume")
        console.print(f"[green]Resumed:[/green] {name}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@schedule_app.command("delete")
def delete(name: str = typer.Argument(...), force: bool = typer.Option(False, "--force", "-f")):
    if not force:
        typer.confirm(f"Delete schedule '{name}'?", abort=True)
    client = get_client()
    try:
        import httpx
        with httpx.Client() as c:
            c.delete(client._url(f"/api/schedules/{name}"), headers=client._headers()).raise_for_status()
        console.print(f"[green]Deleted:[/green] {name}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
