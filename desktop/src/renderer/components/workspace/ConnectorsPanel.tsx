import { useEffect, useState } from 'react'
import { Plug, ExternalLink, RefreshCw } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import { fetchConnectors } from '../../api/client'
import type { Connector } from '../../api/types'

export function ConnectorsPanel() {
  const setView = useAppStore((s) => s.setView)
  const [connectors, setConnectors] = useState<Connector[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setConnectors(await fetchConnectors())
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
        <h2 className="text-sm font-semibold text-app-text">Connectors</h2>
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

      <div className="overflow-y-auto p-5 space-y-3">
        {loading && !connectors.length && (
          <div className="text-sm text-app-muted">Loading connectors...</div>
        )}
        {error && (
          <div className="rounded-xl border border-red-800 bg-red-900/20 p-4">
            <div className="text-sm text-red-400">{error}</div>
          </div>
        )}
        {!loading && connectors.length === 0 && !error && (
          <div className="rounded-xl border border-app-border bg-app-panel p-6 text-center">
            <Plug size={32} className="mx-auto mb-3 text-app-muted" />
            <div className="text-sm font-semibold text-app-text mb-1">No Connectors</div>
            <div className="text-xs text-app-muted">
              Connectors allow agents to interact with external services.
            </div>
          </div>
        )}

        {connectors.map((c) => (
          <div
            key={c.id}
            className="rounded-xl border border-app-border bg-app-panel p-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                  c.status === 'connected' ? 'bg-green-900/30' : 'bg-red-900/30'
                }`}>
                  <Plug size={18} className={c.status === 'connected' ? 'text-green-400' : 'text-red-400'} />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-semibold text-app-text">{c.type.toUpperCase()}</span>
                    <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                      c.status === 'connected' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                    }`}>
                      {c.status}
                    </span>
                  </div>
                  <div className="text-sm text-app-secondary">{c.label}</div>
                  <div className="text-xs text-app-muted font-mono mt-0.5">{c.account}</div>
                </div>
              </div>
              <div className="flex gap-2">
                {c.type === 'github' && (
                  <a
                    href={`https://github.com/${c.account}`}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg p-2 text-app-muted hover:bg-app-hover hover:text-app-text"
                    title="Open on GitHub"
                  >
                    <ExternalLink size={15} />
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Info notice */}
        <div className="rounded-xl border border-app-border/60 bg-app-panel/50 p-4">
          <div className="text-xs text-app-muted leading-relaxed">
            <strong className="text-app-secondary">Connectors</strong> are configured per-agent and give models access to external tools
            (GitHub repositories, Gmail inbox, custom services). Connector setup and per-agent configuration is available through the
            agent settings dialog. OAuth flows are handled through the browser when adding a new connector.
          </div>
        </div>
      </div>
    </main>
  )
}
