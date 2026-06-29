import { useState } from 'react'
import type { WsEvent } from '../api/client'
import { ChevronDown, ChevronRight, Terminal, AlertCircle } from 'lucide-react'

export function ToolCallCard({ toolEvent, resultEvent }: {
  toolEvent: WsEvent
  resultEvent?: WsEvent
}) {
  const [expanded, setExpanded] = useState(false)
  const tool = toolEvent.payload?.tool || 'unknown'
  const input = toolEvent.payload?.input || {}
  const cmd = input.command || JSON.stringify(input).slice(0, 200)
  const result = resultEvent?.payload?.content || ''
  const isError = resultEvent?.payload?.is_error

  return (
    <div className="border border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 p-3 bg-gray-800/50 hover:bg-gray-800 text-left"
      >
        {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <Terminal size={16} className="text-yellow-400" />
        <span className="text-sm font-medium text-yellow-300">{tool}</span>
        <span className="text-xs text-gray-500 truncate flex-1">{cmd}</span>
        {resultEvent && (
          isError
            ? <AlertCircle size={14} className="text-red-400" />
            : <span className="text-xs text-green-400">done</span>
        )}
      </button>
      {expanded && (
        <div className="p-3 space-y-2 bg-gray-900/50 text-xs">
          <div>
            <div className="text-gray-500 mb-1">Input:</div>
            <pre className="text-gray-300">{cmd}</pre>
          </div>
          {result && (
            <div>
              <div className="text-gray-500 mb-1">Result:</div>
              <pre className={`${isError ? 'text-red-300' : 'text-green-300'} max-h-48 overflow-y-auto`}>
                {typeof result === 'string' ? result.slice(0, 2000) : JSON.stringify(result, null, 2).slice(0, 2000)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
