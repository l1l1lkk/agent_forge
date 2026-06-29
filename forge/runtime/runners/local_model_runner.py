"""LocalModelRunner — OpenAI-compatible API runner.

Supports local vLLM, MindIE, Ollama, or any OpenAI-compatible endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from forge.core.events import Event
from forge.db.models import AgentModel, MessageModel, ProjectModel, SessionModel
from forge.runtime.runners.base import BaseRunner, EventSink, RunnerResult

logger = logging.getLogger(__name__)


class LocalModelRunner(BaseRunner):
    """Runner for OpenAI-compatible local/remote model APIs.

    Connects to any OpenAI-compatible endpoint (vLLM, Ollama, MindIE, etc.)
    and translates responses into unified forge Events.
    """

    name = "openai-compatible"

    def __init__(self, base_url: str = "http://localhost:8000/v1", api_key: str = "not-needed"):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

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
        messages = [{"role": "system", "content": agent.system_prompt or "You are a helpful AI assistant."}]
        for m in history:
            messages.append({"role": m.role, "content": m.content or ""})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                    json={
                        "model": agent.model or "default",
                        "messages": messages,
                        "temperature": agent.temperature or 0.7,
                        "max_tokens": agent.max_tokens or 4096,
                        "stream": True,
                    },
                )
                response.raise_for_status()

                full_text = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                full_text += text
                                await event_sink(Event(
                                    type="assistant_text_delta",
                                    session_id=session.id,
                                    seq=0,
                                    payload={"text": text},
                                ))
                        except json.JSONDecodeError:
                            pass

                await event_sink(Event(
                    type="assistant_message",
                    session_id=session.id,
                    seq=0,
                    payload={"text": full_text},
                ))

                return RunnerResult(success=True, messages=[{"role": "assistant", "content": full_text}])

        except Exception as e:
            logger.error("LocalModelRunner error: %s", e)
            return RunnerResult(success=False, error=str(e))

    async def interrupt(self, session_id: str) -> None:
        pass  # HTTP requests can't be easily interrupted at protocol level
