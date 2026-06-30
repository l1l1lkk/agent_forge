"""Session management service.

Orchestrates session and message lifecycle — the core of forge-agent.
Now includes runner integration to execute AI turns.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from forge.core.errors import NotFoundError, ConflictError
from forge.core.event_bus import event_bus
from forge.core.events import Event
from forge.core.ids import gen_id
from forge.db.models import SessionModel, MessageModel, EventModel
from forge.db.repositories.session_repo import SessionRepo
from forge.db.repositories.message_repo import MessageRepo
from forge.db.repositories.event_repo import EventRepo
from forge.runtime.runners.base import BaseRunner, RunnerResult
from forge.runtime.runners.registry import registry
from forge.services.agent_manager import AgentManager
from forge.services.project_manager import ProjectManager

logger = logging.getLogger(__name__)

# Valid session states
VALID_STATUSES: set[str] = {
    "idle", "running", "waiting_approval", "interrupted", "error", "archived",
}

# Valid message roles
VALID_ROLES: set[str] = {"user", "assistant", "system", "tool", "tool_call", "tool_result", "thinking"}


class SessionManager:
    """Manages session and message lifecycle, including AI turn execution."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = SessionRepo(db)
        self.message_repo = MessageRepo(db)
        self.event_repo = EventRepo(db)

    # ── Session CRUD ────────────────────────────────────────────

    async def create_session(
        self,
        project_identifier: str,
        agent_identifier: str,
        title: Optional[str] = None,
        cwd: Optional[str] = None,
    ) -> SessionModel:
        """Create a new session."""
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
        """Get a session with its messages loaded."""
        session = await self.session_repo.get_by_id(session_id, load_relations=True)
        if session is None:
            raise NotFoundError("Session", session_id)
        return session

    async def update_status(self, session_id: str, status: str) -> SessionModel:
        """Update a session's status."""
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {status!r}. Must be one of {VALID_STATUSES}"
            )
        session = await self.session_repo.get_by_id(session_id, load_relations=False)
        if session is None:
            raise NotFoundError("Session", session_id)
        session.status = status
        session.updated_at = _utc_iso()
        return await self.session_repo.update(session)

    async def rename_session(self, session_id: str, title: str) -> SessionModel:
        """Rename a session."""
        session = await self.get_session(session_id)
        return await self.session_repo.update(session, title=title)

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages/events."""
        session = await self.get_session(session_id)
        await self.session_repo.delete(session)

    # ── Messages ─────────────────────────────────────────────────

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> MessageModel:
        """Add a message to a session."""
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role!r}. Must be one of {VALID_ROLES}")

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

    async def get_messages(self, session_id: str) -> Sequence[MessageModel]:
        """Get all messages for a session, ordered by sequence."""
        items, _ = await self.message_repo.list_by_session(session_id)
        return items

    # ── Turn Execution ───────────────────────────────────────────

    async def run_turn(
        self,
        session_id: str,
        user_prompt: str,
    ) -> RunnerResult:
        """Execute one AI turn for a session.

        1. Validate session state (must be idle)
        2. Add user message to DB
        3. Set status to "running"
        4. Get runner and execute
        5. Save events and assistant response to DB
        6. Return to "idle" or "error"

        Args:
            session_id: Session ID.
            user_prompt: The user's input.

        Returns:
            RunnerResult with success/failure and collected messages.

        Raises:
            NotFoundError: If session/project/agent not found.
            ConflictError: If session is already running.
        """
        # Load session with relations
        session = await self.session_repo.get_by_id(session_id, load_relations=True)
        if session is None:
            raise NotFoundError("Session", session_id)

        if session.status == "running":
            raise ConflictError(f"Session {session_id} is already running")

        # Load project and agent
        project_mgr = ProjectManager(self.db)
        agent_mgr = AgentManager(self.db)
        project = await project_mgr.get_project(session.project_id)
        agent = await agent_mgr.get_agent(session.agent_id)

        # Get the runner
        runner = registry.get(agent.runner)
        if runner is None:
            runner = registry.get("claude")  # fallback
        if runner is None:
            raise RuntimeError(f"No runner available for: {agent.runner}")

        # Add user message to DB
        user_msg = await self.add_message(session_id, "user", user_prompt)

        # Set status to running
        await self.update_status(session_id, "running")

        # Build history (exclude the just-added user message — runner gets raw history)
        history_items, _ = await self.message_repo.list_by_session(session_id)
        # Remove the last message (just added user message) from history
        # since we pass it separately as prompt
        history = [m for m in history_items if m.id != user_msg.id]

        # Event sink: persist events to DB, save tool events as messages, broadcast
        async def event_sink(event: Event):
            import json as _json
            # Persist to events table
            try:
                db_event = EventModel(
                    id=event.id, session_id=event.session_id, task_id=event.task_id,
                    type=event.type, seq=event.seq,
                    payload_json=event.payload if isinstance(event.payload, str) else _json.dumps(event.payload),
                    created_at=event.created_at.isoformat(),
                )
                await self.event_repo.create(db_event)
            except Exception as e:
                logger.warning("Failed to persist event: %s", e)

            # Also save tool events as messages so they survive session switches
            if event.type == "tool_call_started":
                try:
                    cmd = ""
                    inp = event.payload.get("input", {})
                    if isinstance(inp, dict):
                        cmd = inp.get("command", inp.get("url", str(inp)[:200]))
                    await self.add_message(session_id, "tool_call", _json.dumps({
                        "tool": event.payload.get("tool", ""), "command": cmd,
                        "id": event.payload.get("id", ""),
                    }))
                except Exception as e2:
                    logger.warning("Failed to save tool_call message: %s", e2)
            elif event.type == "tool_result":
                try:
                    content = str(event.payload.get("content", ""))[:2000]
                    await self.add_message(session_id, "tool_result", _json.dumps({
                        "tool_use_id": event.payload.get("tool_use_id", ""),
                        "content": content, "is_error": event.payload.get("is_error", False),
                    }))
                except Exception as e2:
                    logger.warning("Failed to save tool_result message: %s", e2)

            # Broadcast to subscribers
            try:
                await event_bus.publish(event)
            except Exception as e:
                logger.warning("Failed to broadcast event: %s", e)

        # Execute the turn
        try:
            result = await runner.run_turn(
                session=session,
                agent=agent,
                project=project,
                prompt=user_prompt,
                history=history,
                event_sink=event_sink,
            )

            # Save messages from result
            for msg_data in result.messages:
                role = msg_data.get("role", "assistant")
                content = msg_data.get("content", "")
                if not content.strip():
                    continue
                # Skip raw JSON payload dumps (only for assistant role)
                if role == "assistant" and content.startswith("{") and ("content_blocks" in content):
                    continue
                try:
                    await self.add_message(session_id, role, content)
                except Exception as e:
                    logger.warning("Failed to save message: %s", e)

            # Update session status
            if result.success:
                await self.update_status(session_id, "idle")
            else:
                await self.update_status(session_id, "error")

            return result

        except Exception as e:
            logger.exception("Turn execution failed: %s", e)
            await self.update_status(session_id, "error")
            return RunnerResult(success=False, error=str(e))

    async def interrupt_session(self, session_id: str) -> None:
        """Interrupt a running session's turn.

        Args:
            session_id: Session ID.
        """
        session = await self.session_repo.get_by_id(session_id, load_relations=True)
        if session is None:
            raise NotFoundError("Session", session_id)

        if session.status != "running":
            return  # Nothing to interrupt

        runner = registry.get(session.runner)
        if runner:
            await runner.interrupt(session_id)

        await self.update_status(session_id, "interrupted")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
