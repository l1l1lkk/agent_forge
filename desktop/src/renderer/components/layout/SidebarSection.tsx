import type { ReactNode } from 'react'

export function SidebarSection({ title, count, action, children }: { title: string; count?: number; action?: ReactNode; children: ReactNode }) {
  return (
    <section>
      <div className="mb-2 flex items-center justify-between px-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-app-muted">
          <span>{title}</span>
          {typeof count === 'number' && <span>{count}</span>}
        </div>
        {action}
      </div>
      <div className="space-y-1">{children}</div>
    </section>
  )
}
