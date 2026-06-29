"""Ask and Chat CLI commands — interact with AI agents.

Provides `forge ask` (one-shot) and `forge chat` (interactive) commands.
Supports --stream for real-time WebSocket event streaming.
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Optional

import typer
import websockets
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from forge.cli.api_client import get_client
from forge.core.config import settings

console = Console()


# ── ask command ──────────────────────────────────────────────────

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
    stream: bool = typer.Option(
        True, "--stream/--no-stream", help="Stream output in real-time via WebSocket"
    ),
):
    """Send a prompt to an AI agent and get a response.

    With --stream (default), shows tool calls and text as they happen via WebSocket.

    Examples:
        forge ask "Summarize this project" --project myrepo --agent coding
        forge ask "Fix tests" --session ses_abc123 --project myrepo --agent coding
    """
    client = get_client()

    try:
        if session:
            ses = client.get_session(session)
            session_id = ses["id"]
            console.print(f"[dim]Resumed session: {session_id}[/dim]")
        else:
            ses = client.create_session(
                project=project, agent=agent,
                title=title or f"ask: {prompt[:50]}",
            )
            session_id = ses["id"]
            console.print(f"[dim]Created session: {session_id}[/dim]")

        console.print(f"\n[bold green]You:[/bold green] {prompt}\n")

        if stream:
            _run_with_ws_stream(session_id, prompt)
        else:
            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                client.run_turn(session_id, prompt)
            _print_last_assistant(client, session_id)

    except Exception as e:
        _handle_error(e)


# ── chat command ─────────────────────────────────────────────────

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

    Type /exit to quit, /history for messages, /status for session info.

    Examples:
        forge chat --project myrepo --agent coding
        forge chat --session ses_abc123 --project myrepo --agent coding
    """
    client = get_client()

    try:
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
                project=project, agent=agent,
                title=title or "Interactive chat",
            )
            session_id = ses["id"]
            console.print(f"[dim]Created session: {session_id}[/dim]")

        console.print(
            "\n[bold]Chat started.[/bold] Type [cyan]/exit[/cyan] to quit, "
            "[cyan]/help[/cyan] for commands.\n"
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
            _run_with_ws_stream(session_id, user_input)

    except Exception as e:
        _handle_error(e)


# ── WebSocket streaming ──────────────────────────────────────────

def _run_with_ws_stream(session_id: str, prompt: str):
    """Start a turn via REST, then stream events via WebSocket."""
    client = get_client()

    # Start the turn in a background thread (REST POST blocks until done without WS)
    turn_started = threading.Event()
    turn_error: Optional[str] = None

    def start_turn():
        nonlocal turn_error
        try:
            client.run_turn(session_id, prompt)
        except Exception as e:
            turn_error = str(e)
        finally:
            turn_started.set()

    # We need to start the REST call in background, then immediately connect WS
    # But run_turn is synchronous and blocking. So we fire the REST call,
    # then connect WS to catch the events as they're emitted.

    # Actually, the REST call IS the turn. Events are emitted during its execution.
    # For true streaming, we need: fire REST in thread, connect WS to listen.

    thread = threading.Thread(target=start_turn, daemon=True)
    thread.start()

    # Give the REST call a moment to start the Claude process
    import time
    time.sleep(0.3)

    # Connect WebSocket and stream
    asyncio.run(_ws_stream(session_id))

    # Wait for turn to complete
    thread.join(timeout=300)

    if turn_error:
        console.print(f"\n[red]Turn error:[/red] {turn_error}")


async def _ws_stream(session_id: str):
    """Async: connect to WebSocket and display events in real-time."""
    ws_url = f"ws://{settings.host}:{settings.port}/ws"

    try:
        async with websockets.connect(ws_url) as ws:
            # Read connected message
            msg = json.loads(await ws.recv())

            # Subscribe to session
            await ws.send(json.dumps({
                "type": "subscribe_session",
                "session_id": session_id,
                "after_seq": 0,
            }))
            ack = json.loads(await ws.recv())

            tool_ids: set[str] = set()

            # Stream events
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=300)
                except asyncio.TimeoutError:
                    break

                data = json.loads(raw)
                if data.get("type") == "replay_done":
                    continue
                if data.get("type") != "event":
                    continue

                event = data.get("event", {})
                etype = event.get("type", "")
                payload = event.get("payload", {})

                if etype == "assistant_text_delta":
                    text = payload.get("text", "")
                    if text:
                        console.print(text, end="", highlight=False)

                elif etype == "tool_call_started":
                    console.print()  # newline after text
                    tid = payload.get("id", "")
                    if tid not in tool_ids:
                        tool_ids.add(tid)
                        cmd = payload.get("input", {}).get("command", "") if isinstance(payload.get("input"), dict) else str(payload.get("input", ""))[:300]
                        console.print(Panel(
                            f"[bold yellow]{payload.get('tool', 'unknown')}[/bold yellow]\n{cmd}",
                            title="Tool Call", border_style="yellow",
                        ))

                elif etype == "tool_result":
                    content = str(payload.get("content", ""))[:1000]
                    is_err = payload.get("is_error", False)
                    console.print(Panel(
                        content + ("..." if len(str(payload.get("content", ""))) > 1000 else ""),
                        title="Result", border_style="red" if is_err else "green",
                    ))

                elif etype == "error":
                    console.print(f"\n[red]Error:[/red] {payload.get('error', '')}")

                elif etype == "session_status" and payload.get("status") == "completed":
                    console.print("\n[dim]Done.[/dim]")
                    break

    except websockets.ConnectionClosed:
        pass
    except Exception as e:
        console.print(f"\n[dim]Stream ended: {e}[/dim]")


# ── helpers ──────────────────────────────────────────────────────

def _print_last_assistant(client, session_id: str):
    """Print the last assistant message from a session."""
    messages = client.get_messages(session_id)
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    if assistant_msgs:
        console.print("[bold blue]Assistant:[/bold blue]")
        content = assistant_msgs[-1].get("content", "")
        if content:
            try:
                console.print(Markdown(content))
            except Exception:
                console.print(content)
        console.print()
    else:
        console.print("[dim](No response)[/dim]")


def _handle_slash(cmd: str, client, session_id: str) -> bool:
    """Handle slash commands. Returns True to exit."""
    parts = cmd.strip().split()
    command = parts[0].lower()

    if command in ("/exit", "/quit"):
        console.print("[dim]Goodbye![/dim]")
        return True
    elif command == "/help":
        console.print("""
[bold]Commands:[/bold]
  [cyan]/exit[/cyan]     — Quit
  [cyan]/history[/cyan]  — Show messages
  [cyan]/status[/cyan]   — Session status
  [cyan]/help[/cyan]     — This help
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
        console.print(f"[dim]Unknown: {command}[/dim]")
    return False


def _handle_error(e: Exception) -> None:
    import httpx
    if isinstance(e, httpx.HTTPStatusError):
        try:
            detail = e.response.json().get("detail", {})
            msg = detail.get("message", str(e)) if isinstance(detail, dict) else str(detail)
        except Exception:
            msg = str(e)
        console.print(f"[red]Error:[/red] {msg}")
    else:
        console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(1)
