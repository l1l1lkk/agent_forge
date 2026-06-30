import { useState } from 'react'
import { ChevronDown, ChevronRight, Plus } from 'lucide-react'
import type { Agent } from '../../api/types'
import { useAgentStore } from '../../stores/agentStore'
import { SessionTreeItem } from './SessionTreeItem'
import { CreateSessionModal } from './CreateSessionModal'

export function AgentTreeItem({ agent }: { agent: Agent }) {
  const expandedAgentIds = useAgentStore((s) => s.expandedAgentIds)
  const selectedAgentId = useAgentStore((s) => s.selectedAgentId)
  const toggleAgent = useAgentStore((s) => s.toggleAgent)
  const selectAgent = useAgentStore((s) => s.selectAgent)
  const isExpanded = expandedAgentIds.includes(agent.id)
  const isSelected = selectedAgentId === agent.id
  const [showCreate, setShowCreate] = useState(false)

  return (
    <div>
      <div
        className={`group flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-sm ${isSelected ? 'bg-app-selected text-app-text' : 'text-app-text hover:bg-app-hover'}`}
        onClick={() => selectAgent(agent.id)}
      >
        <button className="text-app-muted" onClick={(e) => { e.stopPropagation(); toggleAgent(agent.id) }}>
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        <span className="text-base">{agent.avatar}</span>
        <span className="min-w-0 flex-1 truncate font-medium">{agent.name}</span>
        <button className="opacity-40 hover:opacity-100 text-app-muted" onClick={(e) => { e.stopPropagation(); setShowCreate(true) }}>
          <Plus size={14} />
        </button>
      </div>
      {isExpanded && (
        <div className="ml-8 mt-1 space-y-1 border-l border-app-border pl-3">
          {agent.sessions.map((s) => <SessionTreeItem key={s.id} session={s} />)}
        </div>
      )}
      <CreateSessionModal agentId={agent.id} agentName={agent.name} open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}
