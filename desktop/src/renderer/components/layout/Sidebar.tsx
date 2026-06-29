import { AgentsSection } from '../sidebar/AgentsSection'
import { SchedulesSection } from '../sidebar/SchedulesSection'
import { ConnectorsSection } from '../sidebar/ConnectorsSection'
import { HarnessSection } from '../sidebar/HarnessSection'

export function Sidebar() {
  return (
    <aside className="flex w-[280px] shrink-0 flex-col border-r border-app-border bg-app-sidebar">
      <div className="flex-1 overflow-y-auto px-3 py-3">
        <AgentsSection />
        <div className="mt-5 space-y-5">
          <SchedulesSection />
          <ConnectorsSection />
          <HarnessSection />
        </div>
      </div>
      <div className="border-t border-app-border px-3 py-3">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-app-accent text-sm font-bold text-white">A</div>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-app-text">Agent Forge</div>
            <div className="truncate text-xs text-app-muted">local workspace</div>
          </div>
        </div>
      </div>
    </aside>
  )
}
