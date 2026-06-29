import { Plus } from 'lucide-react'
import { mockHarnesses } from '../../api/mockData'
import { SidebarSection } from '../layout/SidebarSection'

export function HarnessSection() {
  return (
    <SidebarSection title="Harness" action={<button className="rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text"><Plus size={14} /></button>}>
      {mockHarnesses.map((h) => (
        <button key={h.id} className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-app-hover">
          <span className="rounded bg-app-badge px-1.5 py-0.5 text-[10px] font-bold uppercase text-blue-300">{h.type}</span>
          <span className="min-w-0 flex-1 truncate text-app-secondary">{h.label}</span>
          {h.authType && <span className="text-[10px] font-semibold uppercase text-app-muted">{h.authType}</span>}
        </button>
      ))}
    </SidebarSection>
  )
}
