"""Repository for agent CRUD operations."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.db.models import AgentModel


class AgentRepo:
    """Async CRUD repository for agents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, agent: AgentModel) -> AgentModel:
        """Insert a new agent."""
        self.db.add(agent)
        await self.db.flush()
        return agent

    async def get_by_id(self, agent_id: str) -> Optional[AgentModel]:
        """Get an agent by its ID."""
        result = await self.db.execute(
            select(AgentModel).where(AgentModel.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[AgentModel]:
        """Get an agent by its unique name."""
        result = await self.db.execute(
            select(AgentModel).where(AgentModel.name == name)
        )
        return result.scalar_one_or_none()

    async def list(
        self, offset: int = 0, limit: int = 100
    ) -> Tuple[Sequence[AgentModel], int]:
        """List agents with pagination. Returns (items, total)."""
        total_q = select(func.count()).select_from(AgentModel)
        total = (await self.db.execute(total_q)).scalar() or 0

        q = (
            select(AgentModel)
            .order_by(AgentModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = (await self.db.execute(q)).scalars().all()
        return items, total

    async def update(
        self, agent: AgentModel, **kwargs
    ) -> AgentModel:
        """Update agent fields."""
        for key, value in kwargs.items():
            if hasattr(agent, key) and value is not None:
                setattr(agent, key, value)
        await self.db.flush()
        return agent

    async def delete(self, agent: AgentModel) -> None:
        """Delete an agent."""
        await self.db.delete(agent)
        await self.db.flush()
