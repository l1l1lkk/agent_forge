import { useEffect, useState } from 'react'
import { Server, Cpu, HardDrive, Activity, RefreshCw } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import { fetchDiagnostics } from '../../api/client'

interface DiagnosticsData {
  health: { status: string; version: string }
  db: { projects: number; agents: number; running_sessions: number; running_tasks: number }
  runners: Array<{ name: string; registered: boolean; available: boolean; path: string | null }>
  features: Record<string, boolean>
}

export function SettingsPanel() {
  const setView = useAppStore((s) => s.setView)
  const daemonLabel = useAppStore((s) => s.daemonLabel)
  const [data, setData] = useState<DiagnosticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const d = await fetchDiagnostics()
      setData(d)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <main className="flex min-w-0 flex-1 flex-col bg-app-bg">
      <div className="flex h-12 items-center justify-between border-b border-app-border px-5">
        <h2 className="text-sm font-semibold text-app-text">Settings</h2>
        <div className="flex items-center gap-2">
          <button
            className="rounded-lg p-2 text-app-muted hover:bg-app-hover hover:text-app-text"
            onClick={load}
            title="Refresh"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          </button>
          <button
            className="rounded-lg border border-app-border px-3 py-1.5 text-sm text-app-secondary hover:bg-app-hover hover:text-app-text"
            onClick={() => setView('workspace')}
          >
            Back to Workspace
          </button>
        </div>
      </div>

      <div className="overflow-y-auto p-5 space-y-4">
        {loading && !data && (
          <div className="text-sm text-app-muted">Loading settings...</div>
        )}
        {error && (
          <div className="rounded-xl border border-red-800 bg-red-900/20 p-4">
            <div className="text-sm font-semibold text-red-400">Connection Error</div>
            <div className="mt-1 text-sm text-red-300">{error}</div>
            <button
              className="mt-3 rounded-lg border border-red-700 px-3 py-1.5 text-sm text-red-300 hover:bg-red-900/40"
              onClick={load}
            >
              Retry
            </button>
          </div>
        )}

        {data && (
          <>
            {/* Server Info */}
            <section className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-3">
                <Server size={16} className="text-app-accent" />
                <h3 className="text-sm font-semibold text-app-text">Server</h3>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-app-muted text-xs mb-0.5">Daemon</div>
                  <div className="text-app-text">{daemonLabel}</div>
                </div>
                <div>
                  <div className="text-app-muted text-xs mb-0.5">Version</div>
                  <div className="text-app-text font-mono">{data.health.version}</div>
                </div>
                <div>
                  <div className="text-app-muted text-xs mb-0.5">Health</div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-green-400">{data.health.status}</span>
                  </div>
                </div>
                <div>
                  <div className="text-app-muted text-xs mb-0.5">Port</div>
                  <div className="text-app-text font-mono">8765</div>
                </div>
              </div>
            </section>

            {/* Database Stats */}
            <section className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-3">
                <HardDrive size={16} className="text-app-accent" />
                <h3 className="text-sm font-semibold text-app-text">Database</h3>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-app-muted text-xs mb-0.5">Projects</div>
                  <div className="text-app-text font-mono">{data.db.projects}</div>
                </div>
                <div>
                  <div className="text-app-muted text-xs mb-0.5">Agents</div>
                  <div className="text-app-text font-mono">{data.db.agents}</div>
                </div>
                <div>
                  <div className="text-app-muted text-xs mb-0.5">Running Sessions</div>
                  <div className="text-app-text font-mono">{data.db.running_sessions}</div>
                </div>
                <div>
                  <div className="text-app-muted text-xs mb-0.5">Running Tasks</div>
                  <div className="text-app-text font-mono">{data.db.running_tasks}</div>
                </div>
              </div>
            </section>

            {/* Runners */}
            <section className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-3">
                <Cpu size={16} className="text-app-accent" />
                <h3 className="text-sm font-semibold text-app-text">Runners</h3>
              </div>
              <div className="space-y-2">
                {data.runners.map((r) => (
                  <div key={r.name} className="flex items-center justify-between rounded-lg border border-app-border/60 bg-app-bg px-3 py-2">
                    <div className="flex items-center gap-2">
                      <span className={`h-2 w-2 rounded-full ${r.available ? 'bg-green-500' : 'bg-red-500'}`} />
                      <span className="text-sm text-app-text font-medium">{r.name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`rounded px-1.5 py-0.5 font-semibold uppercase ${r.available ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                        {r.available ? 'Ready' : 'Missing'}
                      </span>
                      {r.path && <span className="text-app-muted font-mono truncate max-w-[200px]">{r.path}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Features */}
            <section className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-3">
                <Activity size={16} className="text-app-accent" />
                <h3 className="text-sm font-semibold text-app-text">Features</h3>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(data.features).map(([key, enabled]) => (
                  <div key={key} className="flex items-center justify-between rounded-lg border border-app-border/60 bg-app-bg px-3 py-2">
                    <span className="text-sm text-app-secondary capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className={`h-2 w-2 rounded-full ${enabled ? 'bg-green-500' : 'bg-red-500'}`} />
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  )
}
