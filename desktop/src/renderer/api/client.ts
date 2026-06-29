/** API client — all calls go through IPC to main process. */
import type { Agent, AgentSession, ChatMessage } from './types'

function api(): { get(path: string): Promise<any>; post(path: string, body?: any): Promise<any> } {
  if (window.forgeDesktop?.api) return window.forgeDesktop.api
  // Fallback for browser dev
  return {
    get: async (path: string) => fetch(`http://127.0.0.1:8765${path}`).then(r => r.json()),
    post: async (path: string, body?: any) => fetch(`http://127.0.0.1:8765${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(r => r.json()),
  }
}

export async function fetchAgents(): Promise<Agent[]> {
  const data = await api().get('/api/agents')
  return (data.agents || []).map((a: any) => ({
    id: a.id, name: a.name, avatar: _avatar(a.name), sessions: [],
  }))
}

export async function fetchSessions(): Promise<AgentSession[]> {
  const data = await api().get('/api/sessions')
  return (data.sessions || []).map((s: any) => ({
    id: s.id, agentId: s.agent_id, name: s.title || s.id.slice(-8), status: s.status || 'idle',
  }))
}

export async function fetchMessages(sessionId: string): Promise<ChatMessage[]> {
  const data = await api().get(`/api/sessions/${sessionId}/messages`)
  return (data.messages || []).map((m: any) => ({
    id: m.id, type: m.role === 'user' ? 'user' : 'assistant',
    content: m.content || '', createdAt: m.created_at,
    agentName: '', agentAvatar: '',
  } as ChatMessage))
}

export async function sendMessage(sessionId: string, content: string): Promise<void> {
  await api().post(`/api/sessions/${sessionId}/messages`, { role: 'user', content, run: true })
}

export async function fetchProjects(): Promise<any[]> {
  const data = await api().get('/api/projects')
  return data.projects || []
}

export async function createSession(projectId: string, agentId: string, title: string): Promise<any> {
  return api().post('/api/sessions', { project: projectId, agent: agentId, title })
}

export async function fetchRunners(): Promise<any[]> {
  const data = await api().get('/api/runners')
  return (data.runners || []).map((r: any) => ({
    id: `runner-${r.name}`, type: r.name.includes('claude') ? 'claude' : r.name.includes('codex') ? 'codex' : 'local',
    label: r.name, authType: r.name === 'claude' || r.name === 'codex' ? 'oauth' : 'none',
    status: r.available ? 'ready' : 'missing',
  }))
}

function _avatar(name: string): string {
  const map: Record<string, string> = { coding: '💻', claude: '🧠', review: '🔬', default: '🤖' }
  return map[name] || map['default']
}
