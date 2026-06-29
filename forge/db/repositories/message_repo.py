"""Repository for message CRUD operations."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.db.models import MessageModel


class MessageRepo:
    """Async CRUD repository for messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, message: MessageModel) -> MessageModel:
        """Insert a new message."""
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_by_id(self, message_id: str) -> Optional[MessageModel]:
        """Get a message by its ID."""
        result = await self.db.execute(
            select(MessageModel).where(MessageModel.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_next_seq(self, session_id: str) -> int:
        """Get the next sequence number for a session."""
        q = (
            select(func.coalesce(func.max(MessageModel.seq), 0))
            .where(MessageModel.session_id == session_id)
        )
        result = await self.db.execute(q)
        return (result.scalar() or 0) + 1

    async def list_by_session(
        self, session_id: str, offset: int = 0, limit: int = 500
    ) -> Tuple[Sequence[MessageModel], int]:
        """List messages for a session, ordered by seq. Returns (items, total)."""
        total_q = select(func.count()).select_from(MessageModel).where(
            MessageModel.session_id == session_id
        )
        total = (await self.db.execute(total_q)).scalar() or 0

        q = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.seq.asc())
            .offset(offset)
            .limit(limit)
        )
        items = (await self.db.execute(q)).scalars().all()
        return items, total

    async def delete(self, message: MessageModel) -> None:
        """Delete a message."""
        await self.db.delete(message)
        await self.db.flush()
