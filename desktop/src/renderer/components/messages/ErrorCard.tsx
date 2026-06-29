import type { ErrorMessage } from '../../api/types'

export function ErrorCard({ message }: { message: ErrorMessage }) {
  return (
    <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
      <div className="text-sm font-semibold text-red-300">{message.title}</div>
      {message.detail && <div className="mt-1 text-sm text-red-200/80">{message.detail}</div>}
    </div>
  )
}
