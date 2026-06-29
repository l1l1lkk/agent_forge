import { Plus } from 'lucide-react'
import { SidebarSection } from '../layout/SidebarSection'
import { AgentTreeItem } from './AgentTreeItem'
import { useAgentStore } from '../../stores/agentStore'

export function AgentsSection() {
  const agents = useAgentStore((s) => s.agents)
  return (
    <SidebarSection
      title="Agents"
      action={<button className="rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text"><Plus size={14} /></button>}
    >
      {agents.map((agent) => <AgentTreeItem key={agent.id} agent={agent} />)}
    </SidebarSection>
  )
}
