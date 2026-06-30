import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { AssistantMessage } from '../../api/types'

function formatTime(iso: string) {
  try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) } catch { return '' }
}

export function AssistantMessageBubble({ message }: { message: AssistantMessage }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="flex justify-start">
      <div className="w-full max-w-4xl">
        <div className="mb-1 flex items-center gap-2 text-sm font-medium text-app-text">
          <span>{message.agentAvatar}</span>
          <span>{message.agentName}</span>
        </div>
        <div className="rounded-xl border border-app-border bg-app-panel px-4 py-3 text-sm leading-6 text-app-text prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        <div className="mt-1 flex items-center gap-2 text-xs text-app-muted opacity-0 hover:opacity-100 transition-opacity">
          <button onClick={handleCopy} className="rounded p-0.5 hover:bg-app-hover hover:text-app-text" title="Copy">
            {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
          </button>
          <span>{formatTime(message.createdAt)}</span>
        </div>
      </div>
    </div>
  )
}
