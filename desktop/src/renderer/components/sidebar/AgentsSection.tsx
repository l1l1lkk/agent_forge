import { useState } from 'react'
import { Plus } from 'lucide-react'
import { SidebarSection } from '../layout/SidebarSection'
import { AgentTreeItem } from './AgentTreeItem'
import { useAgentStore } from '../../stores/agentStore'
import { AgentSettingsDialog } from './AgentSettingsDialog'

export function AgentsSection() {
  const agents = useAgentStore((s) => s.agents)
  const [settingsOpen, setSettingsOpen] = useState(false)
  return (
    <>
      <SidebarSection
        title="Agents"
        action={
          <button
            className="rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text"
            onClick={() => setSettingsOpen(true)}
            title="Agent settings"
          >
            <Plus size={14} />
          </button>
        }
      >
        {agents.map((agent) => <AgentTreeItem key={agent.id} agent={agent} />)}
      </SidebarSection>
      <AgentSettingsDialog open={settingsOpen} initialAgentId={null} onClose={() => setSettingsOpen(false)} />
    </>
  )
}
