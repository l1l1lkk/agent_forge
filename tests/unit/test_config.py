"""Tests for configuration management."""

from __future__ import annotations

from pathlib import Path

from forge.core.config import Settings


class TestSettings:
    """Tests for the Settings class."""

    def test_defaults(self):
        """Settings should have sensible defaults."""
        s = Settings()
        assert s.host == "127.0.0.1"
        assert s.port == 8765
        assert s.log_level == "INFO"

    def test_resolved_db_path_default(self):
        """Default DB path should be under ~/.forge."""
        s = Settings()
        db_path = s.resolved_db_path
        assert db_path.name == "forge.db"
        assert ".forge" in str(db_path)

    def test_resolved_db_path_custom(self):
        """Custom DB path should be respected."""
        s = Settings(db_path="/tmp/test_forge.db")
        resolved = s.resolved_db_path
        assert resolved.name == "test_forge.db"
        # On Windows, /tmp resolves to CWD drive root, so we just check the name
        assert "test_forge.db" in str(resolved)

    def test_database_url(self):
        """Database URL should be an async SQLite connection string."""
        s = Settings(db_path="/tmp/test_forge.db")
        url = s.database_url
        assert url.startswith("sqlite+aiosqlite:///")
        assert "test_forge.db" in url
