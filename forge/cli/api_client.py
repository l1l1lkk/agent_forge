"""HTTP client for CLI → daemon communication."""

from __future__ import annotations

from typing import Any, Optional

import httpx
from rich.console import Console

from forge.core.config import settings


class APIClient:
    """Async HTTP client for talking to the forge-agent daemon API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.base_url = (base_url or f"http://{settings.host}:{settings.port}").rstrip("/")
        self.token = token or settings.auth_token
        self.console = Console()

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    # ── Projects ────────────────────────────────────────────────

    def list_projects(self) -> list[dict]:
        with httpx.Client() as client:
            r = client.get(self._url("/api/projects"), headers=self._headers())
            r.raise_for_status()
            return r.json()["projects"]

    def create_project(self, **data) -> dict:
        with httpx.Client() as client:
            r = client.post(
                self._url("/api/projects"),
                json=data,
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def get_project(self, identifier: str) -> dict:
        with httpx.Client() as client:
            r = client.get(
                self._url(f"/api/projects/{identifier}"),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def update_project(self, identifier: str, **data) -> dict:
        with httpx.Client() as client:
            r = client.patch(
                self._url(f"/api/projects/{identifier}"),
                json=data,
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def delete_project(self, identifier: str) -> None:
        with httpx.Client() as client:
            r = client.delete(
                self._url(f"/api/projects/{identifier}"),
                headers=self._headers(),
            )
            r.raise_for_status()

    # ── Agents ───────────────────────────────────────────────────

    def list_agents(self) -> list[dict]:
        with httpx.Client() as client:
            r = client.get(self._url("/api/agents"), headers=self._headers())
            r.raise_for_status()
            return r.json()["agents"]

    def create_agent(self, **data) -> dict:
        with httpx.Client() as client:
            r = client.post(
                self._url("/api/agents"),
                json=data,
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def get_agent(self, identifier: str) -> dict:
        with httpx.Client() as client:
            r = client.get(
                self._url(f"/api/agents/{identifier}"),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def update_agent(self, identifier: str, **data) -> dict:
        with httpx.Client() as client:
            r = client.patch(
                self._url(f"/api/agents/{identifier}"),
                json=data,
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def delete_agent(self, identifier: str) -> None:
        with httpx.Client() as client:
            r = client.delete(
                self._url(f"/api/agents/{identifier}"),
                headers=self._headers(),
            )
            r.raise_for_status()

    # ── Sessions ─────────────────────────────────────────────────

    def list_sessions(self, project_id: Optional[str] = None) -> list[dict]:
        with httpx.Client() as client:
            params = {}
            if project_id:
                params["project_id"] = project_id
            r = client.get(
                self._url("/api/sessions"),
                params=params,
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()["sessions"]

    def create_session(self, **data) -> dict:
        with httpx.Client() as client:
            r = client.post(
                self._url("/api/sessions"),
                json=data,
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def get_session(self, session_id: str) -> dict:
        with httpx.Client() as client:
            r = client.get(
                self._url(f"/api/sessions/{session_id}"),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def get_messages(self, session_id: str) -> list[dict]:
        with httpx.Client() as client:
            r = client.get(
                self._url(f"/api/sessions/{session_id}/messages"),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()["messages"]

    def add_message(self, session_id: str, role: str, content: str) -> dict:
        with httpx.Client() as client:
            r = client.post(
                self._url(f"/api/sessions/{session_id}/messages"),
                json={"role": role, "content": content},
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def run_turn(self, session_id: str, prompt: str) -> dict:
        """Send a user message and trigger an AI turn. Returns the user message."""
        with httpx.Client(timeout=300.0) as client:
            r = client.post(
                self._url(f"/api/sessions/{session_id}/messages"),
                json={"role": "user", "content": prompt, "run": True},
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def interrupt_session(self, session_id: str) -> dict:
        """Interrupt a running session."""
        with httpx.Client() as client:
            r = client.post(
                self._url(f"/api/sessions/{session_id}/interrupt"),
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    def delete_session(self, session_id: str) -> None:
        with httpx.Client() as client:
            r = client.delete(
                self._url(f"/api/sessions/{session_id}"),
                headers=self._headers(),
            )
            r.raise_for_status()


# Singleton client
_client: Optional[APIClient] = None


def get_client() -> APIClient:
    """Get or create the global API client."""
    global _client
    if _client is None:
        _client = APIClient()
    return _client
