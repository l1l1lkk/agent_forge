import { create } from 'zustand'
import { useAppStore } from './appStore'
import { useAgentStore } from './agentStore'
import { useSessionStore } from './sessionStore'
import { fetchSessions } from '../api/client'

type OpenChatTarget = {
  agentId?: string
  sessionId?: string
  runner?: string
  createIfMissing?: boolean
}

type NavigationStore = {
  openChat: (target: OpenChatTarget) => Promise<void>
}

export const useNavigationStore = create<NavigationStore>(() => ({
  openChat: async (target) => {
    const app = useAppStore.getState()
    const agentStore = useAgentStore.getState()
    const sessionStore = useSessionStore.getState()

    // 1. Always switch to workspace
    app.setView('workspace')

    // Load latest data
    await agentStore.loadAgents()

    // 2. Find or use target agent
    let agentId = target.agentId
    if (!agentId && target.runner) {
      const agents = agentStore.agents
      const found = agents.find((a: any) =>
        a.name?.toLowerCase().includes(target.runner!)
      )
      agentId = found?.id ?? null
    }
    if (!agentId) {
      agentId = agentStore.selectedAgentId ?? agentStore.agents[0]?.id ?? null
    }
    if (!agentId) {
      app.setConnectionStatus('disconnected')
      return
    }

    // 3. Expand and select the agent
    agentStore.expandAgent(agentId)
    agentStore.selectAgent(agentId)

    // 4. Find best session for this agent
    let sessionId = target.sessionId
    if (!sessionId) {
      const agent = agentStore.agents.find((a: any) => a.id === agentId)
      sessionId = agent?.sessions?.[0]?.id ?? null
    }
    if (!sessionId && target.createIfMissing) {
      // Create session via API
      try {
        const api = (await import('../api/client'))
        const projData = await api.fetchProjects()
        const projId = projData[0]?.id
        if (projId) {
          const ses = await api.createSession(projId, agentId, `${target.runner || 'new'} chat`)
          sessionId = ses.id
          await agentStore.loadAgents()
        }
      } catch {}
    }
    if (!sessionId) return

    // 5. Always select session (even if same — forces reload)
    await sessionStore.selectSession(sessionId)
  },
}))
