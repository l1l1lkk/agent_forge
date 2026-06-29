"""WebSocket client for CLI real-time event streaming."""

from __future__ import annotations

import asyncio
import json
from typing import Optional

import websockets
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from forge.core.config import settings


class WSClient:
    """Async WebSocket client for real-time event streaming from forge daemon."""

    def __init__(self, base_url: Optional[str] = None):
        ws_base = (base_url or f"http://{settings.host}:{settings.port}").replace("http://", "ws://").replace("https://", "wss://")
        self._ws_url = f"{ws_base}/ws"
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self.console = Console()

    async def connect(self) -> None:
        """Connect to the WebSocket endpoint."""
        self._ws = await websockets.connect(self._ws_url)
        # Read the connected message
        msg = await self._ws.recv()
        data = json.loads(msg)

    async def subscribe_session(self, session_id: str, after_seq: int = 0) -> None:
        """Subscribe to events for a session."""
        await self._ws.send(json.dumps({
            "type": "subscribe_session",
            "session_id": session_id,
            "after_seq": after_seq,
        }))
        # Read the subscribed ack
        await self._ws.recv()

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        if self._ws:
            await self._ws.close()

    async def stream_events(self, session_id: str) -> None:
        """Stream events for a session and display them in real-time.

        Shows:
        - Text deltas as they arrive (streaming text)
        - Tool calls with command/input
        - Tool results
        - Session status changes
        """
        await self.subscribe_session(session_id)

        tool_calls_displayed: set[str] = set()
        current_text: list[str] = []

        try:
            async for raw in self._ws:
                data = json.loads(raw)
                if data.get("type") != "event":
                    continue

                event = data.get("event", {})
                event_type = event.get("type", "")
                payload = event.get("payload", {})

                if event_type == "assistant_text_delta":
                    text = payload.get("text", "")
                    if text:
                        current_text.append(text)
                        # Print incrementally
                        self.console.print(text, end="", highlight=False)

                elif event_type == "tool_call_started":
                    # Flush accumulated text before showing tool call
                    if current_text:
                        self.console.print()
                        current_text.clear()

                    tool_name = payload.get("tool", "unknown")
                    tool_input = payload.get("input", {})
                    cmd = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)[:200]
                    tool_id = event.get("id", "")

                    if tool_id not in tool_calls_displayed:
                        tool_calls_displayed.add(tool_id)
                        panel = Panel(
                            f"[bold yellow]Tool:[/bold yellow] {tool_name}\n"
                            f"{cmd}",
                            title="Tool Call",
                            border_style="yellow",
                        )
                        self.console.print(panel)

                elif event_type == "tool_result":
                    tool_use_id = payload.get("tool_use_id", "")
                    content = payload.get("content", "")
                    is_error = payload.get("is_error", False)
                    border = "red" if is_error else "green"

                    if content:
                        display = content[:1000] + ("..." if len(content) > 1000 else "")
                        panel = Panel(
                            display,
                            title="Result",
                            border_style=border,
                        )
                        self.console.print(panel)

                elif event_type == "error":
                    self.console.print(f"\n[red]Error:[/red] {payload.get('error', 'Unknown error')}")

                elif event_type == "session_status":
                    status = payload.get("status", "")
                    if status == "completed":
                        self.console.print("\n[dim]Turn completed.[/dim]")

        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            self.console.print(f"\n[red]Stream error:[/red] {e}")


# Synchronous wrapper for CLI use
def stream_session(session_id: str, base_url: Optional[str] = None) -> None:
    """Synchronous entry point: stream session events to console."""
    client = WSClient(base_url)

    async def _run():
        await client.connect()
        try:
            await client.stream_events(session_id)
        finally:
            await client.disconnect()

    asyncio.run(_run())
