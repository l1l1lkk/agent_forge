import type { UserMessage } from '../../api/types'

export function UserMessageBubble({ message }: { message: UserMessage }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-2xl">
        <div className="mb-1 text-right text-xs font-medium text-app-muted">You</div>
        <div className="rounded-xl border border-app-accent/40 bg-app-card px-4 py-3 text-sm leading-6 text-app-text shadow-sm">
          {message.content}
        </div>
      </div>
    </div>
  )
}
