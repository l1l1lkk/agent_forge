import { useState } from 'react'
import { ChevronRight, ChevronDown, Copy, Check } from 'lucide-react'
import type { ToolResultMessage } from '../../api/types'

export function ToolResultCard({ message }: { message: ToolResultMessage }) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  const lines = (message.content || '').split('\n')
  const firstLine = lines[0] || '(empty)'
  const hasMore = lines.length > 1

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="rounded-xl border border-app-border bg-app-card overflow-hidden group">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-start gap-3 px-4 py-3 text-left"
      >
        {expanded ? <ChevronDown size={15} className="mt-0.5 text-app-muted shrink-0" /> : <ChevronRight size={15} className="mt-0.5 text-app-muted shrink-0" />}
        <span className={`rounded px-1.5 py-0.5 text-xs font-bold uppercase shrink-0 ${message.exitCode === 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
          Result
        </span>
        <pre className="min-w-0 flex-1 overflow-hidden font-mono text-sm leading-6 text-app-secondary whitespace-pre-wrap">
          {expanded ? message.content : firstLine}
        </pre>
      </button>
      {expanded && hasMore && (
        <div className="px-4 pb-3 pl-12 relative">
          <pre className="font-mono text-sm text-app-secondary whitespace-pre-wrap break-all max-h-96 overflow-y-auto">
            {lines.slice(1).join('\n')}
          </pre>
          <button
            onClick={handleCopy}
            className="absolute top-0 right-3 opacity-0 group-hover:opacity-100 rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text"
          >
            {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
          </button>
        </div>
      )}
    </div>
  )
}
