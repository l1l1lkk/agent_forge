import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useAppStore } from '../stores/appStore'
import { api } from '../api/client'
import { ChatWindow } from '../components/ChatWindow'

export function SessionPage() {
  const { id } = useParams<{ id: string }>()
  const { setCurrentSession } = useAppStore()

  useEffect(() => {
    if (id && id !== 'new') {
      api.getSession(id).then(s => setCurrentSession(s)).catch(console.error)
    }
    return () => setCurrentSession(null)
  }, [id])

  if (!id || id === 'new') {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        Select a project and agent to start a new session.
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col">
      <ChatWindow sessionId={id} />
    </div>
  )
}
