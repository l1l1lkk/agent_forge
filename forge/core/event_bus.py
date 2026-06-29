"""Event bus for pub/sub event distribution.

Manages subscribers that receive events for specific sessions, tasks, or global broadcasts.
Supports multiple concurrent subscribers per key (e.g., multiple WS connections).
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, AsyncIterator, Callable, Optional, Set

from forge.core.events import Event

logger = logging.getLogger(__name__)

# Callable that receives an Event
Subscriber = Callable[[Event], Any]


class EventBus:
    """In-memory event distribution hub.

    - Multiple queue subscribers per key (for WebSocket connections)
    - Callback subscribers per key (for programmatic handlers)
    - Global wildcard "*" key for catch-all listeners
    """

    def __init__(self) -> None:
        self._callbacks: dict[str, list[Subscriber]] = defaultdict(list)
        self._queues: dict[str, list[asyncio.Queue[Event]]] = defaultdict(list)
        self._sub_count: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    def add_callback(self, key: str, callback: Subscriber) -> None:
        """Register a callback subscriber that receives events synchronously."""
        self._callbacks[key].append(callback)
        self._sub_count[key] += 1

    def remove_callback(self, key: str, callback: Subscriber) -> None:
        """Remove a callback subscriber."""
        try:
            self._callbacks[key].remove(callback)
        except ValueError:
            pass
        self._sub_count[key] -= 1
        if self._sub_count[key] <= 0:
            self._sub_count.pop(key, None)

    async def subscribe(self, key: str) -> AsyncIterator[Event]:
        """Subscribe to events for a given key via async iterator.

        Args:
            key: Session ID, task ID, or "*" for all events.

        Yields:
            Events as they arrive.
        """
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._queues[key].append(queue)
            self._sub_count[key] += 1

        try:
            while True:
                event = await queue.get()
                yield event
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                try:
                    self._queues[key].remove(queue)
                except ValueError:
                    pass
                self._sub_count[key] -= 1
                if self._sub_count[key] <= 0:
                    self._sub_count.pop(key, None)

    async def publish(self, event: Event) -> None:
        """Publish an event to all matching subscribers.

        Delivery order: session_id → task_id → "*" (global).
        """
        keys_to_try: list[str] = []
        if event.session_id:
            keys_to_try.append(event.session_id)
        if event.task_id and event.task_id != event.session_id:
            keys_to_try.append(event.task_id)
        keys_to_try.append("*")

        for key in keys_to_try:
            # Callback subscribers
            for cb in list(self._callbacks.get(key, [])):
                try:
                    result = cb(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    pass

            # Queue subscribers
            for q in list(self._queues.get(key, [])):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop oldest event to make room
                    try:
                        q.get_nowait()
                        q.put_nowait(event)
                    except Exception:
                        pass

    async def unsubscribe_all(self, key: str) -> None:
        """Remove all subscribers for a key."""
        self._callbacks.pop(key, None)
        for q in self._queues.pop(key, []):
            # Cancel any waiting consumers
            pass
        self._sub_count.pop(key, None)

    def subscriber_count(self, key: Optional[str] = None) -> int:
        """Return the number of subscribers for a key, or total if key is None."""
        if key:
            return self._sub_count.get(key, 0)
        return sum(self._sub_count.values())


# Global event bus instance
event_bus = EventBus()
