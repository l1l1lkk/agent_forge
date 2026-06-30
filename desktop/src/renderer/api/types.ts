export type ConnectionStatus = 'checking' | 'connected' | 'disconnected'
export type SessionStatus = 'idle' | 'running' | 'error' | 'done'

export type Agent = {
  id: string; name: string; avatar: string; sessions: AgentSession[]
}

export type AgentSession = {
  id: string; agentId: string; name: string; status: SessionStatus; unread?: boolean; hidden?: boolean; delegation?: DelegationInfo
}

export type DelegationInfo = {
  id: string
  parentSessionId?: string
  parentAgentId?: string
  parentAgentName?: string
  targetAgentId?: string
  targetAgentName?: string
  childSessionId?: string
  depth?: number
}

export type Connector = {
  id: string; type: 'github' | 'gmail' | 'custom'; label: string; account: string; status: 'connected' | 'disconnected'
}

export type Harness = {
  id: string; type: 'codex' | 'claude' | 'local'; label: string; authType?: 'oauth' | 'api_key' | 'none'; status: 'ready' | 'missing' | 'error'
}

export type ChatMessage =
  | UserMessage | AssistantMessage | ThinkingMessage | ToolInvocationMessage | ToolResultMessage | DelegationResultMessage | StatusMessage | ErrorMessage

export type ThinkingMessage = { id: string; type: 'thinking'; content: string; signature?: string; createdAt: string }

export type UserMessage = { id: string; type: 'user'; content: string; createdAt: string }
export type AssistantMessage = { id: string; type: 'assistant'; agentName: string; agentAvatar: string; content: string; createdAt: string }
export type ToolInvocationMessage = { id: string; type: 'tool_invocation'; toolName: string; command?: string; summary: string; status: 'running' | 'done' | 'error'; createdAt: string }
export type ToolResultMessage = { id: string; type: 'tool_result'; toolName?: string; content: string; exitCode?: number; createdAt: string }
export type DelegationResultMessage = { id: string; type: 'delegation_result'; content: string; delegationId: string; childSessionId?: string; agentId?: string; agentName?: string; createdAt: string }
export type StatusMessage = { id: string; type: 'status'; label: string; cost?: string; createdAt: string }
export type ErrorMessage = { id: string; type: 'error'; title: string; detail?: string; createdAt: string }
