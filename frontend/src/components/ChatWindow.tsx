import { useEffect, useRef, useState } from 'react'
import { useAppStore } from '../stores/appStore'
import { api, type WsEvent } from '../api/client'
import { MessageBubble } from './MessageBubble'
import { ToolCallCard } from './ToolCallCard'
import { InputBox } from './InputBox'
import { StopCircle } from 'lucide-react'

export function ChatWindow({ sessionId }: { sessionId: string }) {
  const { messages, events, isStreaming, setMessages, addMessage, addEvent, setStreaming, clearEvents } = useAppStore()
  const bottomRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Load messages
    api.getMessages(sessionId).then(r => setMessages(r.messages)).catch(console.error)
    clearEvents()
  }, [sessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, events])

  // WebSocket connection for real-time events
  const connectWS = () => {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${proto}//${location.host}/ws`)

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'subscribe_session', session_id: sessionId, after_seq: 0 }))
    }

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'event') {
        addEvent(data.event as WsEvent)
      }
    }

    ws.onerror = () => setError('WebSocket connection error')
    ws.onclose = () => setStreaming(false)

    wsRef.current = ws
  }

  const handleSend = async (content: string) => {
    setError(null)
    setStreaming(true)
    connectWS()

    try {
      await api.sendMessage(sessionId, content, true)
      // Reload messages after turn completes
      const r = await api.getMessages(sessionId)
      setMessages(r.messages)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setStreaming(false)
      wsRef.current?.close()
      clearEvents()
    }
  }

  const handleInterrupt = async () => {
    try {
      await api.interruptSession(sessionId)
      setStreaming(false)
      wsRef.current?.close()
    } catch (e: any) {
      setError(e.message)
    }
  }

  // Group events by type for display
  const textEvents = events.filter(e => e.type === 'assistant_text_delta')
  const toolCalls = events.filter(e => e.type === 'tool_call_started')
  const toolResults = events.filter(e => e.type === 'tool_result')
  const errorEvents = events.filter(e => e.type === 'error')

  return (
    <div className="flex-1 flex flex-col">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(m => (
          <MessageBubble key={m.id} message={m} />
        ))}

        {/* Streaming tool calls */}
        {toolCalls.map((tc, i) => {
          const result = toolResults.find(r => r.payload?.tool_use_id === tc.payload?.id)
          return <ToolCallCard key={i} toolEvent={tc} resultEvent={result} />
        })}

        {/* Streaming text */}
        {textEvents.length > 0 && (
          <div className="p-4 rounded-lg bg-gray-800/50">
            <p className="text-sm text-gray-300 whitespace-pre-wrap">
              {textEvents.map(e => e.payload?.text || '').join('')}
            </p>
          </div>
        )}

        {/* Error events */}
        {errorEvents.map((ev, i) => (
          <div key={i} className="p-3 rounded bg-red-900/30 border border-red-800 text-red-300 text-sm">
            {ev.payload?.error || 'Unknown error'}
          </div>
        ))}

        {/* Streaming indicator */}
        {isStreaming && (
          <div className="flex items-center gap-2 text-sm text-forge-400">
            <span>Agent is working</span>
            <span className="streaming-dot">.</span>
            <span className="streaming-dot">.</span>
            <span className="streaming-dot">.</span>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="p-3 rounded bg-red-900/30 border border-red-800 text-red-300 text-sm">
            {error}
            <button onClick={() => setError(null)} className="ml-2 text-red-400 hover:text-red-200">Dismiss</button>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-800 p-4">
        {isStreaming && (
          <div className="flex justify-end mb-2">
            <button onClick={handleInterrupt}
              className="flex items-center gap-1 px-3 py-1 text-sm rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 border border-red-800">
              <StopCircle size={14} /> Interrupt
            </button>
          </div>
        )}
        <InputBox onSend={handleSend} disabled={isStreaming} />
      </div>
    </div>
  )
}
