/**
 * Maps forge WS events → UI ChatMessage cards.
 */
import type { ChatMessage } from './types'

export function adaptEvent(event: any): ChatMessage | null {
  const etype = event?.type
  const payload = event?.payload || {}
  const id = event?.id || `evt-${Date.now()}`
  const now = new Date().toISOString()

  switch (etype) {
    case 'assistant_text_delta':
      return { id, type: 'assistant', agentName: '', agentAvatar: '🤖', content: payload.text || '', createdAt: now }

    case 'assistant_message':
      return { id, type: 'assistant', agentName: '', agentAvatar: '🤖', content: payload.text || JSON.stringify(payload), createdAt: now }

    case 'tool_call_started':
      return { id, type: 'tool_invocation',
        toolName: payload.tool || 'unknown',
        command: payload.input?.command || '',
        summary: payload.input?.command || payload.tool || '',
        status: 'running', createdAt: now }

    case 'tool_result':
      return { id, type: 'tool_result',
        toolName: payload.tool || '',
        content: typeof payload.content === 'string' ? payload.content.slice(0, 2000) : JSON.stringify(payload.content).slice(0, 2000),
        exitCode: payload.exit_code ?? (payload.is_error ? 1 : 0),
        createdAt: now }

    case 'session_status':
      if (payload.status === 'completed' || payload.status === 'idle') {
        return { id, type: 'status', label: 'DONE', cost: payload.usage?.cost, createdAt: now }
      }
      return null

    case 'error':
      return { id, type: 'error', title: payload.error || 'Unknown error', detail: payload.message, createdAt: now }

    default:
      return null
  }
}
