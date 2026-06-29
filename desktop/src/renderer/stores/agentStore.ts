import { create } from 'zustand'
import { mockAgents } from '../api/mockData'
import type { Agent } from '../api/types'

type AgentStore = {
  agents: Agent[]
  expandedAgentIds: string[]
  selectedAgentId: string | null
  toggleAgent: (agentId: string) => void
  selectAgent: (agentId: string) => void
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  agents: mockAgents,
  expandedAgentIds: ['agent-octo', 'agent-vera', 'agent-charlie', 'agent-weber'],
  selectedAgentId: 'agent-octo',
  toggleAgent: (agentId) => {
    const current = get().expandedAgentIds
    set({ expandedAgentIds: current.includes(agentId) ? current.filter((id) => id !== agentId) : [...current, agentId] })
  },
  selectAgent: (selectedAgentId) => set({ selectedAgentId }),
}))
