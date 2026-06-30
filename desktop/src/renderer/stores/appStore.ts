import { create } from 'zustand'
import type { ConnectionStatus } from '../api/types'

type AppView = 'workspace' | 'settings' | 'diagnostics' | 'schedules' | 'connectors' | 'git'

type AppStore = {
  view: AppView
  connectionStatus: ConnectionStatus
  daemonLabel: string
  setView: (view: AppView) => void
  setConnectionStatus: (status: ConnectionStatus) => void
}

export const useAppStore = create<AppStore>((set) => ({
  view: 'workspace',
  connectionStatus: 'connected',
  daemonLabel: 'Local',
  setView: (view) => set({ view }),
  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),
}))
