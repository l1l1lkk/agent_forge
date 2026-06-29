import { useEffect, useState } from 'react'
import { Activity, Server, Terminal, Wrench, Play, Square, RefreshCw } from 'lucide-react'

// Extend window type
declare global {
  interface Window {
    forgeDesktop: {
      daemon: {
        health: () => Promise<{ status: string; version: string } | null>
        start: () => Promise<boolean>
        stop: () => Promise<void>
        restart: () => Promise<boolean>
        logs: () => Promise<string[]>
        info: () => Promise<{ host: string; port: number }>
      }
      api: {
        get: (path: string) => Promise<any>
        post: (path: string, body?: any) => Promise<any>
      }
    }
  }
}

interface BootstrapData {
  health: { status: string }
  projects_count: number
  agents_count: number
  running_sessions: number
  running_tasks: number
  available_runners: string[]
  runners: { name: string; available: boolean }[]
  features: Record<string, boolean>
}

export default function App() {
  const [bootstrap, setBootstrap] = useState<BootstrapData | null>(null)
  const [daemonStatus, setDaemonStatus] = useState<'checking' | 'healthy' | 'unhealthy' | 'starting'>('checking')
  const [logs, setLogs] = useState<string[]>([])
  const [showLogs, setShowLogs] = useState(false)

  const api = window.forgeDesktop

  const checkDaemon = async () => {
    setDaemonStatus('checking')
    const health = await api.daemon.health()
    if (health) {
      setDaemonStatus('healthy')
      // Load bootstrap data
      try {
        const data = await api.api.get('/api/desktop/bootstrap')
        setBootstrap(data as BootstrapData)
      } catch (e) {
        console.error('Bootstrap failed:', e)
      }
    } else {
      setDaemonStatus('unhealthy')
    }
  }

  const startDaemon = async () => {
    setDaemonStatus('starting')
    const ok = await api.daemon.start()
    if (ok) {
      setDaemonStatus('healthy')
      // Small delay then load data
      setTimeout(checkDaemon, 500)
    } else {
      setDaemonStatus('unhealthy')
    }
  }

  const stopDaemon = async () => {
    await api.daemon.stop()
    setDaemonStatus('checking')
    setTimeout(checkDaemon, 500)
  }

  const restartDaemon = async () => {
    setDaemonStatus('starting')
    await api.daemon.restart()
    setTimeout(checkDaemon, 1000)
  }

  useEffect(() => {
    checkDaemon()
    // Poll every 10s
    const interval = setInterval(checkDaemon, 10000)
    return () => clearInterval(interval)
  }, [])

  const statusColor = {
    checking: 'text-yellow-400',
    healthy: 'text-green-400',
    unhealthy: 'text-red-400',
    starting: 'text-blue-400',
  }[daemonStatus]

  const StatusIcon = {
    checking: Activity,
    healthy: Server,
    unhealthy: Square,
    starting: RefreshCw,
  }[daemonStatus]

  return (
    <div className="min-h-screen bg-[#0f0f1a] text-gray-100 font-sans">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Terminal className="text-blue-400" size={28} />
          <div>
            <h1 className="text-xl font-bold">Agent Forge Desktop</h1>
            <p className="text-xs text-gray-500">AI Coding Workbench</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Daemon status */}
          <div className="flex items-center gap-2">
            <StatusIcon className={statusColor} size={18} />
            <span className={`text-sm font-medium ${statusColor}`}>
              {daemonStatus === 'healthy' && 'Daemon Connected'}
              {daemonStatus === 'unhealthy' && 'Daemon Offline'}
              {daemonStatus === 'checking' && 'Checking...'}
              {daemonStatus === 'starting' && 'Starting...'}
            </span>
            {bootstrap && (
              <span className="text-xs text-gray-600 ml-1">
                v{bootstrap.health.status === 'ok' ? '(active)' : ''}
              </span>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-1">
            {daemonStatus !== 'healthy' ? (
              <button onClick={startDaemon} className="px-3 py-1.5 bg-green-700 hover:bg-green-600 rounded text-sm flex items-center gap-1">
                <Play size={14} /> Start
              </button>
            ) : (
              <>
                <button onClick={restartDaemon} className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm flex items-center gap-1">
                  <RefreshCw size={14} /> Restart
                </button>
                <button onClick={stopDaemon} className="px-3 py-1.5 bg-red-800 hover:bg-red-700 rounded text-sm flex items-center gap-1">
                  <Square size={14} /> Stop
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="p-6">
        {/* Status cards */}
        {bootstrap && daemonStatus === 'healthy' && (
          <div className="grid grid-cols-4 gap-4 mb-6">
            <StatusCard icon={<Server size={20} />} label="Projects" value={bootstrap.projects_count} />
            <StatusCard icon={<Wrench size={20} />} label="Agents" value={bootstrap.agents_count} />
            <StatusCard icon={<Activity size={20} />} label="Running Sessions" value={bootstrap.running_sessions} color="text-green-400" />
            <StatusCard icon={<Terminal size={20} />} label="Running Tasks" value={bootstrap.running_tasks} color="text-blue-400" />
          </div>
        )}

        {/* Runners */}
        {bootstrap && (
          <section className="mb-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Available Runners</h2>
            <div className="grid grid-cols-3 gap-4">
              {bootstrap.runners.map((r) => (
                <div key={r.name} className={`p-4 rounded-lg border ${r.available ? 'border-green-800 bg-green-900/20' : 'border-gray-800 bg-gray-900/50'}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{r.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${r.available ? 'bg-green-900 text-green-300' : 'bg-gray-800 text-gray-500'}`}>
                      {r.available ? 'Available' : 'Not Found'}
                    </span>
                  </div>
                </div>
              ))}
              {bootstrap.runners.length === 0 && (
                <p className="text-gray-600 col-span-3 text-sm">No runners registered.</p>
              )}
            </div>
          </section>
        )}

        {/* Features */}
        {bootstrap && (
          <section className="mb-6">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Features</h2>
            <div className="grid grid-cols-4 gap-3">
              {Object.entries(bootstrap.features).map(([name, enabled]) => (
                <div key={name} className={`px-3 py-2 rounded text-sm ${enabled ? 'bg-blue-900/20 text-blue-300' : 'bg-gray-900/30 text-gray-600'}`}>
                  {name.replace(/_/g, ' ')}: {enabled ? 'On' : 'Off'}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Quick start hint */}
        {!bootstrap && daemonStatus === 'healthy' && (
          <div className="text-center py-12">
            <Activity className="mx-auto text-gray-600 mb-3" size={48} />
            <p className="text-gray-500">Loading workspace data...</p>
          </div>
        )}

        {daemonStatus !== 'healthy' && (
          <div className="text-center py-12">
            <Server className="mx-auto text-red-600 mb-3" size={48} />
            <p className="text-gray-400 mb-4">Daemon is not running</p>
            <button onClick={startDaemon} className="px-6 py-2 bg-green-700 hover:bg-green-600 rounded-lg text-white font-medium flex items-center gap-2 mx-auto">
              <Play size={18} /> Start Forge Daemon
            </button>
          </div>
        )}

        {/* Logs toggle */}
        <div className="mt-8">
          <button onClick={() => setShowLogs(!showLogs)} className="text-sm text-gray-600 hover:text-gray-400">
            {showLogs ? 'Hide' : 'Show'} Daemon Logs
          </button>
          {showLogs && (
            <pre className="mt-2 p-4 bg-black/50 rounded-lg text-xs text-gray-400 max-h-64 overflow-y-auto font-mono">
              {logs.length > 0 ? logs.join('\n') : 'No logs yet. Use Start/Restart to see daemon output.'}
            </pre>
          )}
        </div>
      </main>
    </div>
  )
}

function StatusCard({ icon, label, value, color = 'text-gray-300' }: {
  icon: React.ReactNode
  label: string
  value: number
  color?: string
}) {
  return (
    <div className="p-4 rounded-lg border border-gray-800 bg-gray-900/50">
      <div className="flex items-center gap-2 text-gray-500 mb-2">
        {icon}
        <span className="text-xs uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  )
}
