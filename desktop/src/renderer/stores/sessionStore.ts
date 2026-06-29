import { create } from 'zustand'

type SessionStore = {
  selectedSessionId: string | null
  selectSession: (sessionId: string) => void
}

export const useSessionStore = create<SessionStore>((set) => ({
  selectedSessionId: 'session-octopus',
  selectSession: (selectedSessionId) => set({ selectedSessionId }),
}))
