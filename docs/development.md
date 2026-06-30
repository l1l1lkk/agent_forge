# Development Notes

## Ports

- Backend daemon: `127.0.0.1:8765`.
- Web console: `9999`.
- Desktop renderer: `19999`, configured in
  `desktop/electron.vite.config.ts`.
  During `npm.cmd run dev`, electron-vite may choose the next available port
  if the configured port is already in use.

Before assuming a port is broken, check what is listening:

```cmd
netstat -ano | findstr ":8765"
netstat -ano | findstr ":9999"
```

## Claude CLI From Codex

Use `cmd.exe` and feed long prompts through a task file. Avoid long positional
`-p "..."` prompts because they can be truncated.

```cmd
type claude_task_tmp.txt | claude.cmd -p --permission-mode bypassPermissions --effort high --output-format text
```

Do not ask Claude to start long-lived dev servers unless the task explicitly
requires it. If a Claude run stalls, inspect processes and `git status` before
interrupting; it may have spawned a child process.

## Git Discipline

- Keep user changes. Do not revert files just because they were not authored
  by the current agent.
- Commit versioned batches with the existing style:
  `@ Version x.y.zrcN - Short summary`.
- Update the matching release note under `docs/releases/`.

## Product Rules

- Avoid visible mock data on product surfaces. If persistence is not ready,
  return a real empty state from the backend and make the UI explain the
  missing setup.
- UI buttons that look actionable must either perform the action, open a
  concrete flow, or be hidden until the flow exists.
- Desktop features should work through Electron IPC and browser fallback when
  practical.

## Verification

Run fresh verification before claiming a batch is ready:

```cmd
pytest
cd desktop && npm.cmd run build
git diff --check
```

For desktop UI changes, start the desktop app and perform a rendered smoke
test against the active electron-vite port.
