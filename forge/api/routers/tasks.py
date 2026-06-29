"""Task API routes — background shell tasks."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from forge.api.deps import get_db
from forge.api.schemas import ErrorResponse
from forge.core.errors import NotFoundError
from forge.services.task_manager import TaskManager

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    command: str = Field(..., description="Shell command to execute")
    cwd: str = Field(..., description="Working directory")
    name: str | None = Field(None)
    project_id: str | None = Field(None)
    session_id: str | None = Field(None)


class TaskResponse(BaseModel):
    id: str
    name: str | None
    command: str | None
    status: str
    pid: int | None
    exit_code: int | None
    started_at: str | None
    finished_at: str | None
    created_at: str
    session_id: str | None = None
    project_id: str | None = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    project_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    mgr = TaskManager(db)
    items = await mgr.list_tasks(project_id=project_id)
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in items],
        total=len(items),
    )


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    mgr = TaskManager(db)
    task = await mgr.start_task(
        command=body.command,
        cwd=body.cwd,
        name=body.name,
        project_id=body.project_id,
        session_id=body.session_id,
    )
    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    mgr = TaskManager(db)
    try:
        task = await mgr.get_task(task_id)
        return TaskResponse.model_validate(task)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: str, db: AsyncSession = Depends(get_db)):
    mgr = TaskManager(db)
    try:
        task = await mgr.cancel_task(task_id)
        return TaskResponse.model_validate(task)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})
