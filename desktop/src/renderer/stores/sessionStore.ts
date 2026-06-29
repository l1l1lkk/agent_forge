import { create } from 'zustand'
import { fetchMessages } from '../api/client'
import { connectWS, disconnectWS } from '../api/wsClient'
import { useMessageStore } from './messageStore'

type SessionStore = {
  selectedSessionId: string | null
  selectTick: number
  selectSession: (sessionId: string) => Promise<void>
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  selectedSessionId: null,
  selectTick: 0,

  selectSession: async (sessionId) => {
    // Disconnect previous WS
    disconnectWS()

    // Always increment tick to force UI refresh even for same session
    set({ selectedSessionId: sessionId, selectTick: get().selectTick + 1 })

    // Load messages from REST
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
