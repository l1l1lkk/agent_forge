import { create } from 'zustand'
import { fetchRunners } from '../api/client'
import type { Harness } from '../api/types'

type RunnerStore = {
  runners: Harness[]
  loading: boolean
  error: string | null
  loadRunners: () => Promise<void>
}

export const useRunnerStore = create<RunnerStore>((set) => ({
  runners: [],
  loading: false,
  error: null,
  loadRunners: async () => {
    set({ loading: true, error: null })
    try {
      const runners = await fetchRunners()
      set({ runners: runners.length > 0 ? runners : [] })
    } catch (e) {
      set({ error: String(e) })
    } finally {
      set({ loading: false })
    }
  },
}))
