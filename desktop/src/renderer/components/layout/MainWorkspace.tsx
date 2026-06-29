import { ChatHeader } from '../workspace/ChatHeader'
import { MessageList } from '../workspace/MessageList'
import { Composer } from '../workspace/Composer'
import { EmptyWorkspace } from '../workspace/EmptyWorkspace'
import { useSessionStore } from '../../stores/sessionStore'

export function MainWorkspace() {
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId)
  if (!selectedSessionId) return <EmptyWorkspace />
  return (
    <main className="flex min-w-0 flex-1 flex-col bg-app-bg">
      <ChatHeader />
      <MessageList />
      <Composer />
    </main>
  )
}
