import { useEffect, useRef } from 'react'
import { useSessionStore } from '../../stores/sessionStore'
import { useMessageStore } from '../../stores/messageStore'
import { UserMessageBubble } from '../messages/UserMessageBubble'
import { AssistantMessageBubble } from '../messages/AssistantMessageBubble'
import { ToolInvocationCard } from '../messages/ToolInvocationCard'
import { ToolResultCard } from '../messages/ToolResultCard'
import { StatusDivider } from '../messages/StatusDivider'
import { ErrorCard } from '../messages/ErrorCard'
import { ThinkingCard } from '../messages/ThinkingCard'

export function MessageList() {
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId)
  const messagesBySession = useMessageStore((s) => s.messagesBySession)
  const messages = messagesBySession[selectedSessionId || ''] ?? []
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages.length])

  return (
    <div className="flex-1 overflow-y-auto px-5 py-5">
      <div className="mx-auto flex max-w-3xl flex-col gap-3">
        {messages.map((m) => {
          if (m.type === 'user') return <UserMessageBubble key={m.id} message={m} />
          if (m.type === 'assistant') return <AssistantMessageBubble key={m.id} message={m} />
          if (m.type === 'thinking') return <ThinkingCard key={m.id} thinking={m.content || ''} />
          if (m.type === 'tool_invocation') return <ToolInvocationCard key={m.id} message={m} />
          if (m.type === 'tool_result') return <ToolResultCard key={m.id} message={m} />
          if (m.type === 'status') return <StatusDivider key={m.id} message={m} />
          if (m.type === 'error') return <ErrorCard key={m.id} message={m} />
          return null
        })}
        <div ref={endRef} />
      </div>
    </div>
  )
}
