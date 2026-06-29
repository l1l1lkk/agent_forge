# forge-agent

**AI Coding CLI Workbench** — A CLI-first, daemon-based system for controlling AI coding agents.

## Overview

forge-agent is not a chatbot or a chat UI. It's a developer workbench built around:
- **Projects & workspaces** — every agent operation is scoped to a project
- **Sessions & messages** — persistent, queryable conversation history
- **Daemon architecture** — long-running background service, not tied to a terminal
- **CLI-first** — all functionality available via `forge` commands
- **Runner pluggable** — Codex, Claude, local models (coming in future milestones)

## Installation

### Requirements

- Python 3.12+
- pip

### Install from source

```bash
git clone https://github.com/forge-agent/forge-agent.git
cd forge-agent
pip install -e ".[dev]"
```

## Quick Start

### 1. Start the daemon

```bash
forge serve
```

The daemon starts on `http://127.0.0.1:8765`. Health check:

```bash
curl http://127.0.0.1:8765/api/health
# {"status":"ok","version":"0.1.0"}
```

### 2. Add a project

```bash
forge project add /path/to/your/repo --name my-project
forge project list
```

### 3. Create an agent

```bash
forge agent create coding \
  --runner codex \
  --model gpt-5.5 \
  --system-prompt "You are a senior Python engineer."

forge agent list
```

### 4. Start a session

```bash
forge session create \
  --project my-project \
  --agent coding \
  --title "Exploring the codebase"

forge session list
```

### 5. View a session

```bash
forge session open ses_xxxxxxxx
```

## CLI Reference

### Daemon commands

```bash
forge serve                    # Start daemon (default: 127.0.0.1:8765)
forge serve --host 0.0.0.0 --port 9000
```

### Project commands

```bash
forge project add <path>                   # Add a project
forge project add <path> --name <name>     # Add with custom name
forge project add <path> --runner codex    # Set default runner
forge project list                         # List all projects
forge project show <name-or-id>            # Show project details
forge project remove <name-or-id>          # Delete project
forge project env <name-or-id>             # View env vars
forge project env <name> --set KEY=VALUE   # Set env vars
```

### Agent commands

```bash
forge agent create <name> --runner <runner>
forge agent create <name> --runner codex --model gpt-5.5
forge agent list
forge agent show <name-or-id>
forge agent edit <name-or-id> --model claude-sonnet-4-6
forge agent delete <name-or-id>
```

### Session commands

```bash
forge session create --project <proj> --agent <agent>
forge session create --project <proj> --agent <agent> --title "Title"
forge session list
forge session list --project <proj>
forge session open <session-id>
forge session delete <session-id>
```

## API Reference

The daemon exposes a REST API at `http://127.0.0.1:8765/api/`.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Get project |
| PATCH | `/api/projects/{id}` | Update project |
| DELETE | `/api/projects/{id}` | Delete project |
| GET | `/api/agents` | List agents |
| POST | `/api/agents` | Create agent |
| GET | `/api/agents/{id}` | Get agent |
| PATCH | `/api/agents/{id}` | Update agent |
| DELETE | `/api/agents/{id}` | Delete agent |
| GET | `/api/sessions` | List sessions |
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions/{id}` | Get session |
| DELETE | `/api/sessions/{id}` | Delete session |
| GET | `/api/sessions/{id}/messages` | Get messages |
| POST | `/api/sessions/{id}/messages` | Add message |
| WS | `/ws` | WebSocket (placeholder) |

### Authentication

Set `FORGE_AUTH_TOKEN` in `.env` to require Bearer token authentication on all non-health endpoints.

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
FORGE_HOST=127.0.0.1
FORGE_PORT=8765
FORGE_LOG_LEVEL=INFO
# FORGE_AUTH_TOKEN=my-secret-token
# FORGE_DB_PATH=/custom/path/forge.db
```

## Architecture

```
CLI (Typer)  →  HTTP/httpx  →  FastAPI Daemon  →  SQLAlchemy  →  SQLite
                                  ↓
                            Services Layer
                         (Project/Agent/Session Managers)
                                  ↓
                            Repository Layer
```

- **`forge/core/`** — Config, ID generation, errors, events, security
- **`forge/db/`** — SQLAlchemy models, repositories, session management
- **`forge/services/`** — Business logic (ProjectManager, AgentManager, SessionManager)
- **`forge/api/`** — FastAPI app, routers, schemas, middleware
- **`forge/cli/`** — Typer CLI commands, API client
- **`forge/runtime/`** — Runner and tool abstractions (future milestones)

## Development

### Run tests

```bash
pytest
```

### Run with coverage

```bash
pytest --cov=forge --cov-report=term
```

## Milestone Status

| Milestone | Status |
|-----------|--------|
| M0: Project Init | Done |
| M1: Project & Agent CRUD | Done |
| M2: Session & Message Persistence | Done |
| M3: CodexRunner | Planned |
| M4: WebSocket Events | Planned |
| M5: Web UI MVP | Planned |
| M6: Background Tasks | Planned |
| M7: Security System | Planned |
| M8: Cloudflare Tunnel | Planned |
| M9: Scheduled Tasks | Planned |
| M10: Multi-Runner | Planned |

## License

MIT
