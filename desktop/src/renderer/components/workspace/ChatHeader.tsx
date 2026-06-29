import { useAgentStore } from '../../stores/agentStore'
import { useSessionStore } from '../../stores/sessionStore'

export function ChatHeader() {
  const agents = useAgentStore((s) => s.agents)
  const selectedAgentId = useAgentStore((s) => s.selectedAgentId)
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId)
  const agent = agents.find((a) => a.id === selectedAgentId)
  const session = agent?.sessions.find((s) => s.id === selectedSessionId)

  return (
    <div className="flex h-12 shrink-0 items-center justify-between border-b border-app-border bg-app-bg px-5">
      <div className="flex min-w-0 items-center gap-2">
        <span>{agent?.avatar}</span>
        <span className="text-sm font-medium text-app-muted">{agent?.name}</span>
        <span className="text-app-muted">/</span>
        <span className="truncate text-sm font-semibold text-app-text">{session?.name}</span>
        <span className="ml-2 rounded-full bg-app-card px-2 py-0.5 text-xs text-app-muted">{session?.status ?? 'idle'}</span>
      </div>
      <div className="flex items-center gap-2 text-xs text-app-muted">
        <span className="h-2 w-2 rounded-full bg-emerald-400" />
        <span>Connected</span>
      </div>
    </div>
  )
}
