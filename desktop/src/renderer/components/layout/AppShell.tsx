import { TopBar } from './TopBar'
import { Sidebar } from './Sidebar'
import { MainWorkspace } from './MainWorkspace'
import { SettingsPanel } from '../workspace/SettingsPanel'
import { DiagnosticsPanel } from '../workspace/DiagnosticsPanel'
import { SchedulesPanel } from '../workspace/SchedulesPanel'
import { ConnectorsPanel } from '../workspace/ConnectorsPanel'
import { GitWorkspacePanel } from '../workspace/GitWorkspacePanel'
import { useAppStore } from '../../stores/appStore'

export function AppShell() {
  const view = useAppStore((s) => s.view)
  return (
    <div className="h-screen w-screen overflow-hidden bg-app-bg text-app-text">
      <TopBar />
      <div className="flex h-[calc(100vh-44px)]">
        <Sidebar />
        {view === 'workspace' && <MainWorkspace />}
        {view === 'settings' && <SettingsPanel />}
        {view === 'diagnostics' && <DiagnosticsPanel />}
        {view === 'schedules' && <SchedulesPanel />}
        {view === 'connectors' && <ConnectorsPanel />}
        {view === 'git' && <GitWorkspacePanel />}
      </div>
    </div>
  )
}
