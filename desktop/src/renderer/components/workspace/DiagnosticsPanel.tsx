import { useAppStore } from '../../stores/appStore'

export function DiagnosticsPanel() {
  const setView = useAppStore((s) => s.setView)
  return (
    <main className="flex min-w-0 flex-1 flex-col bg-app-bg">
      <div className="flex h-12 items-center justify-between border-b border-app-border px-5">
        <h2 className="text-sm font-semibold text-app-text">Diagnostics</h2>
        <button className="rounded-lg border border-app-border px-3 py-1.5 text-sm text-app-secondary hover:bg-app-hover hover:text-app-text" onClick={() => setView('workspace')}>
          Back to Workspace
        </button>
      </div>
      <div className="p-5">
        <div className="rounded-xl border border-app-border bg-app-panel p-4">
          <div className="text-sm font-semibold text-app-text">Daemon Status</div>
          <div className="mt-2 text-sm text-app-muted">Health: OK · Version: 0.0.9rc1 · Port: 8765</div>
        </div>
      </div>
    </main>
  )
}
