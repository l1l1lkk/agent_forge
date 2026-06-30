"""Integration tests for the Session API."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSessionAPI:
    """Integration tests for session and message endpoints."""

    async def _setup_project_and_agent(self, client: AsyncClient):
        """Create a test project and agent, return their IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pr = await client.post(
                "/api/projects",
                json={"root_path": tmpdir, "name": "session-test-project"},
            )
            proj_id = pr.json()["id"]

            ar = await client.post(
                "/api/agents",
                json={"name": "session-test-agent", "runner": "codex"},
            )
            agent_id = ar.json()["id"]

            return proj_id, agent_id

    async def test_create_session(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)

        r = await client.post(
            "/api/sessions",
            json={
                "project": proj_id,
                "agent": agent_id,
                "title": "Integration Test Session",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["id"].startswith("ses_")
        assert data["status"] == "idle"
        assert data["runner"] == "codex"
        assert data["title"] == "Integration Test Session"

    async def test_create_session_by_names(self, client: AsyncClient):
        """Sessions should be creatable using project/agent names."""
        proj_id, agent_id = await self._setup_project_and_agent(client)

        r = await client.post(
            "/api/sessions",
            json={
                "project": "session-test-project",
                "agent": "session-test-agent",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["project_id"] == proj_id
        assert data["agent_id"] == agent_id

    async def test_create_session_nonexistent_project(self, client: AsyncClient):
        r = await client.post(
            "/api/sessions",
            json={"project": "nonexistent", "agent": "nonexistent"},
        )
        assert r.status_code == 404

    async def test_get_session(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)

        created = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )
        ses_id = created.json()["id"]

        r = await client.get(f"/api/sessions/{ses_id}")
        assert r.status_code == 200
        assert r.json()["id"] == ses_id

    async def test_get_session_not_found(self, client: AsyncClient):
        r = await client.get("/api/sessions/ses_nonexistent")
        assert r.status_code == 404

    async def test_add_message(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)

        created = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )
        ses_id = created.json()["id"]

        r = await client.post(
            f"/api/sessions/{ses_id}/messages",
            json={"role": "user", "content": "Hello, help me code!"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["role"] == "user"
        assert data["content"] == "Hello, help me code!"
        assert data["seq"] == 1

    async def test_add_message_invalid_role(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)

        created = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )
        ses_id = created.json()["id"]

        r = await client.post(
            f"/api/sessions/{ses_id}/messages",
            json={"role": "invalid_role", "content": "test"},
        )
        assert r.status_code == 400

    async def test_get_messages(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)

        created = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )
        ses_id = created.json()["id"]

        # Add some messages
        for i, role in enumerate(["user", "assistant", "user"]):
            await client.post(
                f"/api/sessions/{ses_id}/messages",
                json={"role": role, "content": f"Message {i+1}"},
            )

        r = await client.get(f"/api/sessions/{ses_id}/messages")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        assert data["messages"][0]["seq"] == 1
        assert data["messages"][1]["seq"] == 2
        assert data["messages"][2]["seq"] == 3

    async def test_message_seq_auto_increment(self, client: AsyncClient):
        """Multiple messages should get sequential seq numbers."""
        proj_id, agent_id = await self._setup_project_and_agent(client)

        created = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )
        ses_id = created.json()["id"]

        for i in range(5):
            r = await client.post(
                f"/api/sessions/{ses_id}/messages",
                json={"role": "user", "content": f"msg-{i}"},
            )
            assert r.json()["seq"] == i + 1

    async def test_delete_session(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)

        created = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )
        ses_id = created.json()["id"]

        r = await client.delete(f"/api/sessions/{ses_id}")
        assert r.status_code == 204

        r = await client.get(f"/api/sessions/{ses_id}")
        assert r.status_code == 404

    async def test_list_sessions(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)

        for _ in range(3):
            await client.post(
                "/api/sessions",
                json={"project": proj_id, "agent": agent_id},
            )

        r = await client.get("/api/sessions")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3

    async def test_list_sessions_filtered_by_project(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)

        await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )

        r = await client.get(f"/api/sessions?project_id={proj_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1

    async def test_create_delegation_session(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)
        reviewer = await client.post(
            "/api/agents",
            json={"name": "reviewer-agent", "runner": "codex"},
        )
        reviewer_id = reviewer.json()["id"]
        parent = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id, "title": "Parent"},
        )
        parent_id = parent.json()["id"]

        r = await client.post(
            f"/api/sessions/{parent_id}/delegations",
            json={"agent": reviewer_id, "request": "Review auth.py", "title": "Review auth"},
        )

        assert r.status_code == 201
        data = r.json()
        assert data["delegation_id"].startswith("dlg_")
        assert data["parent_session_id"] == parent_id
        child = data["child_session"]
        assert child["agent_id"] == reviewer_id
        assert child["title"] == "Review auth"
        assert "\"parent_session_id\"" in child["metadata_json"]
        assert data["parent_message"]["role"] == "tool_call"

        child_messages = await client.get(f"/api/sessions/{child['id']}/messages")
        assert child_messages.json()["total"] == 1
        assert "Delegation protocol" in child_messages.json()["messages"][0]["content"]

    async def test_complete_delegation_injects_parent_result(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)
        reviewer = await client.post(
            "/api/agents",
            json={"name": "reviewer-result-agent", "runner": "codex"},
        )
        parent = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )
        delegation = await client.post(
            f"/api/sessions/{parent.json()['id']}/delegations",
            json={"agent": reviewer.json()["id"], "request": "Review the patch"},
        )
        child_id = delegation.json()["child_session"]["id"]

        result = await client.post(
            f"/api/sessions/{child_id}/delegation-result",
            json={"content": "No blocking issues."},
        )

        assert result.status_code == 201
        assert result.json()["content"] == "No blocking issues."
        parent_messages = await client.get(f"/api/sessions/{parent.json()['id']}/messages")
        injected = parent_messages.json()["messages"][-1]
        assert injected["role"] == "assistant"
        assert "delegation_result" in injected["metadata_json"]

    async def test_continue_delegation_reuses_child_session(self, client: AsyncClient):
        proj_id, agent_id = await self._setup_project_and_agent(client)
        reviewer = await client.post(
            "/api/agents",
            json={"name": "reviewer-continue-agent", "runner": "codex"},
        )
        parent = await client.post(
            "/api/sessions",
            json={"project": proj_id, "agent": agent_id},
        )
        first = await client.post(
            f"/api/sessions/{parent.json()['id']}/delegations",
            json={"agent": reviewer.json()["id"], "request": "Initial review"},
        )
        delegation_id = first.json()["delegation_id"]
        child_id = first.json()["child_session"]["id"]

        second = await client.post(
            f"/api/sessions/{parent.json()['id']}/delegations",
            json={"delegation_id": delegation_id, "request": "Check the fixes"},
        )

        assert second.status_code == 201
        assert second.json()["child_session"]["id"] == child_id
        child_messages = await client.get(f"/api/sessions/{child_id}/messages")
        assert child_messages.json()["total"] == 2
        assert "Check the fixes" in child_messages.json()["messages"][1]["content"]
