"""Schedule API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from forge.api.deps import get_db
from forge.core.errors import NotFoundError, ConflictError
from forge.services.schedule_manager import ScheduleManager

router = APIRouter(prefix="/schedules", tags=["schedules"])


class ScheduleCreate(BaseModel):
    name: str
    project_id: str
    agent_id: str
    cron: str
    prompt: str
    enabled: bool = True


class ScheduleResponse(BaseModel):
    id: str
    name: str
    project_id: str
    agent_id: str
    cron: str
    prompt: str
    enabled: bool
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}


class ScheduleListResponse(BaseModel):
    schedules: list[ScheduleResponse]
    total: int


@router.get("", response_model=ScheduleListResponse)
async def list_schedules(db: AsyncSession = Depends(get_db)):
    mgr = ScheduleManager(db)
    items = await mgr.list()
    return ScheduleListResponse(
        schedules=[ScheduleResponse.model_validate(s) for s in items],
        total=len(items),
    )


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(body: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    mgr = ScheduleManager(db)
    try:
        s = await mgr.create(body.name, body.project_id, body.agent_id, body.cron, body.prompt, body.enabled)
        return ScheduleResponse.model_validate(s)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})


@router.post("/{name}/pause", response_model=ScheduleResponse)
async def pause_schedule(name: str, db: AsyncSession = Depends(get_db)):
    mgr = ScheduleManager(db)
    try:
        s = await mgr.pause(name)
        return ScheduleResponse.model_validate(s)
    except NotFoundError as e:
        raise HTTPException(404, detail={"code": e.code, "message": e.message})


@router.post("/{name}/resume", response_model=ScheduleResponse)
async def resume_schedule(name: str, db: AsyncSession = Depends(get_db)):
    mgr = ScheduleManager(db)
    try:
        s = await mgr.resume(name)
        return ScheduleResponse.model_validate(s)
    except NotFoundError as e:
        raise HTTPException(404, detail={"code": e.code, "message": e.message})


@router.delete("/{name}", status_code=204)
async def delete_schedule(name: str, db: AsyncSession = Depends(get_db)):
    mgr = ScheduleManager(db)
    try:
        await mgr.delete(name)
    except NotFoundError as e:
        raise HTTPException(404, detail={"code": e.code, "message": e.message})
