import { Plus } from 'lucide-react'
import { mockConnectors } from '../../api/mockData'
import { SidebarSection } from '../layout/SidebarSection'

export function ConnectorsSection() {
  return (
    <SidebarSection title="Connectors" action={<button className="rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text"><Plus size={14} /></button>}>
      {mockConnectors.map((c) => (
        <button key={c.id} className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-app-hover">
          <span className="rounded bg-app-badge px-1.5 py-0.5 text-[10px] font-bold uppercase text-app-accent">{c.label}</span>
          <span className="min-w-0 truncate text-app-secondary">{c.account}</span>
        </button>
      ))}
    </SidebarSection>
  )
}
