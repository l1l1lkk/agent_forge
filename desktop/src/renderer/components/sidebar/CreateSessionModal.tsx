import { useState } from 'react'
import { X } from 'lucide-react'
import { useAgentStore } from '../../stores/agentStore'

type Props = {
  agentId: string
  agentName: string
  open: boolean
  onClose: () => void
}

export function CreateSessionModal({ agentId, agentName, open, onClose }: Props) {
  const [name, setName] = useState('')
  const [cwd, setCwd] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const loadAgents = useAgentStore((s) => s.loadAgents)

  if (!open) return null

  const handleCreate = async () => {
    setCreating(true)
    setError(null)
    try {
      const projects = await (await import('../../api/client')).fetchProjects()
      const projectId = projects[0]?.id
      if (!projectId) throw new Error('No project found')

      const api = (await import('../../api/client'))
      await api.createSession(projectId, agentId, name || `${agentName} session`, cwd || undefined)

      await loadAgents()
      onClose()
    } catch (e: any) {
      setError(e.message || String(e))
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="w-96 rounded-xl border border-app-border bg-app-panel p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-app-text">New {agentName} Session</h2>
          <button onClick={onClose} className="rounded-md p-1 text-app-muted hover:bg-app-hover hover:text-app-text"><X size={16} /></button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs text-app-muted mb-1">Session name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={cwd || `${agentName} working directory`}
              className="w-full rounded-lg border border-app-border bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted outline-none focus:border-app-accent"
              autoFocus
              onKeyDown={(e) => { if (e.key === 'Enter') handleCreate() }}
            />
          </div>
          <div>
            <label className="block text-xs text-app-muted mb-1">Working directory</label>
            <input
              type="text"
              value={cwd}
              onChange={(e) => setCwd(e.target.value)}
              placeholder="e.g. D:/my-project"
              className="w-full rounded-lg border border-app-border bg-app-bg px-3 py-2 text-sm text-app-text placeholder:text-app-muted outline-none focus:border-app-accent"
              onKeyDown={(e) => { if (e.key === 'Enter') handleCreate() }}
            />
          </div>
        </div>

        {error && <div className="mt-3 text-xs text-red-400">{error}</div>}

        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-lg border border-app-border px-4 py-2 text-sm text-app-muted hover:bg-app-hover">Cancel</button>
          <button onClick={handleCreate} disabled={creating} className="rounded-lg bg-app-accent px-4 py-2 text-sm font-medium text-white hover:bg-violet-600 disabled:opacity-50">
            {creating ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}
