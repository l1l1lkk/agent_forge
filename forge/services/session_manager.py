"""Session management service.

Orchestrates session and message lifecycle — the core of forge-agent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.errors import NotFoundError, ConflictError
from forge.core.ids import gen_id
from forge.db.models import SessionModel, MessageModel
from forge.db.repositories.session_repo import SessionRepo
from forge.db.repositories.message_repo import MessageRepo
from forge.services.agent_manager import AgentManager
from forge.services.project_manager import ProjectManager


# Valid session states
VALID_STATUSES: set[str] = {
    "idle", "running", "waiting_approval", "interrupted", "error", "archived",
}

# Valid message roles
VALID_ROLES: set[str] = {"user", "assistant", "system", "tool"}


class SessionManager:
    """Manages session and message lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepo(db)
        self.message_repo = MessageRepo(db)

    async def create_session(
        self,
        project_identifier: str,
        agent_identifier: str,
        title: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> SessionModel:
        """Create a new session.

        Args:
            project_identifier: Project ID or name.
            agent_identifier: Agent ID or name.
            title: Optional session title.
            cwd: Optional working directory override.

        Returns:
            The created SessionModel.

        Raises:
            NotFoundError: If the project or agent doesn't exist.
        """
        project_mgr = ProjectManager(self.db)
        agent_mgr = AgentManager(self.db)

        project = await project_mgr.get_project(project_identifier)
        agent = await agent_mgr.get_agent(agent_identifier)

        session = SessionModel(
            id=gen_id("session"),
            project_id=project.id,
            agent_id=agent.id,
            title=title,
            status="idle",
            runner=agent.runner,
            cwd=cwd or project.root_path,
            created_at=_utc_iso(),
            updated_at=_utc_iso(),
        )
        return await self.session_repo.create(session)

    async def list_sessions(
        self, project_id: Optional[str] = None
    ) -> Sequence[SessionModel]:
        """List all sessions, optionally filtered by project."""
        items, _ = await self.session_repo.list(project_id=project_id)
        return items

    async def get_session(self, session_id: str) -> SessionModel:
        """Get a session with its messages loaded.

        Args:
            session_id: Session ID (ses_xxx).

        Returns:
            The SessionModel with messages eager-loaded.

        Raises:
            NotFoundError: If the session doesn't exist.
        """
        session = await self.session_repo.get_by_id(session_id, load_relations=True)
        if session is None:
            raise NotFoundError("Session", session_id)
        return session

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> MessageModel:
        """Add a message to a session.

        Args:
            session_id: Session ID.
            role: Message role (user, assistant, system, tool).
            content: Message content.

        Returns:
            The created MessageModel.

        Raises:
            NotFoundError: If the session doesn't exist.
            ValidationError: If the role is invalid.
        """
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role!r}. Must be one of {VALID_ROLES}")

        # Verify session exists
        session = await self.session_repo.get_by_id(
            session_id, load_relations=False
        )
        if session is None:
            raise NotFoundError("Session", session_id)

        seq = await self.message_repo.get_next_seq(session_id)
        message = MessageModel(
            id=gen_id("message"),
            session_id=session_id,
            role=role,
            content=content,
            seq=seq,
            created_at=_utc_iso(),
        )
        return await self.message_repo.create(message)

    async def get_messages(
        self, session_id: str
    ) -> Sequence[MessageModel]:
        """Get all messages for a session, ordered by sequence.

        Args:
            session_id: Session ID.

        Returns:
            List of MessageModel ordered by seq.
        """
        items, _ = await self.message_repo.list_by_session(session_id)
        return items

    async def update_status(self, session_id: str, status: str) -> SessionModel:
        """Update a session's status.

        Args:
            session_id: Session ID.
            status: New status (must be one of VALID_STATUSES).

        Returns:
            The updated SessionModel.

        Raises:
            NotFoundError: If the session doesn't exist.
            ValueError: If the status is invalid.
        """
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {status!r}. Must be one of {VALID_STATUSES}"
            )

        session = await self.get_session(session_id)
        session.status = status
        session.updated_at = _utc_iso()
        return await self.session_repo.update(session)

    async def rename_session(self, session_id: str, title: str) -> SessionModel:
        """Rename a session.

        Args:
            session_id: Session ID.
            title: New title.

        Returns:
            The updated SessionModel.
        """
        session = await self.get_session(session_id)
        return await self.session_repo.update(session, title=title)

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages/events.

        Args:
            session_id: Session ID.
        """
        session = await self.get_session(session_id)
        await self.session_repo.delete(session)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
