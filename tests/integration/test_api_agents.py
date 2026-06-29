"""Integration tests for the Agent API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAgentAPI:
    """Integration tests for agent CRUD endpoints."""

    async def test_list_agents_empty(self, client: AsyncClient):
        r = await client.get("/api/agents")
        assert r.status_code == 200
        data = r.json()
        assert data["agents"] == []

    async def test_create_agent(self, client: AsyncClient):
        r = await client.post(
            "/api/agents",
            json={
                "name": "coding-agent",
                "runner": "codex",
                "model": "gpt-5.5",
                "system_prompt": "You are a Python expert.",
                "temperature": 0.5,
                "max_tokens": 4096,
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "coding-agent"
        assert data["runner"] == "codex"
        assert data["model"] == "gpt-5.5"
        assert data["temperature"] == 0.5
        assert data["max_tokens"] == 4096
        assert data["id"].startswith("agent_")

    async def test_create_agent_minimal(self, client: AsyncClient):
        """Agent should be creatable with just name and runner."""
        r = await client.post(
            "/api/agents",
            json={"name": "minimal-agent", "runner": "claude"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["model"] is None
        assert data["system_prompt"] is None

    async def test_create_agent_duplicate_name(self, client: AsyncClient):
        await client.post(
            "/api/agents",
            json={"name": "dup-agent", "runner": "codex"},
        )
        r = await client.post(
            "/api/agents",
            json={"name": "dup-agent", "runner": "claude"},
        )
        assert r.status_code == 409

    async def test_get_agent_by_name(self, client: AsyncClient):
        created = await client.post(
            "/api/agents",
            json={"name": "get-me", "runner": "codex"},
        )
        agent_id = created.json()["id"]

        r = await client.get("/api/agents/get-me")
        assert r.status_code == 200
        assert r.json()["id"] == agent_id

    async def test_get_agent_by_id(self, client: AsyncClient):
        created = await client.post(
            "/api/agents",
            json={"name": "by-id-agent", "runner": "codex"},
        )
        agent_id = created.json()["id"]

        r = await client.get(f"/api/agents/{agent_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "by-id-agent"

    async def test_get_agent_not_found(self, client: AsyncClient):
        r = await client.get("/api/agents/nonexistent")
        assert r.status_code == 404

    async def test_update_agent(self, client: AsyncClient):
        created = await client.post(
            "/api/agents",
            json={"name": "update-me", "runner": "codex"},
        )
        agent_id = created.json()["id"]

        r = await client.patch(
            f"/api/agents/{agent_id}",
            json={"model": "claude-sonnet-4-6", "temperature": 0.8},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["model"] == "claude-sonnet-4-6"
        assert data["temperature"] == 0.8
        assert data["name"] == "update-me"  # unchanged

    async def test_delete_agent(self, client: AsyncClient):
        created = await client.post(
            "/api/agents",
            json={"name": "delete-me", "runner": "codex"},
        )
        agent_id = created.json()["id"]

        r = await client.delete(f"/api/agents/{agent_id}")
        assert r.status_code == 204

        r = await client.get(f"/api/agents/{agent_id}")
        assert r.status_code == 404

    async def test_list_agents(self, client: AsyncClient):
        runners = ["codex", "claude", "openai-compatible"]
        for runner in runners:
            await client.post(
                "/api/agents",
                json={"name": f"list-{runner}", "runner": runner},
            )

        r = await client.get("/api/agents")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
