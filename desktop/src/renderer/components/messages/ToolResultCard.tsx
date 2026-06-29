import { ChevronRight } from 'lucide-react'
import type { ToolResultMessage } from '../../api/types'

export function ToolResultCard({ message }: { message: ToolResultMessage }) {
  return (
    <div className="rounded-xl border border-app-border bg-app-card overflow-hidden">
      <div className="flex items-start gap-3 px-4 py-3">
        <ChevronRight size={15} className="mt-0.5 text-app-muted shrink-0" />
        <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-xs font-bold uppercase text-emerald-400 shrink-0">Result</span>
        <pre className="min-w-0 flex-1 overflow-hidden whitespace-pre-wrap break-words font-mono text-sm leading-6 text-app-secondary">
          {message.content}
        </pre>
      </div>
    </div>
  )
}
