"""Repository for session CRUD operations."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from forge.db.models import SessionModel


class SessionRepo:
    """Async CRUD repository for sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: SessionModel) -> SessionModel:
        """Insert a new session."""
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id(
        self, session_id: str, load_relations: bool = True
    ) -> Optional[SessionModel]:
        """Get a session by its ID, optionally eager-loading messages."""
        q = select(SessionModel).where(SessionModel.id == session_id)
        if load_relations:
            q = q.options(
                selectinload(SessionModel.messages),
                selectinload(SessionModel.project),
                selectinload(SessionModel.agent),
            )
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def list(
        self,
        project_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[Sequence[SessionModel], int]:
        """List sessions, optionally filtered by project. Returns (items, total)."""
        total_q = select(func.count()).select_from(SessionModel)
        q = select(SessionModel)

        if project_id:
            total_q = total_q.where(SessionModel.project_id == project_id)
            q = q.where(SessionModel.project_id == project_id)

        total = (await self.db.execute(total_q)).scalar() or 0

        q = (
            q.order_by(SessionModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = (await self.db.execute(q)).scalars().all()
        return items, total

    async def update(
        self, session: SessionModel, **kwargs
    ) -> SessionModel:
        """Update session fields."""
        for key, value in kwargs.items():
            if hasattr(session, key) and value is not None:
                setattr(session, key, value)
        await self.db.flush()
        return session

    async def delete(self, session: SessionModel) -> None:
        """Delete a session and cascade to its messages/events."""
        await self.db.delete(session)
        await self.db.flush()
