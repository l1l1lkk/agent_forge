/**
 * WebSocket client for /api/ws — subscribes to session events.
 */
import { adaptEvent } from './eventAdapter'
import type { ChatMessage } from './types'

type EventHandler = (msgs: ChatMessage[]) => void

let ws: WebSocket | null = null
let currentSessionId: string | null = null
let handler: EventHandler | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let deltaBuffer: { text: string; id: string } | null = null

export function connectWS(sessionId: string, onMessages: EventHandler): void {
  if (currentSessionId === sessionId && ws?.readyState === WebSocket.OPEN) return
  disconnectWS()
  currentSessionId = sessionId
  handler = onMessages
  deltaBuffer = null
  _connect()
}

function _connect(): void {
  if (!currentSessionId) return
  const wsUrl = `ws://127.0.0.1:8765/api/ws`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    ws?.send(JSON.stringify({ type: 'subscribe_session', session_id: currentSessionId, after_seq: 0 }))
  }

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'event') {
        const result = adaptEvent(data.event)
        if (!result) return
        const msgs = Array.isArray(result) ? result : [result]
        if (msgs.length > 0) handler?.(msgs)
      }
    } catch {}
  }

  ws.onerror = () => {}
  ws.onclose = () => {
    ws = null
    // Auto-reconnect after 2s
    if (currentSessionId) {
      reconnectTimer = setTimeout(_connect, 2000)
    }
  }
}

export function disconnectWS(): void {
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (ws) { ws.onclose = null; ws.close(); ws = null }
  currentSessionId = null
  handler = null
  deltaBuffer = null
}
