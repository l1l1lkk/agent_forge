"""WebSocket API routes — real-time event streaming.

Clients subscribe to session events and receive them as they're emitted
by runners during AI turns.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from forge.core.event_bus import event_bus
from forge.core.events import Event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming.

    Client sends:
      {"type": "subscribe_session", "session_id": "ses_xxx"}
      {"type": "send_message", "session_id": "ses_xxx", "content": "prompt"}

    Server sends:
      {"type": "connected", "message": "..."}
      {"type": "event", "event": {...}}  (streamed events)
      {"type": "error", "message": "..."}
    """
    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "WebSocket connected"})

    subscribed_sessions: set[str] = set()
    event_task: asyncio.Task | None = None

    async def event_listener(session_id: str):
        """Listen to events for a session and forward to WebSocket."""
        try:
            async for event in event_bus.subscribe(session_id):
                try:
                    await websocket.send_json({
                        "type": "event",
                        "event": event.to_dict(),
                    })
                except Exception:
                    break  # Client disconnected
        except asyncio.CancelledError:
            pass

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "subscribe_session":
                session_id = data.get("session_id", "")
                if session_id and session_id not in subscribed_sessions:
                    subscribed_sessions.add(session_id)
                    # Start background listener
                    if event_task is None or event_task.done():
                        event_task = asyncio.create_task(event_listener(session_id))
                    await websocket.send_json({
                        "type": "subscribed",
                        "session_id": session_id,
                    })

            elif msg_type == "send_message":
                # Client wants to send a message through the WebSocket
                # This is handled by the REST API; here we just acknowledge
                await websocket.send_json({
                    "type": "info",
                    "message": "Use POST /api/sessions/{id}/messages with run=true to send",
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    finally:
        if event_task and not event_task.done():
            event_task.cancel()
