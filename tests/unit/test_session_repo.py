"""Tests for SessionRepo and MessageRepo CRUD operations."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.ids import gen_id
from forge.db.models import (
    AgentModel,
    MessageModel,
    ProjectModel,
    SessionModel,
)
from forge.db.repositories.message_repo import MessageRepo
from forge.db.repositories.session_repo import SessionRepo


@pytest.mark.asyncio
class TestSessionRepo:
    """Tests for the session repository."""

    async def _create_project(self, db_session: AsyncSession) -> ProjectModel:
        p = ProjectModel(
            id=gen_id("project"),
            name="test-proj",
            root_path="/tmp/test",
        )
        db_session.add(p)
        await db_session.flush()
        return p

    async def _create_agent(self, db_session: AsyncSession) -> AgentModel:
        a = AgentModel(
            id=gen_id("agent"),
            name="test-agent",
            runner="codex",
        )
        db_session.add(a)
        await db_session.flush()
        return a

    async def test_create_session(self, db_session: AsyncSession):
        repo = SessionRepo(db_session)
        project = await self._create_project(db_session)
        agent = await self._create_agent(db_session)

        session = SessionModel(
            id=gen_id("session"),
            project_id=project.id,
            agent_id=agent.id,
            title="Test Session",
            status="idle",
            runner="codex",
        )
        created = await repo.create(session)
        assert created.status == "idle"
        assert created.project_id == project.id

    async def test_get_by_id_with_relations(self, db_session: AsyncSession):
        repo = SessionRepo(db_session)
        project = await self._create_project(db_session)
        agent = await self._create_agent(db_session)

        session = SessionModel(
            id=gen_id("session"),
            project_id=project.id,
            agent_id=agent.id,
            status="idle",
            runner="codex",
        )
        await repo.create(session)

        found = await repo.get_by_id(session.id, load_relations=True)
        assert found is not None
        assert found.project is not None
        assert found.project.name == "test-proj"

    async def test_list_by_project(self, db_session: AsyncSession):
        repo = SessionRepo(db_session)
        project = await self._create_project(db_session)
        agent = await self._create_agent(db_session)

        for i in range(2):
            s = SessionModel(
                id=gen_id("session"),
                project_id=project.id,
                agent_id=agent.id,
                status="idle",
                runner="codex",
            )
            await repo.create(s)

        items, total = await repo.list(project_id=project.id)
        assert total == 2

    async def test_update_status(self, db_session: AsyncSession):
        repo = SessionRepo(db_session)
        project = await self._create_project(db_session)
        agent = await self._create_agent(db_session)

        session = SessionModel(
            id=gen_id("session"),
            project_id=project.id,
            agent_id=agent.id,
            status="idle",
            runner="codex",
        )
        await repo.create(session)

        updated = await repo.update(session, status="running")
        assert updated.status == "running"

    async def test_delete_cascades(self, db_session: AsyncSession):
        repo = SessionRepo(db_session)
        msg_repo = MessageRepo(db_session)
        project = await self._create_project(db_session)
        agent = await self._create_agent(db_session)

        session = SessionModel(
            id=gen_id("session"),
            project_id=project.id,
            agent_id=agent.id,
            status="idle",
            runner="codex",
        )
        await repo.create(session)

        # Add a message
        msg = MessageModel(
            id=gen_id("message"),
            session_id=session.id,
            role="user",
            content="hello",
            seq=1,
        )
        await msg_repo.create(msg)

        # Delete the session
        await repo.delete(session)

        # Verify session is gone
        found = await repo.get_by_id(session.id)
        assert found is None

        # Messages should cascade-delete
        msgs, _ = await msg_repo.list_by_session(session.id)
        assert len(msgs) == 0


@pytest.mark.asyncio
class TestMessageRepo:
    """Tests for the message repository."""

    async def test_get_next_seq(self, db_session: AsyncSession):
        repo = MessageRepo(db_session)
        session_id = "ses_test"

        # First message should get seq 1
        seq = await repo.get_next_seq(session_id)
        assert seq == 1

        # Add a message
        msg = MessageModel(
            id=gen_id("message"),
            session_id=session_id,
            role="user",
            content="test",
            seq=1,
        )
        await repo.create(msg)

        # Next should be 2
        seq = await repo.get_next_seq(session_id)
        assert seq == 2

    async def test_list_by_session_ordered(self, db_session: AsyncSession):
        repo = MessageRepo(db_session)
        session_id = "ses_test"

        for i, role in enumerate(["user", "assistant", "user"], start=1):
            msg = MessageModel(
                id=gen_id("message"),
                session_id=session_id,
                role=role,
                content=f"msg {i}",
                seq=i,
            )
            await repo.create(msg)

        items, total = await repo.list_by_session(session_id)
        assert total == 3
        assert [m.seq for m in items] == [1, 2, 3]
