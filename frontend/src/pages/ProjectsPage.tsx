import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Project, type Agent } from '../api/client'
import { useAppStore } from '../stores/appStore'
import { Plus, Trash2, Play } from 'lucide-react'

export function ProjectsPage() {
  const { projects, agents, setProjects, setAgents } = useAppStore()
  const navigate = useNavigate()
  const [showCreate, setShowCreate] = useState(false)
  const [newProject, setNewProject] = useState({ path: '', name: '', runner: 'claude' })
  const [newAgent, setNewAgent] = useState({ name: '', runner: 'claude', model: '' })

  useEffect(() => {
    api.listProjects().then(r => setProjects(r.projects)).catch(console.error)
    api.listAgents().then(r => setAgents(r.agents)).catch(console.error)
  }, [])

  const createProject = async () => {
    if (!newProject.path) return
    await api.createProject({ root_path: newProject.path, name: newProject.name || undefined, default_runner: newProject.runner })
    const r = await api.listProjects()
    setProjects(r.projects)
    setShowCreate(false)
    setNewProject({ path: '', name: '', runner: 'claude' })
  }

  const deleteProject = async (id: string) => {
    await api.deleteProject(id)
    setProjects(projects.filter(p => p.id !== id))
  }

  const createAgent = async () => {
    if (!newAgent.name) return
    await api.createAgent(newAgent)
    const r = await api.listAgents()
    setAgents(r.agents)
    setNewAgent({ name: '', runner: 'claude', model: '' })
  }

  const startSession = async (projectId: string, agentId: string) => {
    const s = await api.createSession({ project: projectId, agent: agentId })
    navigate(`/session/${s.id}`)
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Projects</h1>

      {/* Quick start */}
      {projects.length > 0 && agents.length > 0 && (
        <div className="mb-6 p-4 rounded-lg bg-forge-900/20 border border-forge-800">
          <h2 className="text-sm font-semibold text-forge-300 mb-2">Quick Start</h2>
          <div className="flex gap-2">
            <select id="qs-project" className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm">
              {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <select id="qs-agent" className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm">
              {agents.map(a => <option key={a.id} value={a.id}>{a.name} ({a.runner})</option>)}
            </select>
            <button onClick={() => {
              const p = (document.getElementById('qs-project') as HTMLSelectElement).value
              const a = (document.getElementById('qs-agent') as HTMLSelectElement).value
              startSession(p, a)
            }} className="flex items-center gap-1 px-4 py-1.5 bg-forge-600 hover:bg-forge-500 rounded text-sm font-medium">
              <Play size={14} /> Start
            </button>
          </div>
        </div>
      )}

      {/* Projects grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {projects.map(p => (
          <div key={p.id} className="p-4 rounded-lg bg-gray-900 border border-gray-800 hover:border-gray-700">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-gray-200">{p.name}</h3>
              <button onClick={() => deleteProject(p.id)} className="text-gray-600 hover:text-red-400">
                <Trash2 size={14} />
              </button>
            </div>
            <p className="text-xs text-gray-500 truncate mb-3">{p.root_path}</p>
            <div className="flex gap-2">
              {agents.map(a => (
                <button key={a.id} onClick={() => startSession(p.id, a.id)}
                  className="px-2 py-1 text-xs rounded bg-gray-800 hover:bg-forge-800 text-gray-300 hover:text-forge-200">
                  Chat with {a.name}
                </button>
              ))}
            </div>
          </div>
        ))}
        <button onClick={() => setShowCreate(true)}
          className="p-4 rounded-lg border-2 border-dashed border-gray-700 hover:border-forge-600 text-gray-500 hover:text-forge-400 flex items-center justify-center gap-2">
          <Plus size={20} /> Add Project
        </button>
      </div>

      {/* Create project dialog */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-96 space-y-4">
            <h2 className="text-lg font-bold">Add Project</h2>
            <input type="text" placeholder="Path (e.g. /home/user/repo)" value={newProject.path}
              onChange={e => setNewProject({ ...newProject, path: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm" />
            <input type="text" placeholder="Name (optional)" value={newProject.name}
              onChange={e => setNewProject({ ...newProject, name: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200">Cancel</button>
              <button onClick={createProject} className="px-4 py-2 text-sm bg-forge-600 hover:bg-forge-500 rounded">Add</button>
            </div>
          </div>
        </div>
      )}

      {/* Agents section */}
      <h2 className="text-xl font-bold mb-4">Agents</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
        {agents.map(a => (
          <div key={a.id} className="p-4 rounded-lg bg-gray-900 border border-gray-800">
            <h3 className="font-semibold text-gray-200">{a.name}</h3>
            <p className="text-xs text-gray-500">Runner: {a.runner} {a.model ? `· ${a.model}` : ''}</p>
          </div>
        ))}
      </div>
      {/* Create agent inline */}
      <div className="flex gap-2 items-end p-4 rounded-lg bg-gray-900/50 border border-gray-800">
        <input type="text" placeholder="Agent name" value={newAgent.name}
          onChange={e => setNewAgent({ ...newAgent, name: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm w-32" />
        <input type="text" placeholder="Model (optional)" value={newAgent.model}
          onChange={e => setNewAgent({ ...newAgent, model: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm w-40" />
        <button onClick={createAgent}
          className="px-4 py-1.5 text-sm bg-forge-600 hover:bg-forge-500 rounded flex items-center gap-1">
          <Plus size={14} /> Add Agent
        </button>
      </div>
    </div>
  )
}
