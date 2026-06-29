"""Tests for the EventBus pub/sub system."""

from __future__ import annotations

import asyncio

import pytest

from forge.core.event_bus import EventBus
from forge.core.events import Event


@pytest.mark.asyncio
class TestEventBus:
    """Tests for the EventBus."""

    async def test_publish_to_queue_subscriber(self):
        bus = EventBus()
        received: list[Event] = []

        async def collector():
            async for event in bus.subscribe("ses_test"):
                received.append(event)
                if len(received) >= 1:
                    break

        # Start subscriber in background
        task = asyncio.create_task(collector())

        # Give subscriber time to set up
        await asyncio.sleep(0.01)

        # Publish
        event = Event(type="test_event", session_id="ses_test", seq=1, payload={"msg": "hello"})
        await bus.publish(event)

        # Wait for collection
        await asyncio.wait_for(task, timeout=1.0)

        assert len(received) == 1
        assert received[0].type == "test_event"
        assert received[0].session_id == "ses_test"

    async def test_publish_to_callback_subscriber(self):
        bus = EventBus()
        received: list[Event] = []

        def callback(event: Event):
            received.append(event)

        # Register callback
        bus.add_callback("ses_test", callback=callback)

        event = Event(type="test_event", session_id="ses_test", seq=1, payload={})
        await bus.publish(event)

        assert len(received) == 1

    async def test_multiple_subscribers_same_key(self):
        bus = EventBus()
        r1: list[Event] = []
        r2: list[Event] = []

        async def sub1():
            async for e in bus.subscribe("ses_test"):
                r1.append(e)
                if len(r1) >= 1:
                    break

        async def sub2():
            async for e in bus.subscribe("ses_test"):
                r2.append(e)
                if len(r2) >= 1:
                    break

        t1 = asyncio.create_task(sub1())
        t2 = asyncio.create_task(sub2())
        await asyncio.sleep(0.01)

        event = Event(type="test", session_id="ses_test", seq=1, payload={})
        await bus.publish(event)

        await asyncio.wait_for(t1, timeout=1.0)
        await asyncio.wait_for(t2, timeout=1.0)

        assert len(r1) == 1
        assert len(r2) == 1

    async def test_global_wildcard_subscriber(self):
        bus = EventBus()
        received: list[Event] = []

        async def collector():
            async for event in bus.subscribe("*"):
                received.append(event)
                if len(received) >= 1:
                    break

        task = asyncio.create_task(collector())
        await asyncio.sleep(0.01)

        event = Event(type="test", session_id="ses_other", seq=1, payload={})
        await bus.publish(event)

        await asyncio.wait_for(task, timeout=1.0)
        assert len(received) == 1

    async def test_subscriber_count(self):
        bus = EventBus()

        async def sub():
            async for _ in bus.subscribe("ses_count"):
                break

        task = asyncio.create_task(sub())
        await asyncio.sleep(0.01)

        assert bus.subscriber_count("ses_count") == 1

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # After cleanup
        await asyncio.sleep(0.01)
        assert bus.subscriber_count("ses_count") == 0
