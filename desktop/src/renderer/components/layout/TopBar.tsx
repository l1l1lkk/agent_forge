import { useAppStore } from '../../stores/appStore'
import { useAgentStore } from '../../stores/agentStore'
import { useSessionStore } from '../../stores/sessionStore'
import { Settings, Activity, GitBranch } from 'lucide-react'

export function TopBar() {
  const connectionStatus = useAppStore((s) => s.connectionStatus)
  const daemonLabel = useAppStore((s) => s.daemonLabel)
  const setView = useAppStore((s) => s.setView)
  const agents = useAgentStore((s) => s.agents)
  const selectedAgentId = useAgentStore((s) => s.selectedAgentId)
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId)

  const agent = agents.find((a) => a.id === selectedAgentId)
  const session = agent?.sessions.find((s) => s.id === selectedSessionId)

  const statusClass = connectionStatus === 'connected' ? 'bg-emerald-400' : connectionStatus === 'checking' ? 'bg-yellow-400' : 'bg-red-400'

  return (
    <header className="flex h-11 items-center justify-between border-b border-app-border bg-app-topbar px-4 select-none">
      <div className="flex items-center gap-2">
        <span className="text-lg">🌀</span>
        <span className="font-semibold tracking-tight text-app-text">Agent Forge</span>
      </div>

      <div className="flex min-w-0 flex-1 items-center gap-2 px-8 text-sm">
        <span className="text-base">{agent?.avatar ?? '🤖'}</span>
        <span className="font-medium text-app-text">{agent?.name ?? 'No Agent'}</span>
        <span className="text-app-muted">/</span>
        <span className="font-semibold text-app-text">{session?.name ?? 'No Session'}</span>
        <span className="ml-2 rounded-full bg-app-card px-2 py-0.5 text-xs text-app-muted">{session?.status ?? 'idle'}</span>
      </div>

      <div className="flex items-center gap-3 text-xs text-app-muted">
        <span className={`h-2 w-2 rounded-full ${statusClass}`} />
        <span>{daemonLabel}</span>
        <span>Connected</span>
        <button onClick={() => setView('git')} className="ml-1 rounded-lg p-1.5 text-app-muted hover:bg-app-hover hover:text-app-text" title="Git Workspace">
          <GitBranch size={14} />
        </button>
        <button onClick={() => setView('diagnostics')} className="rounded-lg p-1.5 text-app-muted hover:bg-app-hover hover:text-app-text" title="Diagnostics">
          <Activity size={14} />
        </button>
        <button onClick={() => setView('settings')} className="rounded-lg p-1.5 text-app-muted hover:bg-app-hover hover:text-app-text" title="Settings">
          <Settings size={14} />
        </button>
      </div>
    </header>
  )
}
