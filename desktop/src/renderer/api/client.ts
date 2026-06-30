/** API client — all calls go through IPC to main process. */
import type { Agent, AgentSession, ChatMessage, Connector } from './types'

function api(): { get(path: string): Promise<any>; post(path: string, body?: any): Promise<any>; delete(path: string): Promise<any> } {
  if (window.forgeDesktop?.api) return window.forgeDesktop.api
  // Fallback for browser dev
  return {
    get: async (path: string) => parseResponse(await fetch(`http://127.0.0.1:8765${path}`), path),
    post: async (path: string, body?: any) => parseResponse(await fetch(`http://127.0.0.1:8765${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }), path),
    delete: async (path: string) => parseResponse(await fetch(`http://127.0.0.1:8765${path}`, { method: 'DELETE' }), path),
  }
}

async function parseResponse(response: Response, path: string): Promise<any> {
  const text = await response.text()
  let payload: any = text
  try {
    payload = text ? JSON.parse(text) : null
  } catch {
    // Keep plain text payload.
  }
  if (!response.ok) {
    const detail = typeof payload === 'object' && payload?.detail ? JSON.stringify(payload.detail) : text
    throw new Error(`${response.status} ${response.statusText} for ${path}${detail ? `: ${detail}` : ''}`)
  }
  return payload
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
  return (data.messages || []).map((m: any) => {
    const role = m.role
    let t: any = 'assistant'
    let content = m.content || ''
    let extra: any = {}

    if (role === 'user') t = 'user'
    else if (role === 'thinking') t = 'thinking'
    else if (role === 'tool_call') {
      t = 'tool_invocation'
      try {
        const p = JSON.parse(content)
        content = p.command || content
        extra.toolName = p.tool || ''
        extra.summary = p.command || ''
      } catch {}
    }
    else if (role === 'tool_result') {
      t = 'tool_result'
      try {
        const p = JSON.parse(content)
        content = p.content || content
        extra.exitCode = p.is_error ? 1 : 0
      } catch {}
    }

    return { id: m.id, type: t, content, createdAt: m.created_at, agentName: '', agentAvatar: '', ...extra } as ChatMessage
  })
}

export async function sendMessage(sessionId: string, content: string): Promise<void> {
  await api().post(`/api/sessions/${sessionId}/messages`, { role: 'user', content, run: true })
}

export async function fetchProjects(): Promise<any[]> {
  const data = await api().get('/api/projects')
  return data.projects || []
}

export async function createSession(projectId: string, agentId: string, title: string, cwd?: string): Promise<any> {
  return api().post('/api/sessions', { project: projectId, agent: agentId, title, cwd })
}

export async function fetchRunners(): Promise<any[]> {
  const data = await api().get('/api/runners')
  return (data.runners || []).map((r: any) => ({
    id: `runner-${r.name}`, type: r.name.includes('claude') ? 'claude' : r.name.includes('codex') ? 'codex' : 'local',
    label: r.name, authType: r.name === 'claude' || r.name === 'codex' ? 'oauth' : 'none',
    status: r.available ? 'ready' : 'missing',
  }))
}

export async function fetchDiagnostics(): Promise<any> {
  return api().get('/api/desktop/diagnostics')
}

export async function fetchGitStatus(projectPath?: string): Promise<any> {
  const params = projectPath ? `?path=${encodeURIComponent(projectPath)}` : ''
  return api().get(`/api/desktop/git-status${params}`)
}

export async function fetchGitDiff(repoRoot: string, file: string): Promise<string> {
  const params = `?path=${encodeURIComponent(repoRoot)}&file=${encodeURIComponent(file)}`
  return api().get(`/api/desktop/git-diff${params}`)
}

export async function fetchSchedules(): Promise<any[]> {
  const data = await api().get('/api/schedules')
  return data.schedules || []
}

export async function pauseSchedule(name: string): Promise<any> {
  return api().post(`/api/schedules/${name}/pause`)
}

export async function resumeSchedule(name: string): Promise<any> {
  return api().post(`/api/schedules/${name}/resume`)
}

export async function deleteSchedule(name: string): Promise<any> {
  return api().delete(`/api/schedules/${encodeURIComponent(name)}`)
}

export async function interruptSession(sessionId: string): Promise<any> {
  return api().post(`/api/sessions/${sessionId}/interrupt`)
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api().delete(`/api/sessions/${sessionId}`)
}

export async function fetchConnectors(): Promise<Connector[]> {
  const data = await api().get('/api/connectors')
  return data.connectors || []
}

function _avatar(name: string): string {
  const map: Record<string, string> = { coding: '💻', claude: '🧠', review: '🔬', default: '🤖' }
  return map[name] || map['default']
}
