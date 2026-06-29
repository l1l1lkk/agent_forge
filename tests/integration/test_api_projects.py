"""Integration tests for the Project API."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestProjectAPI:
    """Integration tests for project CRUD endpoints."""

    async def test_list_projects_empty(self, client: AsyncClient):
        r = await client.get("/api/projects")
        assert r.status_code == 200
        data = r.json()
        assert data["projects"] == []
        assert data["total"] == 0

    async def test_create_project(self, client: AsyncClient):
        with tempfile.TemporaryDirectory() as tmpdir:
            r = await client.post(
                "/api/projects",
                json={"root_path": tmpdir, "name": "my-project", "default_runner": "codex"},
            )
            assert r.status_code == 201
            data = r.json()
            assert data["name"] == "my-project"
            assert data["root_path"] == tmpdir
            assert data["default_runner"] == "codex"
            assert data["id"].startswith("proj_")

    async def test_create_project_duplicate_name(self, client: AsyncClient):
        with tempfile.TemporaryDirectory() as tmpdir:
            await client.post(
                "/api/projects",
                json={"root_path": tmpdir, "name": "dup-project"},
            )
            r = await client.post(
                "/api/projects",
                json={"root_path": tmpdir, "name": "dup-project"},
            )
            assert r.status_code == 409

    async def test_create_project_nonexistent_path(self, client: AsyncClient):
        r = await client.post(
            "/api/projects",
            json={"root_path": "/nonexistent/path/12345", "name": "bad-project"},
        )
        assert r.status_code == 400

    async def test_get_project_by_name(self, client: AsyncClient):
        with tempfile.TemporaryDirectory() as tmpdir:
            created = await client.post(
                "/api/projects",
                json={"root_path": tmpdir, "name": "get-by-name"},
            )
            proj_id = created.json()["id"]

            r = await client.get(f"/api/projects/get-by-name")
            assert r.status_code == 200
            assert r.json()["id"] == proj_id

    async def test_get_project_by_id(self, client: AsyncClient):
        with tempfile.TemporaryDirectory() as tmpdir:
            created = await client.post(
                "/api/projects",
                json={"root_path": tmpdir, "name": "get-by-id"},
            )
            proj_id = created.json()["id"]

            r = await client.get(f"/api/projects/{proj_id}")
            assert r.status_code == 200
            assert r.json()["name"] == "get-by-id"

    async def test_get_project_not_found(self, client: AsyncClient):
        r = await client.get("/api/projects/nonexistent")
        assert r.status_code == 404

    async def test_update_project(self, client: AsyncClient):
        with tempfile.TemporaryDirectory() as tmpdir:
            created = await client.post(
                "/api/projects",
                json={"root_path": tmpdir, "name": "update-me"},
            )
            proj_id = created.json()["id"]

            r = await client.patch(
                f"/api/projects/{proj_id}",
                json={"name": "updated-name", "default_runner": "claude"},
            )
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == "updated-name"
            assert data["default_runner"] == "claude"

    async def test_delete_project(self, client: AsyncClient):
        with tempfile.TemporaryDirectory() as tmpdir:
            created = await client.post(
                "/api/projects",
                json={"root_path": tmpdir, "name": "delete-me"},
            )
            proj_id = created.json()["id"]

            r = await client.delete(f"/api/projects/{proj_id}")
            assert r.status_code == 204

            # Verify gone
            r = await client.get(f"/api/projects/{proj_id}")
            assert r.status_code == 404

    async def test_list_projects(self, client: AsyncClient):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                await client.post(
                    "/api/projects",
                    json={"root_path": tmpdir, "name": f"list-proj-{i}"},
                )

            r = await client.get("/api/projects")
            assert r.status_code == 200
            data = r.json()
            assert data["total"] == 3
            assert len(data["projects"]) == 3
