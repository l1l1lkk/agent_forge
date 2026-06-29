import type { Agent, ChatMessage, Connector, Harness } from './types'

export const mockAgents: Agent[] = [
  { id: 'agent-octo', name: 'Octo', avatar: '🐙', sessions: [
    { id: 'session-root', agentId: 'agent-octo', name: 'root', status: 'idle' },
    { id: 'session-octopus', agentId: 'agent-octo', name: 'octopus', status: 'idle', unread: true },
    { id: 'session-archerchat', agentId: 'agent-octo', name: 'ArcherChat', status: 'idle' },
    { id: 'session-endlex', agentId: 'agent-octo', name: 'Endlex', status: 'idle' },
    { id: 'session-ai-zto', agentId: 'agent-octo', name: 'AI-ZTO', status: 'idle' },
  ]},
  { id: 'agent-vera', name: 'Vera', avatar: '🔬', sessions: [
    { id: 'session-hidden', agentId: 'agent-vera', name: '+1 delegation hidden', status: 'idle', hidden: true },
    { id: 'session-review', agentId: 'agent-vera', name: 'review', status: 'idle' },
  ]},
  { id: 'agent-charlie', name: 'Charlie', avatar: '🦉', sessions: [
    { id: 'session-stock', agentId: 'agent-charlie', name: 'stock', status: 'idle' },
  ]},
  { id: 'agent-weber', name: 'Weber', avatar: '🛠', sessions: [
    { id: 'session-ideas', agentId: 'agent-weber', name: 'ideas', status: 'idle' },
  ]},
]

export const mockConnectors: Connector[] = [
  { id: 'connector-github', type: 'github', label: 'GITHUB', account: 'l1l1lkk', status: 'connected' },
  { id: 'connector-gmail', type: 'gmail', label: 'GMAIL', account: 'example@gmail...', status: 'connected' },
]

export const mockHarnesses: Harness[] = [
  { id: 'harness-codex', type: 'codex', label: 'codex-gpt', authType: 'oauth', status: 'ready' },
  { id: 'harness-claude', type: 'claude', label: 'claude', authType: 'oauth', status: 'ready' },
]

export const mockMessages: ChatMessage[] = [
  { id: 'm1', type: 'user', content: 'good. commit and push to main.', createdAt: new Date().toISOString() },
  { id: 'm2', type: 'tool_invocation', toolName: 'Bash', command: 'git status && git diff', summary: 'git status && git diff', status: 'done', createdAt: new Date().toISOString() },
  { id: 'm3', type: 'tool_result', toolName: 'Bash', content: "On branch main\nYour branch is up to date with 'origin/main'.\nChanges not staged for commit...", exitCode: 0, createdAt: new Date().toISOString() },
  { id: 'm4', type: 'tool_invocation', toolName: 'Bash', command: 'git log --oneline -5', summary: 'git log --oneline -5', status: 'done', createdAt: new Date().toISOString() },
  { id: 'm5', type: 'tool_result', toolName: 'Bash', content: '13ae001 docs: correct backend test count\n0a07c59 docs: correct frontend test count', exitCode: 0, createdAt: new Date().toISOString() },
  { id: 'm6', type: 'assistant', agentName: 'Octo', agentAvatar: '🐙', content: 'Pushed `ab58a28`. Two fixes in one commit: delegation single-turn contract and KaTeX math rendering in chat messages.', createdAt: new Date().toISOString() },
  { id: 'm7', type: 'status', label: 'DONE', cost: '$0.2048', createdAt: new Date().toISOString() },
]
