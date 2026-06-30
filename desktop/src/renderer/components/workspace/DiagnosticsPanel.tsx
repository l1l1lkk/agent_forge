import { useEffect, useState } from 'react'
import { Activity, Cpu, Server, Wifi, Clock, RefreshCw } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import { fetchDiagnostics } from '../../api/client'

interface DiagnosticsData {
  health: { status: string; version: string }
  db: { projects: number; agents: number; running_sessions: number; running_tasks: number }
  runners: Array<{ name: string; registered: boolean; available: boolean; path: string | null }>
  running_sessions: Array<{ id: string; title: string; agent_id: string; runner: string; created_at: string }>
  running_tasks: Array<{ id: string; name: string; session_id: string | null; created_at: string }>
  features: Record<string, boolean>
}

export function DiagnosticsPanel() {
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

  // Auto-refresh every 15s
  useEffect(() => {
    const interval = setInterval(load, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <main className="flex min-w-0 flex-1 flex-col bg-app-bg">
      <div className="flex h-12 items-center justify-between border-b border-app-border px-5">
        <h2 className="text-sm font-semibold text-app-text">Diagnostics</h2>
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
          <div className="text-sm text-app-muted flex items-center gap-2">
            <RefreshCw size={14} className="animate-spin" />
            Loading diagnostics...
          </div>
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
            {/* Daemon Health */}
            <div className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-3">
                <Server size={16} className="text-app-accent" />
                <div className="text-sm font-semibold text-app-text">Daemon Status</div>
              </div>
              <div className="grid grid-cols-2 gap-y-2 text-sm">
                <div className="text-app-muted">Health</div>
                <div className="flex items-center gap-1.5 text-app-text">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  {data.health.status} / v{data.health.version}
                </div>
                <div className="text-app-muted">Daemon</div>
                <div className="text-app-text">{daemonLabel} / Port 8765</div>
                <div className="text-app-muted">WebSocket</div>
                <div className="flex items-center gap-1.5 text-app-text">
                  <Wifi size={12} className="text-green-400" />
                  Connected
                </div>
              </div>
            </div>

            {/* Runners */}
            <div className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-3">
                <Cpu size={16} className="text-app-accent" />
                <div className="text-sm font-semibold text-app-text">Runners ({data.runners.length})</div>
              </div>
              <div className="space-y-1.5">
                {data.runners.map((r) => (
                  <div key={r.name} className="flex items-center justify-between rounded-lg border border-app-border/60 bg-app-bg px-3 py-2">
                    <span className="text-sm text-app-text font-medium">{r.name}</span>
                    <div className="flex items-center gap-2">
                      {r.path && <span className="text-xs text-app-muted font-mono">{r.path}</span>}
                      <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                        r.available ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                      }`}>
                        {r.available ? 'AVAIL' : r.registered ? 'NO CLI' : 'N/A'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* DB Overview */}
            <div className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-3">
                <Activity size={16} className="text-app-accent" />
                <div className="text-sm font-semibold text-app-text">Database</div>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'Projects', value: data.db.projects },
                  { label: 'Agents', value: data.db.agents },
                  { label: 'Running Sessions', value: data.db.running_sessions },
                  { label: 'Running Tasks', value: data.db.running_tasks },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-lg border border-app-border/60 bg-app-bg p-3 text-center">
                    <div className="text-xl font-bold text-app-text font-mono">{stat.value}</div>
                    <div className="text-[10px] text-app-muted mt-1 uppercase tracking-wide">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Running Sessions */}
            <div className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-3">
                <Clock size={16} className="text-app-accent" />
                <div className="text-sm font-semibold text-app-text">
                  Running Sessions ({data.running_sessions.length})
                </div>
              </div>
              {data.running_sessions.length === 0 ? (
                <div className="text-xs text-app-muted">No running sessions</div>
              ) : (
                <div className="space-y-1.5">
                  {data.running_sessions.map((s) => (
                    <div key={s.id} className="rounded-lg border border-app-border/60 bg-app-bg px-3 py-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-app-text font-medium">{s.title || s.id.slice(0, 8)}</span>
                        <span className="rounded bg-green-900/30 px-1.5 py-0.5 text-green-400 font-bold uppercase">Running</span>
                      </div>
                      <div className="mt-1 text-app-muted">
                        Runner: {s.runner} / Agent: {s.agent_id?.slice(0, 8) || '-'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </main>
  )
}
