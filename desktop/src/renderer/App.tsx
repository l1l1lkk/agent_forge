import { useEffect } from 'react'
import { AppShell } from './components/layout/AppShell'
import { useAgentStore } from './stores/agentStore'
import { useRunnerStore } from './stores/runnerStore'
import './styles/globals.css'

export default function App() {
  const loadAgents = useAgentStore(s => s.loadAgents)
  const loadRunners = useRunnerStore(s => s.loadRunners)

  useEffect(() => {
    loadAgents()
    loadRunners()
    const interval = setInterval(() => { loadAgents(); loadRunners() }, 15000)
    return () => clearInterval(interval)
  }, [])

  return <AppShell />
}
