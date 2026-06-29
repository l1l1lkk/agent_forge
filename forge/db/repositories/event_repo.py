"""Repository for event CRUD operations."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.db.models import EventModel


class EventRepo:
    """Async CRUD repository for events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event: EventModel) -> EventModel:
        """Insert a new event."""
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_by_id(self, event_id: str) -> Optional[EventModel]:
        """Get an event by its ID."""
        result = await self.db.execute(
            select(EventModel).where(EventModel.id == event_id)
        )
        return result.scalar_one_or_none()

    async def list_by_session(
        self,
        session_id: str,
        after_seq: int = 0,
        offset: int = 0,
        limit: int = 1000,
    ) -> Tuple[Sequence[EventModel], int]:
        """List events for a session, ordered by seq. Returns (items, total)."""
        total_q = (
            select(func.count())
            .select_from(EventModel)
            .where(EventModel.session_id == session_id)
        )
        if after_seq > 0:
            total_q = total_q.where(EventModel.seq > after_seq)
        total = (await self.db.execute(total_q)).scalar() or 0

        q = (
            select(EventModel)
            .where(EventModel.session_id == session_id)
        )
        if after_seq > 0:
            q = q.where(EventModel.seq > after_seq)
        q = q.order_by(EventModel.seq.asc()).offset(offset).limit(limit)
        items = (await self.db.execute(q)).scalars().all()
        return items, total
