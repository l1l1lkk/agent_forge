"""Project management service.

Orchestrates project CRUD operations with validation and path resolution.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.errors import ConflictError, NotFoundError, ValidationError
from forge.core.ids import gen_id
from forge.db.models import ProjectModel
from forge.db.repositories.project_repo import ProjectRepo


class ProjectManager:
    """Manages project lifecycle: create, list, get, update, delete."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepo(db)

    async def add_project(
        self,
        root_path: str | Path,
        name: Optional[str] = None,
        **kwargs,
    ) -> ProjectModel:
        """Add a new project.

        Args:
            root_path: Absolute or relative path to the project directory.
            name: Human-readable name. Defaults to the directory name.
            **kwargs: Additional fields (default_runner, allowed_paths, etc.)

        Returns:
            The created ProjectModel.

        Raises:
            ValidationError: If the path does not exist or is not a directory.
            ConflictError: If a project with the given name already exists.
        """
        resolved = Path(root_path).expanduser().resolve()
        if not resolved.exists():
            raise ValidationError(f"Path does not exist: {resolved}")
        if not resolved.is_dir():
            raise ValidationError(f"Path is not a directory: {resolved}")

        project_name = name or resolved.name

        existing = await self.repo.get_by_name(project_name)
        if existing is not None:
            raise ConflictError(f"Project already exists: {project_name}")

        project = ProjectModel(
            id=gen_id("project"),
            name=project_name,
            root_path=str(resolved),
            created_at=_utc_iso(),
            updated_at=_utc_iso(),
            **kwargs,
        )
        return await self.repo.create(project)

    async def list_projects(self) -> Sequence[ProjectModel]:
        """List all projects."""
        items, _ = await self.repo.list()
        return items

    async def get_project(self, identifier: str) -> ProjectModel:
        """Get a project by ID or name.

        Args:
            identifier: Project ID (proj_xxx) or name.

        Returns:
            The ProjectModel.

        Raises:
            NotFoundError: If no project matches.
        """
        project = None
        if identifier.startswith("proj_"):
            project = await self.repo.get_by_id(identifier)
        if project is None:
            project = await self.repo.get_by_name(identifier)
        if project is None:
            raise NotFoundError("Project", identifier)
        return project

    async def update_project(
        self, identifier: str, **kwargs
    ) -> ProjectModel:
        """Update project fields.

        Args:
            identifier: Project ID or name.
            **kwargs: Fields to update (name, default_runner, env_json, etc.)

        Returns:
            The updated ProjectModel.
        """
        project = await self.get_project(identifier)
        project.updated_at = _utc_iso()
        return await self.repo.update(project, **kwargs)

    async def remove_project(self, identifier: str) -> None:
        """Delete a project and all associated data.

        Args:
            identifier: Project ID or name.
        """
        project = await self.get_project(identifier)
        await self.repo.delete(project)

    async def set_env(self, identifier: str, env_vars: dict[str, str]) -> ProjectModel:
        """Set environment variables for a project.

        Args:
            identifier: Project ID or name.
            env_vars: Dict of env var name → value.

        Returns:
            The updated ProjectModel.
        """
        project = await self.get_project(identifier)
        current = {}
        if project.env_json:
            try:
                current = json.loads(project.env_json)
            except json.JSONDecodeError:
                pass
        current.update(env_vars)
        project.env_json = json.dumps(current)
        project.updated_at = _utc_iso()
        return await self.repo.update(project)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
