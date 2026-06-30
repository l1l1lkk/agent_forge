"""Integration tests for desktop-specific API endpoints."""

from __future__ import annotations

import shutil
import subprocess

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


def _git(cwd, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


async def test_desktop_git_status_preserves_porcelain_paths(client: AsyncClient, tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    tracked = tmp_path / "desktop.txt"
    tracked.write_text("v1\n")
    _git(tmp_path, "add", "desktop.txt")
    _git(tmp_path, "commit", "-qm", "init")
    tracked.unlink()

    response = await client.get(
        "/api/desktop/git-status",
        params={"path": str(tmp_path)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["in_repo"] is True
    assert data["dirty_count"] == 1
    assert data["dirty_files"] == ["desktop.txt"]
    assert data["branch"] in {"master", "main"}
    assert " init " in data["recent_commits"][0]["raw"]


async def test_desktop_diagnostics_reports_runner_and_db_counts(client: AsyncClient):
    response = await client.get("/api/desktop/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert data["health"]["status"] == "ok"
    assert "runners" in data
    assert data["db"]["projects"] == 0
    assert data["features"]["websocket"] is True


# git-diff tests


async def test_desktop_git_diff_returns_unified_diff_for_modified_tracked_file(
    client: AsyncClient, tmp_path,
):
    """GET /api/desktop/git-diff?path=<repo>&file=<filename> returns unified diff."""
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    # Setup: init repo, commit a tracked file, then modify it
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    readme = tmp_path / "README.md"
    readme.write_text("# Hello\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-qm", "initial commit")

    # Modify the tracked file
    readme.write_text("# Hello\n\nWorld\n")

    response = await client.get(
        "/api/desktop/git-diff",
        params={"path": str(tmp_path), "file": "README.md"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:500]}"
    body = response.text

    # Unified diff markers
    assert "---" in body, f"Missing '---' header in diff:\n{body[:500]}"
    assert "+++" in body, f"Missing '+++' header in diff:\n{body[:500]}"

    # Preserves the full filename in the diff header
    assert "README.md" in body, f"Filename 'README.md' not found in diff:\n{body[:500]}"

    # Contains the actual diff hunk: added line "+World"
    assert "+World" in body, f"Expected '+World' line in diff:\n{body[:500]}"


async def test_desktop_git_diff_returns_empty_for_unmodified_tracked_file(
    client: AsyncClient, tmp_path,
):
    """GET /api/desktop/git-diff returns empty or clean diff for an unmodified tracked file."""
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    f = tmp_path / "clean.txt"
    f.write_text("unchanged\n")
    _git(tmp_path, "add", "clean.txt")
    _git(tmp_path, "commit", "-qm", "initial")

    response = await client.get(
        "/api/desktop/git-diff",
        params={"path": str(tmp_path), "file": "clean.txt"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:500]}"
    body = response.text.strip()
    # No modifications means diff should be empty or contain no change hunks
    assert body == "" or "@@" not in body, f"Expected empty diff for clean file:\n{body[:500]}"


async def test_desktop_git_diff_rejects_path_traversal(client: AsyncClient, tmp_path):
    """Path-traversal in 'file' param must be rejected with non-200."""
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    # Attempt to escape with ../ in filename
    response = await client.get(
        "/api/desktop/git-diff",
        params={"path": str(tmp_path), "file": "../secrets.txt"},
    )

    assert response.status_code != 200, (
        f"Path traversal must be rejected. Got {response.status_code}: {response.text[:500]}"
    )


async def test_desktop_git_diff_rejects_file_outside_repo(client: AsyncClient, tmp_path):
    """A file outside the repo root must be rejected with non-200."""
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    outside = tmp_path / "outside.txt"
    outside.write_text("data\n")

    # The file is inside tmp_path but at the repo root; this should be fine.
    # To test "outside repo", use an absolute path to a non-existent file in the parent.
    # Actually, for a repo in tmp_path, the parent is the system temp dir.
    # Instead, construct an absolute path that resolves outside tmp_path.
    import os
    outside_abs = os.path.abspath(os.path.join(str(tmp_path), "..", "outside_file.txt"))

    response = await client.get(
        "/api/desktop/git-diff",
        params={"path": str(tmp_path), "file": outside_abs},
    )

    assert response.status_code != 200, (
        f"File outside repo must be rejected. Got {response.status_code}: {response.text[:500]}"
    )


async def test_desktop_git_diff_rejects_absolute_file_inside_repo(client: AsyncClient, tmp_path):
    """The file parameter must be repo-relative, not an absolute path."""
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    tracked = tmp_path / "absolute.txt"
    tracked.write_text("v1\n")
    _git(tmp_path, "add", "absolute.txt")
    _git(tmp_path, "commit", "-qm", "initial")
    tracked.write_text("v2\n")

    response = await client.get(
        "/api/desktop/git-diff",
        params={"path": str(tmp_path), "file": str(tracked)},
    )

    assert response.status_code != 200, (
        f"Absolute file param must be rejected. Got {response.status_code}: {response.text[:500]}"
    )


async def test_desktop_git_diff_rejects_missing_file_param(client: AsyncClient, tmp_path):
    """Calling git-diff without the 'file' param must return non-200."""
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    response = await client.get(
        "/api/desktop/git-diff",
        params={"path": str(tmp_path)},
    )

    assert response.status_code != 200, (
        f"Missing 'file' param must be rejected. Got {response.status_code}: {response.text[:500]}"
    )


async def test_desktop_git_diff_rejects_nonexistent_file(client: AsyncClient, tmp_path):
    """A filename that doesn't exist in the repo must return non-200."""
    if shutil.which("git") is None:
        pytest.skip("git is not available")

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")

    response = await client.get(
        "/api/desktop/git-diff",
        params={"path": str(tmp_path), "file": "nonexistent.py"},
    )

    assert response.status_code != 200, (
        f"Nonexistent file must be rejected. Got {response.status_code}: {response.text[:500]}"
    )
