"""Core event types and event bus for forge-agent.

All runner output is unified into Event objects that can be:
- Streamed via WebSocket
- Persisted to SQLite
- Broadcast to subscribers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from forge.core.ids import gen_id


# ── Event Types ──────────────────────────────────────────────────

EVENT_TYPES: set[str] = {
    "session_started",
    "session_status",
    "user_message",
    "assistant_text_delta",
    "assistant_message",
    "tool_call_started",
    "tool_call_delta",
    "tool_call_finished",
    "tool_result",
    "task_started",
    "task_log",
    "task_finished",
    "error",
    "interrupt",
}


@dataclass
class Event:
    """A unified event emitted by runners and tasks."""

    type: str
    seq: int = 0
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: gen_id("event"))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "id": self.id,
            "type": self.type,
            "seq": self.seq,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }
