const BASE = '/api'

export interface Project {
  id: string; name: string; root_path: string; default_runner?: string;
  created_at: string; updated_at: string;
}

export interface Agent {
  id: string; name: string; runner: string; model?: string;
  system_prompt?: string; temperature?: number;
}

export interface Session {
  id: string; project_id: string; agent_id: string; title?: string;
  status: string; runner: string; cwd?: string; created_at: string;
}

export interface Message {
  id: string; session_id: string; role: string; content?: string;
  seq: number; created_at: string;
}

export interface WsEvent {
  id: string; type: string; seq: number; session_id?: string;
  task_id?: string; payload: Record<string, any>; created_at: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: { message: r.statusText } }))
    throw new Error(err.detail?.message || r.statusText)
  }
  if (r.status === 204) return undefined as T
  return r.json()
}

export const api = {
  // Projects
  listProjects: () => request<{ projects: Project[]; total: number }>('/projects'),
  createProject: (data: any) => request<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),

  // Agents
  listAgents: () => request<{ agents: Agent[]; total: number }>('/agents'),
  createAgent: (data: any) => request<Agent>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  deleteAgent: (id: string) => request<void>(`/agents/${id}`, { method: 'DELETE' }),

  // Sessions
  listSessions: (projectId?: string) => {
    const q = projectId ? `?project_id=${projectId}` : ''
    return request<{ sessions: Session[]; total: number }>(`/sessions${q}`)
  },
  createSession: (data: any) => request<Session>('/sessions', { method: 'POST', body: JSON.stringify(data) }),
  getSession: (id: string) => request<Session>(`/sessions/${id}`),
  deleteSession: (id: string) => request<void>(`/sessions/${id}`, { method: 'DELETE' }),

  // Messages
  getMessages: (sessionId: string) =>
    request<{ messages: Message[]; total: number }>(`/sessions/${sessionId}/messages`),
  sendMessage: (sessionId: string, content: string, run: boolean = true) =>
    request<Message>(`/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ role: 'user', content, run }),
    }),
  interruptSession: (sessionId: string) =>
    request<Session>(`/sessions/${sessionId}/interrupt`, { method: 'POST' }),
}
