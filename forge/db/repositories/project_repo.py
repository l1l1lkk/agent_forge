"""Repository for project CRUD operations."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.db.models import ProjectModel


class ProjectRepo:
    """Async CRUD repository for projects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, project: ProjectModel) -> ProjectModel:
        """Insert a new project."""
        self.db.add(project)
        await self.db.flush()
        return project

    async def get_by_id(self, project_id: str) -> Optional[ProjectModel]:
        """Get a project by its ID."""
        result = await self.db.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[ProjectModel]:
        """Get a project by its unique name."""
        result = await self.db.execute(
            select(ProjectModel).where(ProjectModel.name == name)
        )
        return result.scalar_one_or_none()

    async def list(
        self, offset: int = 0, limit: int = 100
    ) -> Tuple[Sequence[ProjectModel], int]:
        """List projects with pagination. Returns (items, total)."""
        total_q = select(func.count()).select_from(ProjectModel)
        total = (await self.db.execute(total_q)).scalar() or 0

        q = (
            select(ProjectModel)
            .order_by(ProjectModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = (await self.db.execute(q)).scalars().all()
        return items, total

    async def update(
        self, project: ProjectModel, **kwargs
    ) -> ProjectModel:
        """Update project fields."""
        for key, value in kwargs.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        await self.db.flush()
        return project

    async def delete(self, project: ProjectModel) -> None:
        """Delete a project and cascade to its sessions/messages/events."""
        await self.db.delete(project)
        await self.db.flush()
