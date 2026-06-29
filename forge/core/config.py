"""Configuration management for forge-agent.

Loads settings from .env file and FORGE_* environment variables.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and .env file."""

    model_config = SettingsConfigDict(
        env_prefix="FORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Daemon ---
    host: str = "127.0.0.1"
    port: int = 8765

    # --- Database ---
    db_path: str = ""  # Empty = auto-detect ~/.forge/forge.db

    # --- Auth ---
    auth_token: Optional[str] = None

    # --- Logging ---
    log_level: str = "INFO"

    # --- Data directory ---
    data_dir: str = ""  # Empty = auto-detect ~/.forge

    # --- Cloudflare ---
    cloudflared_bin: str = "cloudflared"

    @property
    def resolved_data_dir(self) -> Path:
        """Resolve the data directory path."""
        if self.data_dir:
            return Path(self.data_dir).expanduser().resolve()
        return Path.home() / ".forge"

    @property
    def resolved_db_path(self) -> Path:
        """Resolve the SQLite database path."""
        if self.db_path:
            return Path(self.db_path).expanduser().resolve()
        data = self.resolved_data_dir
        data.mkdir(parents=True, exist_ok=True)
        return data / "forge.db"

    @property
    def database_url(self) -> str:
        """Construct the async SQLite connection URL."""
        db = self.resolved_db_path
        return f"sqlite+aiosqlite:///{db}"


# Global settings singleton
settings = Settings()
