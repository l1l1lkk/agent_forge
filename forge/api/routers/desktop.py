"""Desktop bootstrap + runners API — endpoints for desktop app startup."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from forge.api.deps import get_db
from forge.db.models import ProjectModel, AgentModel, SessionModel, TaskModel
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
        "git": True,
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


@router.get("/api/desktop/git-status")
async def desktop_git_status(
    path: Optional[str] = Query(None, description="Project root path; defaults to CWD"),
    db: AsyncSession = Depends(get_db),
):
    """Read-only Git workspace status for the Desktop workspace view.

    Returns current branch, dirty files count, recent commits (last 5),
    and project path. No commit/push operations.
    """
    working_dir = Path(path).resolve() if path else Path.cwd()

    # Walk up to find the git repo root
    repo_root = working_dir
    while repo_root != repo_root.parent:
        if (repo_root / ".git").exists():
            break
        repo_root = repo_root.parent

    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return {
            "in_repo": False,
            "path": str(working_dir),
            "branch": None,
            "dirty_count": 0,
            "dirty_files": [],
            "recent_commits": [],
            "error": "Not a git repository (or no .git found)",
        }

    async def _run_git(*args: str) -> tuple[int, str, str]:
        """Run a git command and return (exit_code, stdout, stderr)."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=str(repo_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return (
                proc.returncode or 0,
                stdout.decode("utf-8", errors="replace").rstrip(),
                stderr.decode("utf-8", errors="replace").rstrip(),
            )
        except FileNotFoundError:
            return (-1, "", "git not found on PATH")
        except Exception as e:
            return (-1, "", str(e))

    # Current branch
    rc, branch, _ = await _run_git("rev-parse", "--abbrev-ref", "HEAD")
    if rc != 0:
        branch = "HEAD"

    # Dirty files (porcelain status)
    rc, porcelain, _ = await _run_git("status", "--porcelain")
    dirty_files: list[str] = []
    if rc == 0 and porcelain:
        dirty_files = [line[3:] for line in porcelain.split("\n") if len(line) >= 3]
    dirty_count = len(dirty_files)

    # Recent commits (last 5)
    rc, log_out, _ = await _run_git(
        "log", "--oneline", "-5", "--format=%h %s (%ar)",
    )
    recent_commits: list[dict] = []
    if rc == 0 and log_out:
        for line in log_out.split("\n"):
            recent_commits.append({"raw": line})

    # Open project path from DB if available
    project_path = str(working_dir)
    try:
        result = await db.execute(
            select(ProjectModel).where(
                ProjectModel.root_path == str(repo_root)
            )
        )
        proj = result.scalar_one_or_none()
        if proj:
            project_path = proj.root_path
    except Exception:
        pass

    return {
        "in_repo": True,
        "path": project_path,
        "repo_root": str(repo_root),
        "branch": branch,
        "dirty_count": dirty_count,
        "dirty_files": dirty_files,
        "recent_commits": recent_commits,
    }


@router.get("/api/desktop/git-diff", response_class=PlainTextResponse)
async def desktop_git_diff(
    path: str = Query(..., description="Project root path"),
    file: str = Query(..., description="Repo-relative file path"),
):
    """Return unified diff for a single file in the working tree.

    Read-only.  ``path`` is the repo root; ``file`` must be repo-relative.
    Path traversal, absolute paths outside the repo, and nonexistent files
    are rejected.
    """
    working_dir = Path(path).resolve()

    # Walk up to find the git repo root
    repo_root = working_dir
    while repo_root != repo_root.parent:
        if (repo_root / ".git").exists():
            break
        repo_root = repo_root.parent

    if not (repo_root / ".git").exists():
        raise HTTPException(status_code=400, detail="Not a git repository")

    # Resolve and validate the file path
    file_path = Path(file)
    if file_path.is_absolute():
        raise HTTPException(status_code=400, detail="File path must be repo-relative")
    resolved = (repo_root / file_path).resolve()

    # Reject paths outside the repo (catches ../ traversal as well)
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="File is outside the repository")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found in the repository")

    # Compute repo-relative path for the git command
    rel_path = str(resolved.relative_to(repo_root))
    # Normalise to forward slashes for cross-platform git usage
    rel_path = rel_path.replace("\\", "/")

    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "diff", "--", rel_path,
            cwd=str(repo_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _stderr = await proc.communicate()
        return stdout.decode("utf-8", errors="replace")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="git not found on PATH")


@router.get("/api/desktop/diagnostics")
async def desktop_diagnostics(db: AsyncSession = Depends(get_db)):
    """Enhanced diagnostics for the desktop diagnostics panel.

    Returns daemon health, runner diagnostics, DB stats, and active sessions.
    """
    # DB stats
    proj_count = (await db.execute(select(func.count()).select_from(ProjectModel))).scalar() or 0
    agent_count = (await db.execute(select(func.count()).select_from(AgentModel))).scalar() or 0
    running_sessions = (await db.execute(
        select(SessionModel).where(SessionModel.status == "running")
    )).scalars().all()
    running_tasks = (await db.execute(
        select(TaskModel).where(TaskModel.status == "running")
    )).scalars().all()

    # Runner diagnostics
    runners = []
    for name in registry.list_names():
        info = {"name": name, "registered": True}
        if name == "claude":
            path = shutil.which("claude")
            info["path"] = path
            info["available"] = path is not None
        elif name == "openai-compatible":
            info["available"] = True
            info["path"] = None
        else:
            info["available"] = False
            info["path"] = None
        runners.append(info)

    # Running session details
    running_session_list = []
    for s in running_sessions:
        running_session_list.append({
            "id": s.id,
            "title": s.title,
            "agent_id": s.agent_id,
            "runner": s.runner,
            "created_at": s.created_at.isoformat() if s.created_at else "",
        })

    # Running task details
    running_task_list = []
    for t in running_tasks:
        running_task_list.append({
            "id": t.id,
            "name": t.name,
            "session_id": getattr(t, "session_id", None),
            "created_at": t.created_at.isoformat() if t.created_at else "",
        })

    return {
        "health": {"status": "ok", "version": "0.0.15rc1"},
        "db": {
            "projects": proj_count,
            "agents": agent_count,
            "running_sessions": len(running_sessions),
            "running_tasks": len(running_tasks),
        },
        "runners": runners,
        "running_sessions": running_session_list,
        "running_tasks": running_task_list,
        "features": {
            "claude_runner": registry.get("claude") is not None,
            "openai_runner": registry.get("openai-compatible") is not None,
            "codex_runner": registry.get("codex") is not None,
            "websocket": True,
            "tasks": True,
            "schedules": True,
            "git": True,
        },
    }


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
