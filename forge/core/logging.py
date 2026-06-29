"""Structured logging for forge-agent."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from forge.core.config import settings

_console: Optional[Console] = None


def get_console() -> Console:
    """Get or create the shared Rich console."""
    global _console
    if _console is None:
        _console = Console(stderr=False)
    return _console


def setup_logging(level: Optional[str] = None) -> None:
    """Configure the root logger with Rich output.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR). Defaults to config.
    """
    log_level = (level or settings.log_level).upper()

    handler = RichHandler(
        console=get_console(),
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
