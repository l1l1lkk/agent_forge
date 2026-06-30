"""Agent API routes — CRUD for AI coding agents."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
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
async def list_agents(
    include_archived: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """List all agents."""
    mgr = AgentManager(db)
    items = await mgr.list_agents()
    if not include_archived:
        items = [a for a in items if not _agent_policy(a).get("archived")]
    return AgentListResponse(
        agents=[_agent_response(a) for a in items],
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
            tool_policy_json=_agent_policy_json(
                description=body.description,
                avatar=body.avatar,
                mcp_servers=body.mcp_servers,
                tool_allow=body.tool_allow,
                tool_deny=body.tool_deny,
                archived=False,
            ),
        )
        return _agent_response(agent)
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
        return _agent_response(agent)
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
        policy_keys = {"description", "avatar", "mcp_servers", "tool_allow", "tool_deny", "archived"}
        policy_updates = {k: update_data.pop(k) for k in list(update_data.keys()) if k in policy_keys}
        if policy_updates:
            current = await mgr.get_agent(agent_id)
            policy = _agent_policy(current)
            policy.update(policy_updates)
            update_data["tool_policy_json"] = json.dumps(policy)
        agent = await mgr.update_agent(agent_id, **update_data)
        return _agent_response(agent)
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


@router.post(
    "/{agent_id}/archive",
    response_model=AgentResponse,
    responses={404: {"model": ErrorResponse}},
)
async def archive_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Hide an agent from the default list without deleting its sessions."""
    mgr = AgentManager(db)
    try:
        current = await mgr.get_agent(agent_id)
        policy = _agent_policy(current)
        policy["archived"] = True
        agent = await mgr.update_agent(agent_id, tool_policy_json=json.dumps(policy))
        return _agent_response(agent)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


def _agent_policy(agent) -> dict:
    if not agent.tool_policy_json:
        return {}
    try:
        parsed = json.loads(agent.tool_policy_json)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _agent_policy_json(**values) -> str:
    return json.dumps({k: v for k, v in values.items() if v is not None})


def _agent_response(agent) -> AgentResponse:
    policy = _agent_policy(agent)
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        runner=agent.runner,
        model=agent.model,
        system_prompt=agent.system_prompt,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        tool_policy_json=agent.tool_policy_json,
        description=str(policy.get("description") or ""),
        avatar=policy.get("avatar"),
        mcp_servers=policy.get("mcp_servers") if isinstance(policy.get("mcp_servers"), list) else [],
        tool_allow=str(policy.get("tool_allow") or ""),
        tool_deny=str(policy.get("tool_deny") or ""),
        archived=bool(policy.get("archived")),
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )
