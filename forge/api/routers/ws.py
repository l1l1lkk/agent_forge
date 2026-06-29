"""WebSocket API routes — real-time event streaming with replay support.

Clients connect, subscribe to session events, and receive real-time updates.
Supports reconnection with event replay (after_seq parameter).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from forge.core.event_bus import event_bus
from forge.core.events import Event
from forge.db.models import EventModel
from forge.db.repositories.event_repo import EventRepo
from forge.db.session import async_session_factory

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming.

    Client → Server messages:
      {"type": "subscribe_session", "session_id": "ses_xxx", "after_seq": 0}
        Subscribe to events for a session. Optional after_seq replays missed events.

      {"type": "unsubscribe_session", "session_id": "ses_xxx"}
        Unsubscribe from a session.

      {"type": "send_message", "session_id": "ses_xxx", "content": "prompt"}
        Send a user prompt and trigger an AI turn (via REST API internally).

    Server → Client messages:
      {"type": "connected", "message": "..."}
      {"type": "subscribed", "session_id": "..."}
      {"type": "event", "event": {...}}
      {"type": "replay_done", "session_id": "...", "count": N}
      {"type": "error", "message": "..."}
    """
    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "forge-agent WebSocket v1"})

    # Track active subscription tasks: session_id → asyncio.Task
    sub_tasks: dict[str, asyncio.Task] = {}

    async def stream_events(session_id: str, after_seq: int = 0):
        """Background task: replay historical events then stream live ones."""
        try:
            # Step 1: Replay historical events from DB (for reconnection)
            if after_seq > 0:
                try:
                    async with async_session_factory() as db:
                        repo = EventRepo(db)
                        items, count = await repo.list_by_session(
                            session_id, after_seq=after_seq, limit=500
                        )
                        for evt in items:
                            await websocket.send_json({
                                "type": "event",
                                "event": {
                                    "id": evt.id,
                                    "type": evt.type,
                                    "seq": evt.seq,
                                    "session_id": evt.session_id,
                                    "task_id": evt.task_id,
                                    "payload": json.loads(evt.payload_json) if evt.payload_json else {},
                                    "created_at": evt.created_at,
                                },
                            })
                        if count > 0:
                            await websocket.send_json({
                                "type": "replay_done",
                                "session_id": session_id,
                                "count": count,
                            })
                except Exception as e:
                    logger.warning("Event replay failed for %s: %s", session_id, e)

            # Step 2: Stream live events
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
        except Exception as e:
            logger.error("Event stream error for %s: %s", session_id, e)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "subscribe_session":
                session_id = data.get("session_id", "")
                after_seq = data.get("after_seq", 0)

                if not session_id:
                    await websocket.send_json({"type": "error", "message": "session_id required"})
                    continue

                # Cancel existing subscription for this session
                if session_id in sub_tasks:
                    sub_tasks[session_id].cancel()
                    try:
                        await sub_tasks[session_id]
                    except asyncio.CancelledError:
                        pass

                # Start new streaming task
                task = asyncio.create_task(stream_events(session_id, after_seq))
                sub_tasks[session_id] = task

                await websocket.send_json({
                    "type": "subscribed",
                    "session_id": session_id,
                    "after_seq": after_seq,
                })
                logger.debug("WS subscribed to session %s (after_seq=%d)", session_id, after_seq)

            elif msg_type == "unsubscribe_session":
                session_id = data.get("session_id", "")
                if session_id in sub_tasks:
                    sub_tasks[session_id].cancel()
                    try:
                        await sub_tasks[session_id]
                    except asyncio.CancelledError:
                        pass
                    del sub_tasks[session_id]
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "session_id": session_id,
                    })

            elif msg_type == "send_message":
                # Client sent a message — acknowledge, actual processing via REST API
                await websocket.send_json({
                    "type": "info",
                    "message": "Use POST /api/sessions/{id}/messages?run=true to trigger turns",
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        # Clean up all subscription tasks
        for task in sub_tasks.values():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        sub_tasks.clear()
