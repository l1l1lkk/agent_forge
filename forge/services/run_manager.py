"""RunManager — manages async AI turns without blocking HTTP requests."""

from __future__ import annotations

import asyncio
import logging

from forge.core.errors import ConflictError
from forge.core.event_bus import event_bus
from forge.core.events import Event
from forge.db.base import async_session_factory
from forge.db.repositories.event_repo import EventRepo
from forge.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

_running: dict[str, asyncio.Task] = {}


class RunManager:
    """Starts AI turns as background tasks, returns immediately.

    Does NOT store a db session — each background task creates its own.
    """

    @staticmethod
    async def start_run(session_id: str, prompt: str) -> dict:
        """Start an async AI turn. Returns run status immediately."""
        if session_id in _running and not _running[session_id].done():
            raise ConflictError(f"Session {session_id} is already running")

        async def _run():
            # Create a fresh db session for the background task
            async with async_session_factory() as db:
                try:
                    mgr = SessionManager(db)
                    # Verify session exists, reset stuck status if needed
                    session = await mgr.get_session(session_id)
                    if session.status == "running":
                        await mgr.update_status(session_id, "idle")

                    result = await mgr.run_turn(session_id=session_id, user_prompt=prompt)
                    # Explicitly commit — async_session_factory does NOT auto-commit
                    await db.commit()

                    if not result.success:
                        await event_bus.publish(Event(
                            type="error", session_id=session_id, seq=0,
                            payload={"error": result.error or "Unknown error"},
                        ))
                except Exception as e:
                    logger.exception("Background run failed: %s", e)
                    await db.rollback()
                finally:
                    _running.pop(session_id, None)

        task = asyncio.create_task(_run())
        _running[session_id] = task

        return {"run_id": f"run_{session_id}", "session_id": session_id, "status": "running"}

    @staticmethod
    def is_running(session_id: str) -> bool:
        return session_id in _running and not _running[session_id].done()

    @staticmethod
    async def interrupt(session_id: str) -> None:
        task = _running.get(session_id)
        if task and not task.done():
            task.cancel()
        _running.pop(session_id, None)


async def get_session_events(db: AsyncSession, session_id: str, after_seq: int = 0) -> list[dict]:
    """Return session events for timeline replay."""
    repo = EventRepo(db)
    items, _ = await repo.list_by_session(session_id, after_seq=after_seq, limit=200)
    import json
    return [{
        "id": e.id, "type": e.type, "seq": e.seq,
        "session_id": e.session_id, "task_id": e.task_id,
        "payload": json.loads(e.payload_json) if e.payload_json else {},
        "created_at": e.created_at,
    } for e in items]
