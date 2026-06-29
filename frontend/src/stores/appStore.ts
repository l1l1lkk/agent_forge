import { create } from 'zustand'
import type { Project, Agent, Session, Message, WsEvent } from '../api/client'

interface AppState {
  projects: Project[]
  agents: Agent[]
  sessions: Session[]
  currentSession: Session | null
  messages: Message[]
  events: WsEvent[]
  isStreaming: boolean

  setProjects: (p: Project[]) => void
  setAgents: (a: Agent[]) => void
  setSessions: (s: Session[]) => void
  setCurrentSession: (s: Session | null) => void
  setMessages: (m: Message[]) => void
  addMessage: (m: Message) => void
  addEvent: (e: WsEvent) => void
  setStreaming: (v: boolean) => void
  clearEvents: () => void
}

export const useAppStore = create<AppState>((set) => ({
  projects: [],
  agents: [],
  sessions: [],
  currentSession: null,
  messages: [],
  events: [],
  isStreaming: false,

  setProjects: (p) => set({ projects: p }),
  setAgents: (a) => set({ agents: a }),
  setSessions: (s) => set({ sessions: s }),
  setCurrentSession: (s) => set({ currentSession: s }),
  setMessages: (m) => set({ messages: m }),
  addMessage: (m) => set((state) => ({ messages: [...state.messages, m] })),
  addEvent: (e) => set((state) => ({ events: [...state.events, e] })),
  setStreaming: (v) => set({ isStreaming: v }),
  clearEvents: () => set({ events: [] }),
}))
