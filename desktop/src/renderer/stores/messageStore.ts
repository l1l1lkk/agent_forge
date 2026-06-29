import { create } from 'zustand'
import { mockMessages } from '../api/mockData'
import { sendMessage } from '../api/client'
import type { ChatMessage } from '../api/types'

type MessageStore = {
  messagesBySession: Record<string, ChatMessage[]>
  getMessages: (sessionId: string | null) => ChatMessage[]
  setMessages: (sessionId: string, messages: ChatMessage[]) => void
  appendUserMessage: (sessionId: string, content: string) => Promise<void>
  appendMessage: (sessionId: string, msg: ChatMessage) => void
}

export const useMessageStore = create<MessageStore>((set, get) => ({
  messagesBySession: { 'session-octopus': mockMessages },

  getMessages: (sessionId) => {
    if (!sessionId) return []
    return get().messagesBySession[sessionId] ?? []
  },

  setMessages: (sessionId, messages) => {
    set({ messagesBySession: { ...get().messagesBySession, [sessionId]: messages } })
  },

  appendUserMessage: async (sessionId, content) => {
    const userMsg: ChatMessage = { id: `user-${Date.now()}`, type: 'user', content, createdAt: new Date().toISOString() }
    const existing = get().messagesBySession[sessionId] ?? []
    set({ messagesBySession: { ...get().messagesBySession, [sessionId]: [...existing, userMsg] } })

    // Send to daemon with run=true
    try {
      await sendMessage(sessionId, content)
    } catch (e) {
      console.error('Send failed:', e)
      const errMsg: ChatMessage = { id: `err-${Date.now()}`, type: 'error', title: 'Send failed', detail: String(e), createdAt: new Date().toISOString() }
      set({ messagesBySession: { ...get().messagesBySession, [sessionId]: [...get().messagesBySession[sessionId] ?? [], errMsg] } })
    }
  },

  appendMessage: (sessionId, msg) => {
    const existing = get().messagesBySession[sessionId] ?? []
    set({ messagesBySession: { ...get().messagesBySession, [sessionId]: [...existing, msg] } })
  },
}))
