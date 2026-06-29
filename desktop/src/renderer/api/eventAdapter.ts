/**
 * Maps forge WS events → UI ChatMessage timeline items.
 * Handles streaming delta merging and tool/result pairing.
 */
import type { ChatMessage } from './types'

export function adaptEvent(event: any): ChatMessage | ChatMessage[] | null {
  const etype = event?.type
  const payload = event?.payload || {}
  const id = event?.id || `evt-${Date.now()}-${Math.random().toString(36).slice(2,6)}`
  const now = new Date().toISOString()

  switch (etype) {
    case 'session_started':
      return { id, type: 'status', label: 'SESSION STARTED', createdAt: now }

    case 'assistant_text_delta': {
      const text = payload.text || ''
      if (!text.trim()) return null
      return { id: `delta-${id}`, type: 'assistant', agentName: '', agentAvatar: '🤖', content: text, createdAt: now }
    }

    case 'assistant_message': {
      const text = payload.text || payload.content || JSON.stringify(payload.content_blocks || payload)
      if (!text || text.startsWith('[{')) return null // skip raw block dumps
      return { id, type: 'assistant', agentName: '', agentAvatar: '🤖', content: text, createdAt: now }
    }

    case 'tool_call_started': {
      const input = payload.input || {}
      const cmd = input.command || JSON.stringify(input).slice(0, 200)
      return {
        id: payload.id || id, type: 'tool_invocation',
        toolName: payload.tool || 'unknown',
        command: cmd, summary: cmd,
        status: 'running', createdAt: now,
      }
    }

    case 'tool_result': {
      const content = typeof payload.content === 'string'
        ? payload.content.slice(0, 3000)
        : JSON.stringify(payload.content).slice(0, 3000)
      return {
        id: `result-${payload.tool_use_id || id}`, type: 'tool_result',
        toolName: payload.tool || '',
        content, exitCode: payload.exit_code ?? (payload.is_error ? 1 : 0),
        createdAt: now,
      }
    }

    case 'session_status': {
      const st = payload.status || ''
      if (st === 'completed' || st === 'idle')
        return { id, type: 'status', label: 'DONE', cost: payload.usage?.cost, createdAt: now }
      if (st === 'running')
        return { id, type: 'status', label: 'RUNNING', createdAt: now }
      return null
    }

    case 'error':
      return { id, type: 'error', title: payload.error || 'Error', detail: payload.message || '', createdAt: now }

    default:
      return null
  }
}
