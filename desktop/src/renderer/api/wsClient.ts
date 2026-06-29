/**
 * WebSocket client — subscribes to session events and maps them to UI message cards.
 */
import type { ChatMessage } from './types'

type EventHandler = (msg: ChatMessage) => void

let ws: WebSocket | null = null
let currentSessionId: string | null = null
let handler: EventHandler | null = null

export function connectWS(sessionId: string, onMessage: EventHandler): void {
  if (currentSessionId === sessionId && ws?.readyState === WebSocket.OPEN) return

  // Close previous
  disconnectWS()

  currentSessionId = sessionId
  handler = onMessage

  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${proto}//127.0.0.1:8765/ws`

  ws = new WebSocket(url)

  ws.onopen = () => {
    ws?.send(JSON.stringify({ type: 'subscribe_session', session_id: sessionId, after_seq: 0 }))
  }

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'event') {
        const msg = adaptEvent(data.event)
        if (msg) handler?.(msg)
      }
    } catch {}
  }

  ws.onerror = () => {}
  ws.onclose = () => {}
}

export function disconnectWS(): void {
  if (ws) {
    ws.close()
    ws = null
  }
  currentSessionId = null
  handler = null
}
