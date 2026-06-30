import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import type { UserMessage } from '../../api/types'

function formatTime(iso: string) {
  try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) } catch { return '' }
}

export function UserMessageBubble({ message }: { message: UserMessage }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="flex justify-end">
      <div className="max-w-2xl">
        <div className="mb-1 text-right text-xs font-medium text-app-muted">You</div>
        <div className="rounded-xl border border-app-accent/40 bg-app-card px-4 py-3 text-sm leading-6 text-app-text shadow-sm">
          {message.content}
        </div>
        <div className="mt-1 flex items-center justify-end gap-2 text-xs text-app-muted opacity-0 hover:opacity-100 transition-opacity">
          <span>{formatTime(message.createdAt)}</span>
          <button onClick={handleCopy} className="rounded p-0.5 hover:bg-app-hover hover:text-app-text" title="Copy">
            {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
          </button>
        </div>
      </div>
    </div>
  )
}
