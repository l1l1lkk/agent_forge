"""ClaudeRunner — runs Claude Code CLI as a subprocess.

Spawns `claude -p --output-format stream-json`, parses the JSONL output,
and emits unified forge Events via the event sink.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

from forge.core.events import Event
from forge.db.models import AgentModel, MessageModel, ProjectModel, SessionModel
from forge.runtime.parsers.claude_parser import ClaudeParser
from forge.runtime.runners.base import BaseRunner, EventSink, RunnerResult

logger = logging.getLogger(__name__)


class ClaudeRunner(BaseRunner):
    """Runner that executes Claude Code CLI as a subprocess.

    Builds the claude command with:
      -p (non-interactive print mode)
      --output-format stream-json
      --include-partial-messages
      --model <model>
      --permission-mode acceptEdits (configurable)

    Reads JSONL from stdout, parses into Events, and emits via event_sink.
    """

    name = "claude"

    def __init__(
        self,
        claude_bin: Optional[str] = None,
        permission_mode: str = "acceptEdits",
        extra_args: Optional[list[str]] = None,
    ):
        """
        Args:
            claude_bin: Path to the `claude` executable. Auto-detected if None.
            permission_mode: Claude permission mode (acceptEdits, default, etc.)
            extra_args: Additional CLI arguments to pass to claude.
        """
        self._claude_bin = claude_bin or self._find_claude()
        self._permission_mode = permission_mode
        self._extra_args = extra_args or []
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    @staticmethod
    def _find_claude() -> str:
        """Find the claude CLI binary in PATH."""
        found = shutil.which("claude")
        if found:
            return found
        raise RuntimeError(
            "Claude CLI not found in PATH. Install Claude Code: "
            "https://docs.anthropic.com/en/docs/claude-code/overview"
        )

    async def run_turn(
        self,
        *,
        session: SessionModel,
        agent: AgentModel,
        project: ProjectModel,
        prompt: str,
        history: list[MessageModel],
        event_sink: EventSink,
    ) -> RunnerResult:
        """Execute one turn with Claude Code CLI.

        Builds the command, spawns a subprocess, reads stream-json output,
        parses it into Events, and emits them.
        """
        parser = ClaudeParser(session.id)
        cmd = self._build_command(agent, project, prompt, history)

        logger.info("ClaudeRunner starting: %s", " ".join(cmd))
        logger.debug("CWD: %s", project.root_path)

        try:
            # Create subprocess with line-buffered stdout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=session.cwd or project.root_path,
                env=self._build_env(project, agent),
            )

            # Track process for interrupt
            self._processes[session.id] = process

            collected_messages: list[dict] = []
            stderr_lines: list[str] = []

            # Read stdout line by line
            async for line in process.stdout:
                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                # Parse into Events (now returns list)
                events = parser.parse_line(line_str)
                for event in events:
                    # Emit via event sink
                    try:
                        await event_sink(event)
                    except Exception as e:
                        logger.warning("Event sink error: %s", e)

                    # Collect messages for result
                    if event.type == "thinking_delta":
                        collected_messages.append({
                            "role": "thinking",
                            "content": event.payload.get("text", ""),
                            "signature": event.payload.get("signature", ""),
                        })
                    elif event.type == "assistant_message":
                        text = _extract_text(event.payload)
                        if text:
                            collected_messages.append({
                                "role": "assistant",
                                "content": text,
                            })

            # Read stderr
            if process.stderr:
                stderr_data = await process.stderr.read()
                stderr_text = stderr_data.decode("utf-8", errors="replace")
                if stderr_text.strip():
                    stderr_lines = stderr_text.strip().split("\n")
                    for line in stderr_lines[:10]:  # Log first 10 stderr lines
                        logger.warning("Claude stderr: %s", line)

            # Wait for process to complete
            await process.wait()
            exit_code = process.returncode

            # Clean up process tracking
            self._processes.pop(session.id, None)

            if exit_code != 0:
                error_msg = "\n".join(stderr_lines) if stderr_lines else f"Exit code: {exit_code}"
                logger.error("ClaudeRunner failed (exit %d): %s", exit_code, error_msg[:200])
                return RunnerResult(
                    success=False,
                    messages=collected_messages,
                    error=error_msg,
                )

            logger.info("ClaudeRunner completed successfully")
            return RunnerResult(
                success=True,
                messages=collected_messages,
            )

        except asyncio.CancelledError:
            logger.info("ClaudeRunner cancelled for session %s", session.id)
            await self._kill_process(session.id)
            return RunnerResult(
                success=False,
                messages=collected_messages,
                error="Interrupted",
            )
        except Exception as e:
            logger.exception("ClaudeRunner error: %s", e)
            return RunnerResult(success=False, error=str(e))
        finally:
            self._processes.pop(session.id, None)

    async def interrupt(self, session_id: str) -> None:
        """Interrupt a running Claude process."""
        logger.info("Interrupting session %s", session_id)
        await self._kill_process(session_id)

    async def _kill_process(self, session_id: str) -> None:
        """Kill the subprocess for a session."""
        process = self._processes.get(session_id)
        if process is None:
            return
        try:
            process.kill()
            await process.wait()
        except Exception as e:
            logger.warning("Error killing process: %s", e)

    def _build_command(
        self,
        agent: AgentModel,
        project: ProjectModel,
        prompt: str,
        history: list[MessageModel],
    ) -> list[str]:
        """Build the claude CLI command line."""
        cmd = [
            self._claude_bin,
            "-p",  # non-interactive print mode
            "--verbose",  # required for stream-json with --print
            "--output-format", "stream-json",
            "--include-partial-messages",
        ]

        # Model selection
        if agent.model:
            cmd.extend(["--model", agent.model])

        # System prompt
        if agent.system_prompt:
            cmd.extend(["--append-system-prompt", agent.system_prompt])

        policy = _agent_policy(agent)
        allowed_tools = _tool_lines(policy.get("tool_allow"))
        denied_tools = _tool_lines(policy.get("tool_deny"))
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])
        if denied_tools:
            cmd.extend(["--disallowedTools", ",".join(denied_tools)])

        # Permission mode
        cmd.extend(["--permission-mode", self._permission_mode])

        # Extra args
        cmd.extend(self._extra_args)

        # The prompt
        cmd.append(prompt)

        return cmd

    def _build_env(
        self,
        project: ProjectModel,
        agent: AgentModel,
    ) -> dict[str, str]:
        """Build the environment variables for the subprocess.

        Starts with the current environment, then adds project-specific vars.
        """
        env = os.environ.copy()

        # Add project env vars
        if project.env_json:
            try:
                project_env = json.loads(project.env_json)
                env.update(project_env)
            except json.JSONDecodeError:
                pass

        # Ensure PATH is available
        env.setdefault("PATH", os.environ.get("PATH", ""))

        return env


def _extract_text(payload: dict) -> str:
    """Extract clean text from an assistant_message payload.

    Claude 2.1.196+ wraps text in content_blocks array:
      {"content_blocks": [{"type": "text", "text": "Hello!"}]}
    """
    blocks = payload.get("content_blocks", [])
    texts = []
    for b in blocks:
        if b.get("type") == "text":
            t = b.get("text", "")
            if t.strip():
                texts.append(t)
    return "\n".join(texts)


def _agent_policy(agent: AgentModel) -> dict:
    if not agent.tool_policy_json:
        return {}
    try:
        parsed = json.loads(agent.tool_policy_json)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _tool_lines(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]
