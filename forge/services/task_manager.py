"""Task manager service — orchestrates background shell tasks."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.errors import NotFoundError
from forge.core.events import Event
from forge.core.event_bus import event_bus
from forge.core.ids import gen_id
from forge.db.models import TaskModel
from forge.runtime.runners.shell_runner import shell_runner

logger = logging.getLogger(__name__)

VALID_TASK_STATUSES = {"pending", "running", "completed", "failed", "cancelled"}


class TaskManager:
    """Manages backend shell tasks lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_task(
        self,
        command: str,
        cwd: str,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
    ) -> TaskModel:
        """Start a background task and return immediately."""
        task = TaskModel(
            id=gen_id("task"),
            session_id=session_id,
            project_id=project_id,
            name=name or command[:100],
            command=command,
            status="running",
            started_at=_utc_iso(),
            created_at=_utc_iso(),
            updated_at=_utc_iso(),
        )
        self.db.add(task)
        await self.db.flush()

        # Event sink for task logs
        async def log_sink(event: Event):
            event.task_id = task.id
            await event_bus.publish(event)

        # Start in background
        async def _run():
            try:
                pid = await shell_runner.start(
                    task.id, command, cwd, env=env, event_sink=log_sink
                )
                task.pid = pid
                await self.db.flush()

                exit_code = await shell_runner.wait(task.id)

                task.exit_code = exit_code
                task.status = "completed" if exit_code == 0 else "failed"
                task.finished_at = _utc_iso()
                task.updated_at = _utc_iso()
                await self.db.flush()

                await event_bus.publish(Event(
                    type="task_finished",
                    task_id=task.id,
                    session_id=session_id,
                    payload={"exit_code": exit_code, "status": task.status},
                ))

            except Exception as e:
                logger.error("Task %s failed: %s", task.id, e)
                task.status = "failed"
                task.finished_at = _utc_iso()
                task.updated_at = _utc_iso()
                await self.db.flush()

        asyncio.create_task(_run())

        return task

    async def get_task(self, task_id: str) -> TaskModel:
        """Get a task by ID."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise NotFoundError("Task", task_id)
        return task

    async def list_tasks(
        self, project_id: Optional[str] = None, limit: int = 50
    ) -> Sequence[TaskModel]:
        """List tasks, optionally filtered by project."""
        from sqlalchemy import select
        q = select(TaskModel)
        if project_id:
            q = q.where(TaskModel.project_id == project_id)
        q = q.order_by(TaskModel.created_at.desc()).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def cancel_task(self, task_id: str) -> TaskModel:
        """Cancel a running task."""
        task = await self.get_task(task_id)
        if task.status == "running":
            await shell_runner.cancel(task_id)
            task.status = "cancelled"
            task.finished_at = _utc_iso()
            task.updated_at = _utc_iso()
            await self.db.flush()
        return task


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
