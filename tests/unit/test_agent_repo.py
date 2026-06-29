"""Tests for AgentRepo CRUD operations."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.ids import gen_id
from forge.db.models import AgentModel
from forge.db.repositories.agent_repo import AgentRepo


@pytest.mark.asyncio
class TestAgentRepo:
    """Tests for the agent repository."""

    async def test_create_agent(self, db_session: AsyncSession):
        repo = AgentRepo(db_session)
        agent = AgentModel(
            id=gen_id("agent"),
            name="coding-agent",
            runner="codex",
            model="gpt-5.5",
        )
        created = await repo.create(agent)
        assert created.name == "coding-agent"
        assert created.runner == "codex"

    async def test_get_by_id(self, db_session: AsyncSession):
        repo = AgentRepo(db_session)
        agent = AgentModel(
            id=gen_id("agent"),
            name="test-agent",
            runner="codex",
        )
        await repo.create(agent)

        found = await repo.get_by_id(agent.id)
        assert found is not None
        assert found.name == "test-agent"

    async def test_get_by_name(self, db_session: AsyncSession):
        repo = AgentRepo(db_session)
        agent = AgentModel(
            id=gen_id("agent"),
            name="unique-agent",
            runner="claude",
        )
        await repo.create(agent)

        found = await repo.get_by_name("unique-agent")
        assert found is not None
        assert found.runner == "claude"

    async def test_list(self, db_session: AsyncSession):
        repo = AgentRepo(db_session)
        for runner in ["codex", "claude", "openai-compatible"]:
            a = AgentModel(
                id=gen_id("agent"),
                name=f"agent-{runner}",
                runner=runner,
            )
            await repo.create(a)

        items, total = await repo.list()
        assert total == 3

    async def test_update(self, db_session: AsyncSession):
        repo = AgentRepo(db_session)
        agent = AgentModel(
            id=gen_id("agent"),
            name="v1-agent",
            runner="codex",
        )
        await repo.create(agent)

        updated = await repo.update(agent, model="claude-sonnet-4-6", temperature=0.7)
        assert updated.model == "claude-sonnet-4-6"
        assert updated.temperature == 0.7

    async def test_delete(self, db_session: AsyncSession):
        repo = AgentRepo(db_session)
        agent = AgentModel(
            id=gen_id("agent"),
            name="delete-me",
            runner="codex",
        )
        await repo.create(agent)

        await repo.delete(agent)
        found = await repo.get_by_id(agent.id)
        assert found is None
