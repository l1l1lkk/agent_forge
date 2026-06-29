"""Schedule manager — cron-based automated agent tasks.

Uses APScheduler to run agent prompts on a schedule.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Sequence

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.errors import NotFoundError, ConflictError
from forge.core.ids import gen_id
from forge.db.models import ScheduleModel
from forge.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

# Global scheduler
scheduler = AsyncIOScheduler()


class ScheduleManager:
    """Manages scheduled AI agent tasks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        name: str,
        project_id: str,
        agent_id: str,
        cron: str,
        prompt: str,
        enabled: bool = True,
    ) -> ScheduleModel:
        existing = await self.db.execute(
            select(ScheduleModel).where(ScheduleModel.name == name)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Schedule already exists: {name}")

        sched = ScheduleModel(
            id=gen_id("schedule"),
            name=name,
            project_id=project_id,
            agent_id=agent_id,
            cron=cron,
            prompt=prompt,
            enabled=enabled,
            created_at=_utc_iso(),
            updated_at=_utc_iso(),
        )
        self.db.add(sched)
        await self.db.flush()

        if enabled:
            self._add_job(sched)

        return sched

    def _add_job(self, sched: ScheduleModel):
        async def job():
            logger.info("Running scheduled task: %s", sched.name)
            async with self.db.bind.connect() as conn:
                from sqlalchemy.ext.asyncio import AsyncSession as AS
                from forge.services.agent_manager import AgentManager
                from forge.services.project_manager import ProjectManager

                async with AS(conn) as session:
                    mgr = SessionManager(session)
                    try:
                        await mgr.create_session(
                            project_identifier=sched.project_id,
                            agent_identifier=sched.agent_id,
                            title=f"Scheduled: {sched.name}",
                        )
                    except Exception as e:
                        logger.error("Scheduled task %s failed: %s", sched.name, e)

        try:
            trigger = CronTrigger.from_crontab(sched.cron)
            scheduler.add_job(job, trigger, id=sched.id, name=sched.name)
        except Exception as e:
            logger.error("Invalid cron expression: %s", e)

    async def list(self) -> Sequence[ScheduleModel]:
        result = await self.db.execute(select(ScheduleModel).order_by(ScheduleModel.created_at.desc()))
        return result.scalars().all()

    async def get(self, name: str) -> ScheduleModel:
        result = await self.db.execute(
            select(ScheduleModel).where(ScheduleModel.name == name)
        )
        sched = result.scalar_one_or_none()
        if sched is None:
            raise NotFoundError("Schedule", name)
        return sched

    async def pause(self, name: str) -> ScheduleModel:
        sched = await self.get(name)
        sched.enabled = False
        sched.updated_at = _utc_iso()
        scheduler.pause_job(sched.id)
        await self.db.flush()
        return sched

    async def resume(self, name: str) -> ScheduleModel:
        sched = await self.get(name)
        sched.enabled = True
        sched.updated_at = _utc_iso()
        scheduler.resume_job(sched.id)
        await self.db.flush()
        return sched

    async def delete(self, name: str) -> None:
        sched = await self.get(name)
        try:
            scheduler.remove_job(sched.id)
        except Exception:
            pass
        await self.db.delete(sched)
        await self.db.flush()

    @staticmethod
    def start_scheduler():
        if not scheduler.running:
            scheduler.start()
            logger.info("APScheduler started")

    @staticmethod
    def shutdown_scheduler():
        if scheduler.running:
            scheduler.shutdown(wait=False)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
