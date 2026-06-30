import { useEffect, useState } from 'react'
import { Clock, Play, Pause, RefreshCw, Trash2 } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import { deleteSchedule, fetchSchedules, pauseSchedule, resumeSchedule } from '../../api/client'

interface Schedule {
  id: string
  name: string
  project_id: string
  agent_id: string
  cron: string
  prompt: string
  enabled: boolean
  created_at: string
  updated_at: string
}

export function SchedulesPanel() {
  const setView = useAppStore((s) => s.setView)
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchSchedules()
      setSchedules(data)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function toggle(s: Schedule) {
    try {
      if (s.enabled) {
        await pauseSchedule(s.name)
      } else {
        await resumeSchedule(s.name)
      }
      await load()
    } catch (e) {
      setError(String(e))
    }
  }

  async function remove(s: Schedule) {
    const confirmed = window.confirm(`Delete schedule "${s.name}"?`)
    if (!confirmed) return

    try {
      await deleteSchedule(s.name)
      await load()
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <main className="flex min-w-0 flex-1 flex-col bg-app-bg">
      <div className="flex h-12 items-center justify-between border-b border-app-border px-5">
        <h2 className="text-sm font-semibold text-app-text">Schedules</h2>
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
        {loading && !schedules.length && (
          <div className="text-sm text-app-muted">Loading schedules...</div>
        )}
        {error && (
          <div className="rounded-xl border border-red-800 bg-red-900/20 p-4">
            <div className="text-sm text-red-400">{error}</div>
          </div>
        )}
        {!loading && schedules.length === 0 && !error && (
          <div className="rounded-xl border border-app-border bg-app-panel p-6 text-center">
            <Clock size={32} className="mx-auto mb-3 text-app-muted" />
            <div className="text-sm font-semibold text-app-text mb-1">No Schedules</div>
            <div className="text-xs text-app-muted">
              Create a schedule via the chat command <code className="rounded bg-app-badge px-1 py-0.5 text-app-accent">/schedule</code>
            </div>
          </div>
        )}
        {schedules.map((s) => (
          <div
            key={s.id}
            className={`rounded-xl border bg-app-panel p-4 transition-colors ${
              s.enabled ? 'border-app-border' : 'border-app-border/40 opacity-70'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-app-text">{s.name}</span>
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                    s.enabled ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                  }`}>
                    {s.enabled ? 'Active' : 'Paused'}
                  </span>
                </div>
                <div className="text-xs text-app-muted mb-2 font-mono">{s.cron}</div>
                <div className="text-sm text-app-secondary line-clamp-2">{s.prompt}</div>
                <div className="mt-2 text-xs text-app-muted">
                  Agent: {s.agent_id.slice(0, 8)} / Project: {s.project_id.slice(0, 8)} / Created: {s.created_at.slice(0, 10)}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <button
                  className={`rounded-lg p-2 transition-colors ${
                    s.enabled
                      ? 'text-amber-400 hover:bg-amber-900/20'
                      : 'text-green-400 hover:bg-green-900/20'
                  }`}
                  onClick={() => toggle(s)}
                  title={s.enabled ? 'Pause' : 'Resume'}
                >
                  {s.enabled ? <Pause size={16} /> : <Play size={16} />}
                </button>
                <button
                  className="rounded-lg p-2 text-red-400 transition-colors hover:bg-red-900/20"
                  onClick={() => remove(s)}
                  title="Delete"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </main>
  )
}
