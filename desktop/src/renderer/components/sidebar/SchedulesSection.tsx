import { Clock, Plus } from 'lucide-react'
import { SidebarSection } from '../layout/SidebarSection'
import { useAppStore } from '../../stores/appStore'

export function SchedulesSection() {
  const setView = useAppStore((s) => s.setView)
  return (
    <SidebarSection title="Schedules" count={5} action={<button className="rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text"><Plus size={14} /></button>}>
      <button className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-sm text-app-secondary hover:bg-app-hover hover:text-app-text" onClick={() => setView('schedules')}>
        <span>Scheduled runs</span><Clock size={14} />
      </button>
    </SidebarSection>
  )
}
