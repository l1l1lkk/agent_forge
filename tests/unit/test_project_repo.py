"""Tests for ProjectRepo CRUD operations."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.ids import gen_id
from forge.db.models import ProjectModel
from forge.db.repositories.project_repo import ProjectRepo


@pytest.mark.asyncio
class TestProjectRepo:
    """Tests for the project repository."""

    async def test_create_project(self, db_session: AsyncSession):
        repo = ProjectRepo(db_session)
        project = ProjectModel(
            id=gen_id("project"),
            name="test-project",
            root_path="/tmp/test-project",
        )
        created = await repo.create(project)
        assert created.id == project.id
        assert created.name == "test-project"

    async def test_get_by_id(self, db_session: AsyncSession):
        repo = ProjectRepo(db_session)
        project = ProjectModel(
            id=gen_id("project"),
            name="test-project",
            root_path="/tmp/test-project",
        )
        await repo.create(project)

        found = await repo.get_by_id(project.id)
        assert found is not None
        assert found.name == "test-project"

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        repo = ProjectRepo(db_session)
        found = await repo.get_by_id("proj_nonexistent")
        assert found is None

    async def test_get_by_name(self, db_session: AsyncSession):
        repo = ProjectRepo(db_session)
        project = ProjectModel(
            id=gen_id("project"),
            name="my-special-project",
            root_path="/tmp/test",
        )
        await repo.create(project)

        found = await repo.get_by_name("my-special-project")
        assert found is not None
        assert found.id == project.id

    async def test_list(self, db_session: AsyncSession):
        repo = ProjectRepo(db_session)
        for i in range(3):
            p = ProjectModel(
                id=gen_id("project"),
                name=f"project-{i}",
                root_path=f"/tmp/project-{i}",
            )
            await repo.create(p)

        items, total = await repo.list()
        assert total == 3
        assert len(items) == 3

    async def test_update(self, db_session: AsyncSession):
        repo = ProjectRepo(db_session)
        project = ProjectModel(
            id=gen_id("project"),
            name="old-name",
            root_path="/tmp/test",
        )
        await repo.create(project)

        updated = await repo.update(project, name="new-name", default_runner="codex")
        assert updated.name == "new-name"
        assert updated.default_runner == "codex"

    async def test_delete(self, db_session: AsyncSession):
        repo = ProjectRepo(db_session)
        project = ProjectModel(
            id=gen_id("project"),
            name="to-delete",
            root_path="/tmp/test",
        )
        await repo.create(project)

        await repo.delete(project)
        found = await repo.get_by_id(project.id)
        assert found is None
