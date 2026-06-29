import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAppStore } from '../stores/appStore'
import { api, type Project } from '../api/client'
import { FolderKanban, MessageSquare, Bot, Plus } from 'lucide-react'

export function Layout({ children }: { children: React.ReactNode }) {
  const { projects, sessions, setProjects, setSessions, currentSession } = useAppStore()
  const [showNewProject, setShowNewProject] = useState(false)
  const location = useLocation()

  useEffect(() => {
    api.listProjects().then(r => setProjects(r.projects)).catch(console.error)
  }, [])

  useEffect(() => {
    api.listSessions().then(r => setSessions(r.sessions)).catch(console.error)
  }, [currentSession])

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold text-forge-400">
            <Link to="/">forge-agent</Link>
          </h1>
          <p className="text-xs text-gray-500 mt-1">AI Coding Workbench</p>
        </div>

        {/* Projects */}
        <div className="p-3 border-b border-gray-800">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1">
              <FolderKanban size={14} /> Projects
            </h2>
            <button onClick={() => setShowNewProject(true)}
              className="text-gray-500 hover:text-forge-400">
              <Plus size={16} />
            </button>
          </div>
          <div className="space-y-0.5 max-h-40 overflow-y-auto">
            {projects.map(p => (
              <Link key={p.id} to={`/session/new?project=${p.id}`}
                className="block px-2 py-1.5 rounded text-sm text-gray-300 hover:bg-gray-800 hover:text-forge-300 truncate">
                {p.name}
              </Link>
            ))}
          </div>
        </div>

        {/* Sessions */}
        <div className="flex-1 overflow-y-auto p-3">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1 mb-2">
            <MessageSquare size={14} /> Sessions
          </h2>
          <div className="space-y-0.5">
            {sessions.map(s => (
              <Link key={s.id} to={`/session/${s.id}`}
                className={`block px-2 py-1.5 rounded text-sm truncate ${
                  location.pathname.includes(s.id)
                    ? 'bg-forge-900/30 text-forge-300'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`}>
                <div className="truncate">{s.title || s.id}</div>
                <div className="text-xs text-gray-600">{s.status}</div>
              </Link>
            ))}
            {sessions.length === 0 && (
              <p className="text-xs text-gray-600 px-2">No sessions yet</p>
            )}
          </div>
        </div>

        {/* Status */}
        <div className="p-3 border-t border-gray-800 text-xs text-gray-600">
          v0.0.2rc1 — Claude Runner
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {children}
      </main>
    </div>
  )
}
