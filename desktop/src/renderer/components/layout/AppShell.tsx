import { TopBar } from './TopBar'
import { Sidebar } from './Sidebar'
import { MainWorkspace } from './MainWorkspace'
import { DiagnosticsPanel } from '../workspace/DiagnosticsPanel'
import { useAppStore } from '../../stores/appStore'

export function AppShell() {
  const view = useAppStore((s) => s.view)
  return (
    <div className="h-screen w-screen overflow-hidden bg-app-bg text-app-text">
      <TopBar />
      <div className="flex h-[calc(100vh-44px)]">
        <Sidebar />
        {view === 'workspace' && <MainWorkspace />}
        {view === 'diagnostics' && <DiagnosticsPanel />}
        {view === 'settings' && <DiagnosticsPanel />}
        {view === 'schedules' && <Placeholder title="Schedules" />}
        {view === 'connectors' && <Placeholder title="Connectors" />}
      </div>
    </div>
  )
}

function Placeholder({ title }: { title: string }) {
  return (
    <main className="flex flex-1 items-center justify-center bg-app-bg">
      <div className="rounded-xl border border-app-border bg-app-panel px-6 py-5 text-app-muted">{title} coming soon</div>
    </main>
  )
}
