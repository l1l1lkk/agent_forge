"""Runner registry — maps runner names to runner instances."""

from __future__ import annotations

from typing import Optional

from forge.runtime.runners.base import BaseRunner
from forge.runtime.runners.claude_runner import ClaudeRunner


class RunnerRegistry:
    """Registry of available runner implementations.

    Maps runner names (e.g. "claude", "codex") to BaseRunner instances.
    """

    def __init__(self):
        self._runners: dict[str, BaseRunner] = {}

    def register(self, runner: BaseRunner) -> None:
        """Register a runner instance by name."""
        self._runners[runner.name] = runner

    def get(self, name: str) -> Optional[BaseRunner]:
        """Get a runner by name."""
        return self._runners.get(name)

    def list_names(self) -> list[str]:
        """List all registered runner names."""
        return list(self._runners.keys())


# Global registry with default runners
registry = RunnerRegistry()
registry.register(ClaudeRunner())
# Future: registry.register(CodexRunner())
# Future: registry.register(OpenAICompatibleRunner())
