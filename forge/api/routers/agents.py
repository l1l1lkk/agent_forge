"""Agent API routes — CRUD for AI coding agents."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from forge.api.deps import get_db
from forge.api.schemas import (
    AgentCreate,
    AgentListResponse,
    AgentResponse,
    AgentUpdate,
    ErrorResponse,
)
from forge.core.errors import ConflictError, NotFoundError
from forge.services.agent_manager import AgentManager

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents(db: AsyncSession = Depends(get_db)):
    """List all agents."""
    mgr = AgentManager(db)
    items = await mgr.list_agents()
    return AgentListResponse(
        agents=[AgentResponse.model_validate(a) for a in items],
        total=len(items),
    )


@router.post(
    "",
    response_model=AgentResponse,
    status_code=201,
    responses={409: {"model": ErrorResponse}},
)
async def create_agent(
    body: AgentCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new agent."""
    mgr = AgentManager(db)
    try:
        agent = await mgr.create_agent(
            name=body.name,
            runner=body.runner,
            model=body.model,
            system_prompt=body.system_prompt,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
        return AgentResponse.model_validate(agent)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get an agent by ID or name."""
    mgr = AgentManager(db)
    try:
        agent = await mgr.get_agent(agent_id)
        return AgentResponse.model_validate(agent)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    responses={404: {"model": ErrorResponse}},
)
async def update_agent(
    agent_id: str,
    body: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update agent fields."""
    mgr = AgentManager(db)
    try:
        update_data = body.model_dump(exclude_unset=True, exclude_none=True)
        agent = await mgr.update_agent(agent_id, **update_data)
        return AgentResponse.model_validate(agent)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.delete(
    "/{agent_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an agent."""
    mgr = AgentManager(db)
    try:
        await mgr.delete_agent(agent_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})
