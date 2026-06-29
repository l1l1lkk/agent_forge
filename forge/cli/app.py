"""Main CLI entry point for forge-agent.

Provides the `forge` command with subcommand groups for all operations.
"""

from __future__ import annotations

from typing import Optional

import typer

from forge import __version__
from forge.cli.commands_project import project_app
from forge.cli.commands_agent import agent_app
from forge.cli.commands_session import session_app
from forge.cli.commands_serve import serve_app
from forge.cli.commands_ask import ask_command, chat_command
from forge.core.config import settings
from forge.core.logging import setup_logging

app = typer.Typer(
    name="forge",
    help="AI Coding CLI Workbench",
    no_args_is_help=True,
    invoke_without_command=True,
)

# Register subcommand groups for management
app.add_typer(project_app, name="project", help="Manage projects")
app.add_typer(agent_app, name="agent", help="Manage agents")
app.add_typer(session_app, name="session", help="Manage sessions")
app.add_typer(serve_app, name="serve", help="Start the daemon")

# Register ask/chat as direct top-level commands
app.command(name="ask")(ask_command)
app.command(name="chat")(chat_command)


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """forge-agent — AI Coding CLI Workbench.

    A CLI-first, daemon-based system for controlling AI coding agents.

    Quick start:
      forge serve                    Start the daemon
      forge project add .            Add current directory as a project
      forge agent create coding --runner claude   Create an agent
      forge ask "Explain this code" --project . --agent coding
    """
    if version:
        typer.echo(f"forge-agent v{__version__}")
        raise typer.Exit()

    if verbose:
        setup_logging("DEBUG")
    else:
        setup_logging()


if __name__ == "__main__":
    app()
