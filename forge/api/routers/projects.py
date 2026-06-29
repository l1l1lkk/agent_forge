"""Project API routes — CRUD for project workspaces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from forge.api.deps import get_db
from forge.api.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    ErrorResponse,
)
from forge.core.errors import ConflictError, NotFoundError, ValidationError
from forge.services.project_manager import ProjectManager

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all projects."""
    mgr = ProjectManager(db)
    items = await mgr.list_projects()
    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(p) for p in items],
        total=len(items),
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=201,
    responses={409: {"model": ErrorResponse}},
)
async def create_project(
    body: ProjectCreate, db: AsyncSession = Depends(get_db)
):
    """Add a new project."""
    mgr = ProjectManager(db)
    try:
        project = await mgr.add_project(
            root_path=body.root_path,
            name=body.name,
            default_runner=body.default_runner,
            allowed_paths=body.allowed_paths,
        )
        return ProjectResponse.model_validate(project)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get a project by ID or name."""
    mgr = ProjectManager(db)
    try:
        project = await mgr.get_project(project_id)
        return ProjectResponse.model_validate(project)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    responses={404: {"model": ErrorResponse}},
)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update project fields."""
    mgr = ProjectManager(db)
    try:
        update_data = body.model_dump(exclude_unset=True, exclude_none=True)
        project = await mgr.update_project(project_id, **update_data)
        return ProjectResponse.model_validate(project)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.delete(
    "/{project_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a project and all associated sessions/messages."""
    mgr = ProjectManager(db)
    try:
        await mgr.remove_project(project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})
