import { useState } from 'react'
import { Copy, Check, X } from 'lucide-react'
import type { AgentSession } from '../../api/types'
import { useSessionStore } from '../../stores/sessionStore'
import { useNavigationStore } from '../../stores/navigationStore'
import { useAgentStore } from '../../stores/agentStore'
import { deleteSession } from '../../api/client'

export function SessionTreeItem({ session }: { session: AgentSession }) {
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId)
  const openChat = useNavigationStore((s) => s.openChat)
  const loadAgents = useAgentStore((s) => s.loadAgents)
  const isSelected = selectedSessionId === session.id

  const [copied, setCopied] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const dotColor = session.status === 'running' ? 'bg-blue-400' : session.status === 'error' ? 'bg-red-400' : session.unread ? 'bg-app-accent' : 'bg-app-muted'

  const handleCopyId = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard.writeText(session.id).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowConfirm(true)
  }

  const handleConfirmDelete = async () => {
    setDeleting(true)
    try {
      await deleteSession(session.id)
      await loadAgents()
    } catch {} finally {
      setDeleting(false)
      setShowConfirm(false)
    }
  }

  return (
    <>
      <div className="group flex items-center gap-1">
        <button
          className={`flex flex-1 items-center gap-2 rounded-lg px-2 py-2 text-left text-sm ${isSelected ? 'bg-app-selected text-app-text' : 'text-app-secondary hover:bg-app-hover hover:text-app-text'}`}
          onClick={() => openChat({ agentId: session.agentId, sessionId: session.id })}
        >
          <span className={`h-2 w-2 shrink-0 rounded-full ${dotColor}`} />
          {session.hidden && <span className="text-app-muted text-xs">👁</span>}
          <span className={`min-w-0 truncate ${session.hidden ? 'text-app-muted' : ''}`}>{session.name}</span>
        </button>

        <div className="hidden group-hover:flex items-center gap-0.5 shrink-0">
          <button onClick={handleCopyId} className="rounded p-1 text-app-muted hover:bg-app-hover hover:text-app-text" title="Copy session ID">
            {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
          </button>
          <button onClick={handleDeleteClick} className="rounded p-1 text-red-400/50 hover:text-red-400 hover:bg-red-900/20" title="Delete session">
            <X size={12} />
          </button>
        </div>
      </div>

      {/* Delete confirmation modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowConfirm(false)}>
          <div className="w-80 rounded-xl border border-red-500/30 bg-app-panel p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 mb-3">
              <X size={18} className="text-red-400" />
              <h3 className="text-sm font-semibold text-app-text">Delete Session</h3>
            </div>
            <p className="text-sm text-app-secondary mb-1">Are you sure you want to delete</p>
            <p className="text-sm font-medium text-app-text truncate mb-4">"{session.name}"?</p>
            <p className="text-xs text-app-muted mb-4">This will permanently delete all messages and cannot be undone.</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowConfirm(false)} className="rounded-lg border border-app-border px-4 py-2 text-sm text-app-muted hover:bg-app-hover">Cancel</button>
              <button onClick={handleConfirmDelete} disabled={deleting} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50">
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
