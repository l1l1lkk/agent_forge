import { Plus } from 'lucide-react'
import { mockConnectors } from '../../api/mockData'
import { SidebarSection } from '../layout/SidebarSection'
import { useAppStore } from '../../stores/appStore'

export function ConnectorsSection() {
  const setView = useAppStore((s) => s.setView)

  return (
    <SidebarSection title="Connectors" action={<button className="rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text" onClick={() => setView('connectors')}><Plus size={14} /></button>}>
      {mockConnectors.map((c) => (
        <button key={c.id} className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-app-hover" onClick={() => setView('connectors')}>
          <span className="rounded bg-app-badge px-1.5 py-0.5 text-[10px] font-bold uppercase text-app-accent">{c.label}</span>
          <span className="min-w-0 truncate text-app-secondary">{c.account}</span>
        </button>
      ))}
    </SidebarSection>
  )
}
