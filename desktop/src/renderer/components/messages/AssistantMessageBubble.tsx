import type { AssistantMessage } from '../../api/types'

export function AssistantMessageBubble({ message }: { message: AssistantMessage }) {
  return (
    <div className="flex justify-start">
      <div className="w-full max-w-4xl">
        <div className="mb-1 flex items-center gap-2 text-sm font-medium text-app-text">
          <span>{message.agentAvatar}</span>
          <span>{message.agentName}</span>
        </div>
        <div className="rounded-xl border border-app-border bg-app-panel px-4 py-3 text-sm leading-6 text-app-text">
          {message.content}
        </div>
      </div>
    </div>
  )
}
