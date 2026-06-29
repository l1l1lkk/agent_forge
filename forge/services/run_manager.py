"""RunManager — manages async AI turns without blocking HTTP requests."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.errors import NotFoundError, ConflictError
from forge.core.ids import gen_id
from forge.core.event_bus import event_bus
from forge.core.events import Event
from forge.db.models import EventModel
from forge.db.repositories.event_repo import EventRepo
from forge.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

_running: dict[str, asyncio.Task] = {}


class RunManager:
    """Starts AI turns as background tasks, returns immediately."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_run(self, session_id: str, prompt: str) -> dict:
        """Start an async AI turn. Returns run status immediately."""
        if session_id in _running and not _running[session_id].done():
            raise ConflictError(f"Session {session_id} is already running")

        mgr = SessionManager(self.db)

        # Verify session exists, reset stuck status if needed
        session = await mgr.get_session(session_id)
        if session.status == "running":
            # Reset stuck session
            await mgr.update_status(session_id, "idle")
        async def _run():
            try:
                result = await mgr.run_turn(session_id=session_id, user_prompt=prompt)
                if not result.success:
                    await event_bus.publish(Event(
                        type="error", session_id=session_id, seq=0,
                        payload={"error": result.error or "Unknown error"},
                    ))
            except Exception as e:
                logger.exception("Background run failed: %s", e)
                try:
                    await mgr.update_status(session_id, "error")
                except Exception:
                    pass
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
        mgr = SessionManager(None)  # placeholder — actual interrupt needs db
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
