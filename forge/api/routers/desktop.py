"""Desktop bootstrap + runners API — endpoints for desktop app startup."""

from __future__ import annotations

import shutil
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.api.deps import get_db
from forge.db.models import ProjectModel, AgentModel, SessionModel, TaskModel
from forge.db.base import async_session_factory
from forge.runtime.runners.registry import registry

router = APIRouter(tags=["desktop"])


@router.get("/api/desktop/bootstrap")
async def desktop_bootstrap(db: AsyncSession = Depends(get_db)):
    """Single endpoint to bootstrap the desktop app.

    Returns all data needed for the desktop home screen in one request:
    health, projects count, agents, running sessions/tasks, available runners.
    """
    # Count entities
    proj_count = (await db.execute(select(func.count()).select_from(ProjectModel))).scalar() or 0
    agent_count = (await db.execute(select(func.count()).select_from(AgentModel))).scalar() or 0
    running_sessions = (await db.execute(
        select(SessionModel).where(SessionModel.status == "running")
    )).scalars().all()
    running_tasks = (await db.execute(
        select(TaskModel).where(TaskModel.status == "running")
    )).scalars().all()

    # Available runners
    runners = _get_runner_status()

    # Features
    features = {
        "claude_runner": registry.get("claude") is not None,
        "openai_runner": registry.get("openai-compatible") is not None,
        "codex_runner": registry.get("codex") is not None,
        "websocket": True,
        "tasks": True,
        "schedules": True,
        "git": False,  # Git API coming in D3
    }

    return {
        "health": {"status": "ok"},
        "projects_count": proj_count,
        "agents_count": agent_count,
        "running_sessions": len(running_sessions),
        "running_tasks": len(running_tasks),
        "available_runners": [r["name"] for r in runners],
        "runners": runners,
        "features": features,
    }


@router.get("/api/runners")
async def list_runners():
    """List all registered runners with availability diagnostics."""
    return {
        "runners": _get_runner_status(),
    }


@router.get("/api/runners/diagnostics")
async def runner_diagnostics():
    """Detailed runner diagnostics including paths and versions."""
    runners = []
    for name in registry.list_names():
        runner = registry.get(name)
        info = {
            "name": name,
            "registered": runner is not None,
        }
        # Check CLI availability
        if name == "claude":
            path = shutil.which("claude")
            info["path"] = path
            info["available"] = path is not None
        elif name == "openai-compatible":
            info["available"] = True  # Always available as HTTP client
            info["path"] = None
        else:
            info["available"] = False
            info["path"] = None
        runners.append(info)
    return {"runners": runners}


def _get_runner_status() -> list[dict]:
    """Check runner availability."""
    runners = []
    for name in registry.list_names():
        available = False
        if name == "claude":
            available = shutil.which("claude") is not None
        elif name == "openai-compatible":
            available = True
        runners.append({"name": name, "available": available})
    return runners
