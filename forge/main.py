"""Main entry point for forge-agent CLI.

The `forge` command is registered as a console script in pyproject.toml.
This module just invokes the Typer app defined in forge.cli.app.
"""

from __future__ import annotations


def main() -> None:
    """Entry point for the `forge` CLI command."""
    from forge.cli.app import app

    app()


if __name__ == "__main__":
    main()
