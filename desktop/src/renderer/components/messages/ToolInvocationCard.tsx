import { ChevronRight, Terminal } from 'lucide-react'
import type { ToolInvocationMessage } from '../../api/types'

export function ToolInvocationCard({ message }: { message: ToolInvocationMessage }) {
  return (
    <div className="rounded-xl border border-app-border bg-app-card overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3">
        <ChevronRight size={15} className="text-app-muted shrink-0" />
        <Terminal size={15} className="text-blue-300 shrink-0" />
        <span className="text-sm font-semibold text-blue-300 shrink-0">{message.toolName}</span>
        <code className="min-w-0 flex-1 truncate font-mono text-sm text-app-secondary">{message.summary}</code>
        <span className="rounded-full bg-app-bg px-2 py-0.5 text-xs text-app-muted shrink-0">{message.status}</span>
      </div>
    </div>
  )
}
