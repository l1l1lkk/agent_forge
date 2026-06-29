import { useEffect } from 'react'
import { AppShell } from './components/layout/AppShell'
import { useAgentStore } from './stores/agentStore'
import './styles/globals.css'

export default function App() {
  const loadAgents = useAgentStore(s => s.loadAgents)

  useEffect(() => {
    loadAgents()
    const interval = setInterval(loadAgents, 15000)
    return () => clearInterval(interval)
  }, [])

  return <AppShell />
}
