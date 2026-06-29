import { MessageCircle, Plus } from 'lucide-react'
import { SidebarSection } from '../layout/SidebarSection'
import { useRunnerStore } from '../../stores/runnerStore'
import { useNavigationStore } from '../../stores/navigationStore'

export function HarnessSection() {
  const runners = useRunnerStore((s) => s.runners)
  const openChat = useNavigationStore((s) => s.openChat)

  return (
    <SidebarSection
      title="Harness"
      action={<button className="rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text"><Plus size={14} /></button>}
    >
      {runners.length === 0 && (
        <div className="px-2 py-1 text-xs text-app-muted">No runners found</div>
      )}
      {runners.map((h) => (
        <div key={h.id} className="group flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-app-hover">
          <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${h.status === 'ready' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
            {h.type}
          </span>
          <span className="min-w-0 flex-1 truncate text-app-secondary">{h.label}</span>
          {h.authType && <span className="text-[10px] font-semibold uppercase text-app-muted">{h.authType}</span>}
          <button
            type="button"
            className="rounded-md p-1 text-app-muted opacity-0 group-hover:opacity-100 hover:bg-app-selected hover:text-app-text"
            title={`Open ${h.type} chat`}
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); openChat({ runner: h.type, createIfMissing: true }) }}
          >
            <MessageCircle size={14} />
          </button>
        </div>
      ))}
    </SidebarSection>
  )
}
