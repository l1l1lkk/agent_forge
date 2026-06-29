import { create } from 'zustand'
import { sendMessage } from '../api/client'
import type { ChatMessage } from '../api/types'

type MessageStore = {
  messagesBySession: Record<string, ChatMessage[]>
  runningBySession: Record<string, boolean>

  getMessages: (sessionId: string | null) => ChatMessage[]
  setMessages: (sessionId: string, messages: ChatMessage[]) => void
  appendUserMessage: (sessionId: string, content: string) => Promise<void>
  appendMessage: (sessionId: string, msg: ChatMessage) => void
  setRunning: (sessionId: string, running: boolean) => void
}

export const useMessageStore = create<MessageStore>((set, get) => ({
  messagesBySession: {},
  runningBySession: {},

  getMessages: (sessionId) => {
    if (!sessionId) return []
    return get().messagesBySession[sessionId] ?? []
  },

  setMessages: (sessionId, messages) => {
    set({
      messagesBySession: { ...get().messagesBySession, [sessionId]: messages },
    })
  },

  appendUserMessage: async (sessionId, content) => {
    const userMsg: ChatMessage = { id: `user-${Date.now()}`, type: 'user', content, createdAt: new Date().toISOString() }
    const existing = get().messagesBySession[sessionId] ?? []
    set({
      messagesBySession: { ...get().messagesBySession, [sessionId]: [...existing, userMsg] },
      runningBySession: { ...get().runningBySession, [sessionId]: true },
    })

    try {
      await sendMessage(sessionId, content)
    } catch (e) {
      const errMsg: ChatMessage = { id: `err-${Date.now()}`, type: 'error', title: 'Send failed', detail: String(e), createdAt: new Date().toISOString() }
      const cur = get().messagesBySession[sessionId] ?? []
      set({
        messagesBySession: { ...get().messagesBySession, [sessionId]: [...cur, errMsg] },
        runningBySession: { ...get().runningBySession, [sessionId]: false },
      })
    }
  },

  appendMessage: (sessionId, msg) => {
    const cur = get().messagesBySession[sessionId] ?? []

    // Merge streaming assistant text deltas into one bubble
    if (msg.type === 'assistant' && msg.content && (msg.id.startsWith('delta-') || msg.id.startsWith('evt-'))) {
      const last = cur[cur.length - 1]
      if (last && last.type === 'assistant' && last.id.startsWith('stream-')) {
        // Append to existing streaming bubble
        last.content += msg.content
        set({ messagesBySession: { ...get().messagesBySession, [sessionId]: [...cur] } })
        return
      }
      // New streaming bubble
      msg.id = `stream-${sessionId}-${Date.now()}`
    }

    // Update running state from status events
    if (msg.type === 'status') {
      const label = (msg as any).label || ''
      if (label === 'DONE') {
        set({ runningBySession: { ...get().runningBySession, [sessionId]: false } })
      }
    }

    set({ messagesBySession: { ...get().messagesBySession, [sessionId]: [...cur, msg] } })
  },

  setRunning: (sessionId, running) => {
    set({ runningBySession: { ...get().runningBySession, [sessionId]: running } })
  },
}))
