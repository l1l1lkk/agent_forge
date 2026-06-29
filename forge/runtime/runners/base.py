"""Base runner abstraction for forge-agent.

All AI backends (Claude, Codex, local models, etc.) implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional

from forge.core.events import Event
from forge.db.models import AgentModel, ProjectModel, SessionModel, MessageModel


@dataclass
class RunnerResult:
    """Result of a runner turn."""
    success: bool
    messages: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class BaseRunner(ABC):
    """Abstract base for all AI backend runners.

    Each runner implementation handles:
    - Building the CLI command / API request
    - Spawning the subprocess / streaming the response
    - Parsing backend-specific output into unified Events
    - Supporting interrupt (kill/cancel)
    """

    name: str = "base"

    @abstractmethod
    async def run_turn(
        self,
        *,
        session: SessionModel,
        agent: AgentModel,
        project: ProjectModel,
        prompt: str,
        history: list[MessageModel],
        event_sink: EventSink,
    ) -> RunnerResult:
        """Execute one turn of the agent.

        Args:
            session: Current session model.
            agent: Agent configuration.
            project: Project workspace.
            prompt: The user's input prompt.
            history: Previous messages in this session.
            event_sink: Callback to emit events during the turn.

        Returns:
            RunnerResult with success/failure and any collected messages.
        """
        ...

    @abstractmethod
    async def interrupt(self, session_id: str) -> None:
        """Interrupt a running turn for the given session."""
        ...


# EventSink: async callable that receives Event objects
EventSink = Any  # Callable[[Event], Awaitable[None]]
