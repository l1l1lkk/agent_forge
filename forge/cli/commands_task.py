"""Task management CLI commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from forge.cli.api_client import get_client

task_app = typer.Typer(name="task", help="Manage background tasks")
console = Console()


@task_app.command("list")
def list_tasks(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project"),
):
    """List background tasks."""
    client = get_client()
    try:
        import httpx
        params = {}
        if project:
            # Resolve project name to ID
            try:
                p = client.get_project(project)
                params["project_id"] = p["id"]
            except Exception:
                params["project_id"] = project

        r = client._make_get("/api/tasks", params=params)
        tasks = r.get("tasks", [])

        if not tasks:
            console.print("[dim]No tasks found.[/dim]")
            return

        table = Table(title="Tasks")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Command")
        table.add_column("Exit")

        for t in tasks:
            status_color = {"running": "green", "completed": "blue", "failed": "red", "cancelled": "yellow"}.get(t["status"], "white")
            table.add_row(
                t["id"], t.get("name") or "-",
                f"[{status_color}]{t['status']}[/{status_color}]",
                (t.get("command") or "")[:60],
                str(t.get("exit_code") or "-"),
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@task_app.command("show")
def show(task_id: str = typer.Argument(..., help="Task ID")):
    """Show task details."""
    client = get_client()
    try:
        import httpx
        task = client._make_get(f"/api/tasks/{task_id}")
        from rich.panel import Panel
        console.print(Panel.fit(
            f"ID: {task['id']}\n"
            f"Name: {task.get('name') or '-'}\n"
            f"Status: {task['status']}\n"
            f"Command: {task.get('command') or '-'}\n"
            f"PID: {task.get('pid') or '-'}\n"
            f"Exit: {task.get('exit_code') or '-'}\n"
            f"Started: {task.get('started_at') or '-'}\n"
            f"Finished: {task.get('finished_at') or '-'}",
            title=f"Task: {task_id}",
            border_style="blue",
        ))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@task_app.command("cancel")
def cancel(task_id: str = typer.Argument(..., help="Task ID")):
    """Cancel a running task."""
    client = get_client()
    try:
        import httpx
        client._make_post(f"/api/tasks/{task_id}/cancel")
        console.print(f"[green]OK[/green] Task cancelled: {task_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
