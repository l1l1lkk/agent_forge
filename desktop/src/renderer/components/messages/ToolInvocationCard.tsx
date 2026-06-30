import { useState } from 'react'
import { ChevronRight, ChevronDown, Terminal, Copy, Check } from 'lucide-react'
import type { ToolInvocationMessage } from '../../api/types'

export function ToolInvocationCard({ message }: { message: ToolInvocationMessage }) {
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  const firstLine = message.summary?.split('\n')[0] || message.toolName
  const hasMore = (message.summary?.includes('\n') || message.command)

  const handleCopy = () => {
    const text = message.command || message.summary
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="rounded-xl border border-app-border bg-app-card overflow-hidden group">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        {expanded ? <ChevronDown size={15} className="text-app-muted shrink-0" /> : <ChevronRight size={15} className="text-app-muted shrink-0" />}
        <Terminal size={15} className="text-blue-300 shrink-0" />
        <span className="text-sm font-semibold text-blue-300 shrink-0">{message.toolName}</span>
        <code className="min-w-0 flex-1 truncate font-mono text-sm text-app-secondary">
          {expanded ? (message.summary || message.command) : firstLine}
        </code>
        <span className="rounded-full bg-app-bg px-2 py-0.5 text-xs text-app-muted shrink-0">{message.status}</span>
      </button>
      {expanded && (
        <div className="px-4 pb-3 pl-12 relative">
          <pre className="font-mono text-sm text-app-secondary whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
            {message.command || message.summary}
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
