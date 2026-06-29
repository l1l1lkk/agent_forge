"""Event bus for pub/sub event distribution.

Manages subscribers that receive events for specific sessions, tasks, or global broadcasts.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator, Callable, Optional

from forge.core.events import Event

# Callable that receives an Event
Subscriber = Callable[[Event], Any]  # sync or async


class EventBus:
    """In-memory event distribution hub.

    Subscribers register with a key (session_id, task_id, or "*" for global).
    Events are delivered to all matching subscribers.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._queues: dict[str, asyncio.Queue[Event]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(
        self, key: str, callback: Optional[Subscriber] = None
    ) -> AsyncIterator[Event]:
        """Subscribe to events for a given key.

        Args:
            key: Session ID, task ID, or "*" for all events.
            callback: Optional sync callback. If omitted, returns an async iterator.

        Yields:
            Events as they arrive (if no callback is provided).
        """
        if callback is not None:
            self._subscribers[key].append(callback)
            return

        queue: asyncio.Queue[Event] = asyncio.Queue()
        async with self._lock:
            self._queues[key] = queue

        try:
            while True:
                event = await queue.get()
                yield event
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                self._queues.pop(key, None)

    async def publish(self, event: Event) -> None:
        """Publish an event to all matching subscribers.

        Delivery order: session_id → task_id → "*" (global).
        """
        keys_to_try = []
        if event.session_id:
            keys_to_try.append(event.session_id)
        if event.task_id:
            keys_to_try.append(event.task_id)
        keys_to_try.append("*")

        for key in keys_to_try:
            # Deliver to callback subscribers
            for cb in self._subscribers.get(key, []):
                try:
                    result = cb(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    pass  # Don't let one subscriber break others

            # Deliver to queue subscribers
            queue = self._queues.get(key)
            if queue is not None:
                await queue.put(event)

    async def unsubscribe_all(self, key: str) -> None:
        """Remove all subscribers for a key."""
        self._subscribers.pop(key, None)
        self._queues.pop(key, None)


# Global event bus instance
event_bus = EventBus()
