"""Tests for the runner registry."""

from __future__ import annotations

import json

from forge.db.models import AgentModel, ProjectModel
from forge.runtime.runners.registry import RunnerRegistry, registry
from forge.runtime.runners.claude_runner import ClaudeRunner


class TestRunnerRegistry:
    """Tests for the runner registry."""

    def test_default_registry_has_claude(self):
        """The global registry should have the Claude runner registered."""
        runner = registry.get("claude")
        assert runner is not None
        assert isinstance(runner, ClaudeRunner)
        assert runner.name == "claude"

    def test_registry_list_names(self):
        """Should list all registered runner names."""
        names = registry.list_names()
        assert "claude" in names

    def test_registry_get_missing(self):
        """Should return None for unknown runners."""
        runner = registry.get("nonexistent_runner")
        assert runner is None

    def test_custom_registry(self):
        """Should support registering custom runners."""
        reg = RunnerRegistry()
        runner = ClaudeRunner()
        reg.register(runner)
        assert reg.get("claude") is runner
        assert "claude" in reg.list_names()


class TestClaudeRunnerCommand:
    def test_tool_allow_and_deny_are_passed_to_cli(self):
        runner = ClaudeRunner(claude_bin="claude")
        agent = AgentModel(
            id="agent_test",
            name="reviewer",
            runner="claude",
            tool_policy_json=json.dumps({
                "tool_allow": "Read\nGrep",
                "tool_deny": "Write\nEdit",
            }),
        )
        project = ProjectModel(id="proj_test", name="proj", root_path="D:\\agentforge")

        cmd = runner._build_command(agent, project, "hello", [])

        assert cmd[cmd.index("--allowedTools") + 1] == "Read,Grep"
        assert cmd[cmd.index("--disallowedTools") + 1] == "Write,Edit"
