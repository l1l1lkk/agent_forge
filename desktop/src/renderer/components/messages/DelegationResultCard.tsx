import { ArrowUpRight, CornerDownLeft } from 'lucide-react'
import type { DelegationResultMessage } from '../../api/types'
import { useNavigationStore } from '../../stores/navigationStore'

export function DelegationResultCard({ message }: { message: DelegationResultMessage }) {
  const openChat = useNavigationStore((s) => s.openChat)

  return (
    <div className="rounded-xl border border-blue-500/30 bg-blue-950/20 px-4 py-3">
      <div className="mb-2 flex items-center justify-between gap-3 text-xs text-blue-200">
        <div className="flex min-w-0 items-center gap-2">
          <CornerDownLeft size={14} />
          <span className="truncate">
            From delegation {message.delegationId}
            {message.agentName ? ` · ${message.agentName}` : ''}
          </span>
        </div>
        {message.childSessionId && (
          <button
            className="flex shrink-0 items-center gap-1 rounded-md px-2 py-1 text-blue-200 hover:bg-blue-900/30 hover:text-blue-100"
            onClick={() => openChat({ agentId: message.agentId, sessionId: message.childSessionId })}
            title="Open delegated session"
          >
            <ArrowUpRight size={13} />
            <span>Open session</span>
          </button>
        )}
      </div>
      <div className="whitespace-pre-wrap text-sm leading-6 text-app-text">{message.content}</div>
    </div>
  )
}
