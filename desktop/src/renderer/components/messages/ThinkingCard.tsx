import { useState } from 'react'
import { ChevronDown, ChevronRight, Brain } from 'lucide-react'

export function ThinkingCard({ thinking }: { thinking: string }) {
  const [expanded, setExpanded] = useState(false)

  if (!thinking.trim()) return null

  return (
    <div className="flex justify-start">
      <div className="w-full max-w-4xl">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-xs text-app-muted hover:text-app-secondary mb-1"
        >
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          <Brain size={12} />
          <span>Thinking</span>
        </button>
        {expanded && (
          <div className="rounded-xl border border-app-border bg-app-card/50 px-4 py-3 text-sm leading-6 text-app-muted italic">
            {thinking}
          </div>
        )}
      </div>
    </div>
  )
}
