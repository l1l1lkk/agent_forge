import { create } from 'zustand'
import { mockMessages } from '../api/mockData'
import type { ChatMessage } from '../api/types'

type MessageStore = {
  messagesBySession: Record<string, ChatMessage[]>
  getMessages: (sessionId: string | null) => ChatMessage[]
  appendUserMessage: (sessionId: string, content: string) => void
}

export const useMessageStore = create<MessageStore>((set, get) => ({
  messagesBySession: { 'session-octopus': mockMessages },
  getMessages: (sessionId) => {
    if (!sessionId) return []
    return get().messagesBySession[sessionId] ?? []
  },
  appendUserMessage: (sessionId, content) => {
    const message: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    const existing = get().messagesBySession[sessionId] ?? []
    set({ messagesBySession: { ...get().messagesBySession, [sessionId]: [...existing, message] } })
  },
}))
