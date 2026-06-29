import type { AgentSession } from '../../api/types'
import { useSessionStore } from '../../stores/sessionStore'

export function SessionTreeItem({ session }: { session: AgentSession }) {
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId)
  const selectSession = useSessionStore((s) => s.selectSession)
  const isSelected = selectedSessionId === session.id

  const dotColor = session.status === 'running' ? 'bg-blue-400' : session.status === 'error' ? 'bg-red-400' : session.unread ? 'bg-app-accent' : 'bg-app-muted'

  return (
    <button
      className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm ${isSelected ? 'bg-app-selected text-app-text' : 'text-app-secondary hover:bg-app-hover hover:text-app-text'}`}
      onClick={() => selectSession(session.id)}
    >
      <span className={`h-2 w-2 shrink-0 rounded-full ${dotColor}`} />
      {session.hidden && <span className="text-app-muted text-xs">👁</span>}
      <span className={`min-w-0 truncate ${session.hidden ? 'text-app-muted' : ''}`}>{session.name}</span>
    </button>
  )
}
