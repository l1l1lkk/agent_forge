import { create } from 'zustand'
import { fetchMessages } from '../api/client'
import { connectWS, disconnectWS } from '../api/wsClient'
import { useMessageStore } from './messageStore'

type SessionStore = {
  selectedSessionId: string | null
  selectSession: (sessionId: string) => Promise<void>
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  selectedSessionId: null,

  selectSession: async (sessionId) => {
    const prev = get().selectedSessionId
    set({ selectedSessionId: sessionId })

    // Disconnect previous WS
    if (prev) disconnectWS()

    // Load messages from REST
    try {
      const messages = await fetchMessages(sessionId)
      if (messages.length > 0) {
        useMessageStore.getState().setMessages(sessionId, messages)
      }
    } catch { /* keep mock */ }

    // Connect WebSocket for live events
    connectWS(sessionId, (msg) => {
      useMessageStore.getState().appendMessage(sessionId, msg)
    })
  },
}))
