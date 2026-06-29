"""Shell task runner — executes shell commands as background tasks."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from forge.core.events import Event

logger = logging.getLogger(__name__)


class ShellTaskRunner:
    """Runs shell commands as background tasks with log streaming.

    Manages process lifecycle: start, stream logs, cancel, check status.
    """

    def __init__(self):
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._task_ids: set[str] = set()

    async def start(
        self,
        task_id: str,
        command: str,
        cwd: str,
        env: Optional[dict[str, str]] = None,
        event_sink=None,
    ) -> int:
        """Start a background shell task.

        Returns immediately with the PID. Logs are streamed via event_sink.
        """
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
            env=cmd_env,
        )

        self._processes[task_id] = process
        self._task_ids.add(task_id)

        pid = process.pid
        logger.info("Task %s started (pid=%d): %s", task_id, pid, command[:100])

        # Stream output
        if event_sink and process.stdout:
            async for line in process.stdout:
                text = line.decode("utf-8", errors="replace")
                await event_sink(Event(
                    type="task_log",
                    task_id=task_id,
                    seq=0,
                    payload={"text": text, "pid": pid},
                ))

        return pid

    async def wait(self, task_id: str, timeout: Optional[float] = None) -> int:
        """Wait for a task to complete. Returns exit code."""
        process = self._processes.get(task_id)
        if process is None:
            raise ValueError(f"Task not found: {task_id}")

        try:
            if timeout:
                exit_code = await asyncio.wait_for(process.wait(), timeout=timeout)
            else:
                exit_code = await process.wait()
        except asyncio.TimeoutError:
            process.kill()
            exit_code = -1

        self._processes.pop(task_id, None)
        self._task_ids.discard(task_id)
        return exit_code or 0

    async def cancel(self, task_id: str) -> None:
        """Cancel/kill a running task."""
        process = self._processes.get(task_id)
        if process is None:
            return
        try:
            process.kill()
            await process.wait()
        except Exception:
            pass
        self._processes.pop(task_id, None)
        self._task_ids.discard(task_id)

    def is_running(self, task_id: str) -> bool:
        """Check if a task is still running."""
        process = self._processes.get(task_id)
        if process is None:
            return False
        return process.returncode is None

    @property
    def running_tasks(self) -> list[str]:
        """List running task IDs."""
        return list(self._task_ids)


# Global instance
shell_runner = ShellTaskRunner()
