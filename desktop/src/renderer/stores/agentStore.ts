import { create } from 'zustand'
import { mockAgents } from '../api/mockData'
import { fetchAgents, fetchSessions } from '../api/client'
import type { Agent } from '../api/types'

type AgentStore = {
  agents: Agent[]
  expandedAgentIds: string[]
  selectedAgentId: string | null
  loading: boolean
  loadAgents: () => Promise<void>
  toggleAgent: (agentId: string) => void
  selectAgent: (agentId: string) => void
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  agents: mockAgents,
  expandedAgentIds: mockAgents.map(a => a.id),
  selectedAgentId: null,
  loading: false,

  loadAgents: async () => {
    set({ loading: true })
    try {
      const agents = await fetchAgents()
      const sessions = await fetchSessions()
      // Group sessions by agent_id
      const merged = agents.map(a => ({
        ...a,
        sessions: sessions.filter(s => s.agentId === a.id),
      }))
      set({
        agents: merged.length > 0 ? merged : mockAgents,
        expandedAgentIds: merged.length > 0 ? merged.map(a => a.id) : get().expandedAgentIds,
        selectedAgentId: get().selectedAgentId || (merged[0]?.id ?? null),
      })
    } catch {
      // Keep mock data on error
    } finally {
      set({ loading: false })
    }
  },

  toggleAgent: (agentId) => {
    const cur = get().expandedAgentIds
    set({ expandedAgentIds: cur.includes(agentId) ? cur.filter(id => id !== agentId) : [...cur, agentId] })
  },
  selectAgent: (selectedAgentId) => set({ selectedAgentId }),
}))
