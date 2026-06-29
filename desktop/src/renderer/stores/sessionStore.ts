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

    // Load messages from REST (always set, even if empty, to clear old session)
    try {
      const messages = await fetchMessages(sessionId)
      useMessageStore.getState().setMessages(sessionId, messages)
    } catch {
      useMessageStore.getState().setMessages(sessionId, [])
    }

    // Connect WebSocket for live events
    connectWS(sessionId, (msgs) => {
      for (const msg of msgs) {
        useMessageStore.getState().appendMessage(sessionId, msg)
      }
    })
  },
}))
