import type { StatusMessage } from '../../api/types'

export function StatusDivider({ message }: { message: StatusMessage }) {
  return (
    <div className="flex justify-center py-3">
      <div className="rounded-full border border-app-border bg-app-card px-3 py-1 text-xs font-semibold uppercase tracking-wide text-app-muted">
        {message.label}
        {message.cost && <span className="ml-1 normal-case">· {message.cost}</span>}
      </div>
    </div>
  )
}
