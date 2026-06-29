import { create } from 'zustand'
import { fetchAgents, fetchSessions } from '../api/client'
import type { Agent } from '../api/types'

type AgentStore = {
  agents: Agent[]
  expandedAgentIds: string[]
  selectedAgentId: string | null
  loading: boolean
  error: string | null
  demoMode: boolean
  loadAgents: () => Promise<void>
  enableDemoMode: () => void
  toggleAgent: (agentId: string) => void
  selectAgent: (agentId: string) => void
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  agents: [],
  expandedAgentIds: [],
  selectedAgentId: null,
  loading: false,
  error: null,
  demoMode: false,

  loadAgents: async () => {
    if (get().demoMode) return
    set({ loading: true, error: null })
    try {
      const agents = await fetchAgents()
      const sessions = await fetchSessions()
      const merged = agents.map(a => ({
        ...a,
        sessions: sessions.filter(s => s.agentId === a.id),
      }))
      set({
        agents: merged,
        expandedAgentIds: merged.map(a => a.id),
        selectedAgentId: get().selectedAgentId || (merged[0]?.id ?? null),
      })
    } catch (e) {
      set({ error: String(e), agents: [] })
    } finally {
      set({ loading: false })
    }
  },

  enableDemoMode: () => {
    const { mockAgents } = require('../api/mockData')
    set({
      demoMode: true,
      agents: mockAgents,
      expandedAgentIds: mockAgents.map((a: Agent) => a.id),
      selectedAgentId: mockAgents[0]?.id ?? null,
      error: null,
    })
  },

  toggleAgent: (agentId) => {
    const cur = get().expandedAgentIds
    set({ expandedAgentIds: cur.includes(agentId) ? cur.filter(id => id !== agentId) : [...cur, agentId] })
  },
  selectAgent: (selectedAgentId) => set({ selectedAgentId }),
}))
