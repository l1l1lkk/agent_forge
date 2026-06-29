"""Audit logging service for security event tracking."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.ids import gen_id
from forge.db.models import AuditLogModel

logger = logging.getLogger(__name__)


class AuditService:
    """Records security-relevant actions for compliance and debugging."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        payload: dict | None = None,
    ) -> AuditLogModel:
        import json
        entry = AuditLogModel(
            id=gen_id("audit"),
            actor=actor or "system",
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload_json=json.dumps(payload) if payload else None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(entry)
        await self.db.flush()
        return entry
