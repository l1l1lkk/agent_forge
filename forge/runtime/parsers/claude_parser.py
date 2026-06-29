"""Parser for Claude Code CLI stream-json output.

Converts Claude's stream-json events into forge-agent's unified Event format.

Claude stream-json event types:
  - {"type":"system","subtype":"init",...}
  - {"type":"assistant","message":{...}}
  - {"type":"user","message":{"role":"user","content":[...]}}
  - {"type":"result","subtype":"success",...}

Each line is a complete JSON object (JSONL format).
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

from forge.core.events import Event


class ClaudeParser:
    """Parses Claude CLI stream-json output into forge Events."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._seq = 0

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def parse_line(self, line: str) -> Optional[Event]:
        """Parse one JSON line from Claude's stream-json output.

        Args:
            line: A single line of JSON from claude stdout.

        Returns:
            An Event object, or None if the line should be skipped.
        """
        line = line.strip()
        if not line:
            return None

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return None

        event_type = data.get("type", "")
        return self._dispatch(event_type, data)

    def _dispatch(self, event_type: str, data: dict[str, Any]) -> Optional[Event]:
        """Dispatch to the appropriate handler based on Claude event type."""
        if event_type == "system":
            return self._handle_system(data)
        elif event_type == "assistant":
            return self._handle_assistant(data)
        elif event_type == "user":
            return self._handle_user(data)
        elif event_type == "result":
            return self._handle_result(data)
        else:
            # Unknown event type — still emit as generic event
            return Event(
                type=event_type,
                seq=self._next_seq(),
                session_id=self.session_id,
                payload={"raw": data},
            )

    def _handle_system(self, data: dict[str, Any]) -> Optional[Event]:
        """Handle system events (init, etc.)."""
        subtype = data.get("subtype", "")
        if subtype == "init":
            return Event(
                type="session_started",
                seq=self._next_seq(),
                session_id=self.session_id,
                payload={
                    "session_id": data.get("session_id", ""),
                    "model": data.get("model", ""),
                    "cwd": data.get("cwd", ""),
                },
            )
        return Event(
            type="session_status",
            seq=self._next_seq(),
            session_id=self.session_id,
            payload={"subtype": subtype, "data": data},
        )

    def _handle_assistant(self, data: dict[str, Any]) -> Optional[Event]:
        """Handle assistant message events.

        An assistant message may contain:
        - Text content blocks
        - Tool use blocks
        - Thinking blocks
        """
        message = data.get("message", {})
        content = message.get("content", [])

        events = []
        for block in content:
            block_type = block.get("type", "")

            if block_type == "text":
                text = block.get("text", "")
                # Emit as text delta + a full assistant_message event
                events.append(Event(
                    type="assistant_text_delta",
                    seq=self._next_seq(),
                    session_id=self.session_id,
                    payload={"text": text},
                ))

            elif block_type == "tool_use":
                events.append(Event(
                    type="tool_call_started",
                    seq=self._next_seq(),
                    session_id=self.session_id,
                    payload={
                        "tool": block.get("name", "unknown"),
                        "id": block.get("id", ""),
                        "input": block.get("input", {}),
                    },
                ))

            elif block_type == "tool_result":
                events.append(Event(
                    type="tool_result",
                    seq=self._next_seq(),
                    session_id=self.session_id,
                    payload={
                        "tool_use_id": block.get("tool_use_id", ""),
                        "content": block.get("content", ""),
                        "is_error": block.get("is_error", False),
                    },
                ))

            else:
                # Thinking, etc.
                events.append(Event(
                    type="assistant_text_delta",
                    seq=self._next_seq(),
                    session_id=self.session_id,
                    payload={"text": json.dumps(block) if block else "", "block_type": block_type},
                ))

        # Also emit a summary assistant_message event
        events.append(Event(
            type="assistant_message",
            seq=self._next_seq(),
            session_id=self.session_id,
            payload={
                "content_blocks": [
                    {"type": b.get("type"), **(b if b.get("type") == "text" else {"name": b.get("name")})}
                    for b in content
                ],
            },
        ))

        # Return the first event if only one, otherwise the last (primary)
        # Actually, we should emit ALL events. The caller should iterate.
        # For now, we return the primary event. Multi-event handling is for Step 2.
        return events[-1] if events else None

    def _handle_user(self, data: dict[str, Any]) -> Optional[Event]:
        """Handle user message events (e.g., tool results sent back to Claude)."""
        message = data.get("message", {})
        content = message.get("content", [])

        for block in content:
            if block.get("type") == "tool_result":
                return Event(
                    type="tool_result",
                    seq=self._next_seq(),
                    session_id=self.session_id,
                    payload={
                        "tool_use_id": block.get("tool_use_id", ""),
                        "content": str(block.get("content", ""))[:500],
                        "is_error": block.get("is_error", False),
                    },
                )

        return Event(
            type="user_message",
            seq=self._next_seq(),
            session_id=self.session_id,
            payload={"raw": data},
        )

    def _handle_result(self, data: dict[str, Any]) -> Optional[Event]:
        """Handle final result events."""
        subtype = data.get("subtype", "")
        if subtype == "success":
            return Event(
                type="session_status",
                seq=self._next_seq(),
                session_id=self.session_id,
                payload={
                    "status": "completed",
                    "result": data.get("result", ""),
                    "usage": data.get("usage", {}),
                },
            )
        elif subtype == "error":
            return Event(
                type="error",
                seq=self._next_seq(),
                session_id=self.session_id,
                payload={
                    "error": data.get("errors", str(data)),
                },
            )
        return Event(
            type="session_status",
            seq=self._next_seq(),
            session_id=self.session_id,
            payload={"subtype": subtype},
        )

    def parse_lines(self, lines: list[str]) -> list[Event]:
        """Parse multiple lines of JSONL output.

        Returns all non-None events.
        """
        events = []
        for line in lines:
            event = self.parse_line(line)
            if event is not None:
                events.append(event)
        return events
