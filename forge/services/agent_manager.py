"""Agent management service.

Orchestrates agent CRUD operations with validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.errors import ConflictError, NotFoundError
from forge.core.ids import gen_id
from forge.db.models import AgentModel
from forge.db.repositories.agent_repo import AgentRepo


class AgentManager:
    """Manages agent lifecycle: create, list, get, update, delete."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AgentRepo(db)

    async def create_agent(
        self,
        name: str,
        runner: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AgentModel:
        """Create a new agent.

        Args:
            name: Unique agent name.
            runner: Runner type (codex, claude, openai-compatible, etc.)
            model: Model identifier.
            system_prompt: System prompt for the agent.
            temperature: Sampling temperature.
            max_tokens: Max output tokens.

        Returns:
            The created AgentModel.

        Raises:
            ConflictError: If an agent with the given name already exists.
        """
        existing = await self.repo.get_by_name(name)
        if existing is not None:
            raise ConflictError(f"Agent already exists: {name}")

        agent = AgentModel(
            id=gen_id("agent"),
            name=name,
            runner=runner,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            created_at=_utc_iso(),
            updated_at=_utc_iso(),
            **kwargs,
        )
        return await self.repo.create(agent)

    async def list_agents(self) -> Sequence[AgentModel]:
        """List all agents."""
        items, _ = await self.repo.list()
        return items

    async def get_agent(self, identifier: str) -> AgentModel:
        """Get an agent by ID or name.

        Args:
            identifier: Agent ID (agent_xxx) or name.

        Returns:
            The AgentModel.

        Raises:
            NotFoundError: If no agent matches.
        """
        agent = None
        if identifier.startswith("agent_"):
            agent = await self.repo.get_by_id(identifier)
        if agent is None:
            agent = await self.repo.get_by_name(identifier)
        if agent is None:
            raise NotFoundError("Agent", identifier)
        return agent

    async def update_agent(self, identifier: str, **kwargs) -> AgentModel:
        """Update agent fields.

        Args:
            identifier: Agent ID or name.
            **kwargs: Fields to update.

        Returns:
            The updated AgentModel.
        """
        agent = await self.get_agent(identifier)
        agent.updated_at = _utc_iso()
        return await self.repo.update(agent, **kwargs)

    async def delete_agent(self, identifier: str) -> None:
        """Delete an agent.

        Args:
            identifier: Agent ID or name.
        """
        agent = await self.get_agent(identifier)
        await self.repo.delete(agent)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
