"""Ask and Chat CLI commands — interact with AI agents.

Provides `forge ask` (one-shot) and `forge chat` (interactive) commands.
These are registered as direct commands on the main Typer app.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from forge.cli.api_client import get_client

console = Console()


# These functions are registered in forge.cli.app as direct commands.
# They are NOT in a sub-typer to avoid double-nesting (forge ask ask "prompt").


def ask_command(
    prompt: str = typer.Argument(..., help="Your question or task"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project ID or name"
    ),
    agent: str = typer.Option(
        ..., "--agent", "-a", help="Agent ID or name"
    ),
    session: Optional[str] = typer.Option(
        None, "--session", "-s", help="Session ID (resume existing)"
    ),
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="Session title (for new sessions)"
    ),
    runner: Optional[str] = typer.Option(
        None, "--runner", "-r", help="Override runner"
    ),
):
    """Send a prompt to an AI agent and get a response.

    Creates a new session or resumes an existing one, then runs the AI turn.

    Examples:
        forge ask "Summarize this project" --project myrepo --agent coding
        forge ask "Fix the failing test" --session ses_abc123 --project myrepo --agent coding
    """
    client = get_client()

    try:
        # Create or resume session
        if session:
            ses = client.get_session(session)
            session_id = ses["id"]
            console.print(f"[dim]Resumed session: {session_id}[/dim]")
        else:
            ses = client.create_session(
                project=project,
                agent=agent,
                title=title or f"ask: {prompt[:50]}",
            )
            session_id = ses["id"]
            console.print(f"[dim]Created session: {session_id}[/dim]")

        # Run the turn
        console.print(f"\n[bold green]You:[/bold green] {prompt}\n")

        with console.status("[bold green]Agent is thinking...[/bold green]", spinner="dots"):
            client.run_turn(session_id, prompt)

        # Display the assistant response
        messages = client.get_messages(session_id)
        assistant_msgs = [m for m in messages if m["role"] == "assistant"]
        if assistant_msgs:
            console.print("[bold blue]Assistant:[/bold blue]")
            content = assistant_msgs[-1].get("content", "")
            if content:
                try:
                    md = Markdown(content)
                    console.print(md)
                except Exception:
                    console.print(content)
            console.print()
        else:
            console.print("[dim](No response from assistant)[/dim]")

    except Exception as e:
        _handle_error(e)


def chat_command(
    project: str = typer.Option(
        ..., "--project", "-p", help="Project ID or name"
    ),
    agent: str = typer.Option(
        ..., "--agent", "-a", help="Agent ID or name"
    ),
    session: Optional[str] = typer.Option(
        None, "--session", "-s", help="Session ID (resume existing)"
    ),
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="Session title"
    ),
):
    """Start an interactive chat with an AI agent.

    Type your prompts and the agent will respond.
    Type /exit to quit, /history to see message history, /status to check status.

    Examples:
        forge chat --project myrepo --agent coding
        forge chat --session ses_abc123 --project myrepo --agent coding
    """
    client = get_client()

    try:
        # Create or resume session
        if session:
            ses = client.get_session(session)
            session_id = ses["id"]
            console.print(f"[dim]Resumed session: {session_id}[/dim]")
            msgs = client.get_messages(session_id)
            for msg in msgs[-6:]:
                role = "[green]You[/green]" if msg["role"] == "user" else "[blue]AI[/blue]"
                console.print(f"  {role}: {msg.get('content', '')[:120]}")
        else:
            ses = client.create_session(
                project=project,
                agent=agent,
                title=title or "Interactive chat",
            )
            session_id = ses["id"]
            console.print(f"[dim]Created session: {session_id}[/dim]")

        console.print(
            "\n[bold]Chat started.[/bold] Type [cyan]/exit[/cyan] to quit, [cyan]/help[/cyan] for commands.\n"
        )

        while True:
            try:
                user_input = typer.prompt("You", prompt_suffix="> ")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Goodbye![/dim]")
                break

            if not user_input.strip():
                continue

            if user_input.startswith("/"):
                if _handle_slash(user_input, client, session_id):
                    break
                continue

            console.print()
            with console.status("[bold green]Agent is thinking...[/bold green]", spinner="dots"):
                client.run_turn(session_id, user_input)

            messages = client.get_messages(session_id)
            assistant_msgs = [m for m in messages if m["role"] == "assistant"]
            if assistant_msgs:
                console.print("[bold blue]Assistant:[/bold blue]")
                content = assistant_msgs[-1].get("content", "")
                if content:
                    try:
                        md = Markdown(content)
                        console.print(md)
                    except Exception:
                        console.print(content)
                console.print()
            else:
                console.print("[dim](No response)[/dim]")

    except Exception as e:
        _handle_error(e)


def _handle_slash(cmd: str, client, session_id: str) -> bool:
    """Handle slash commands. Returns True if should exit."""
    parts = cmd.strip().split()
    command = parts[0].lower()

    if command in ("/exit", "/quit"):
        console.print("[dim]Goodbye![/dim]")
        return True
    elif command == "/help":
        console.print("""
[bold]Available commands:[/bold]
  [cyan]/exit[/cyan]     — Quit
  [cyan]/history[/cyan]  — Show message history
  [cyan]/status[/cyan]   — Show session status
  [cyan]/help[/cyan]     — Show this help
""")
    elif command == "/history":
        msgs = client.get_messages(session_id)
        for msg in msgs:
            role = "[green]You[/green]" if msg["role"] == "user" else "[blue]AI[/blue]"
            console.print(f"  #{msg['seq']} {role}: {msg.get('content', '')[:150]}")
    elif command == "/status":
        ses = client.get_session(session_id)
        console.print(f"  Status: [bold]{ses['status']}[/bold]  Runner: {ses['runner']}")
    else:
        console.print(f"[dim]Unknown: {command}. Type /help[/dim]")
    return False


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
        console.print(f"[red]Error:[/red] {msg}")
    else:
        console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)
