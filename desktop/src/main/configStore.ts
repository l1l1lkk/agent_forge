/**
 * ConfigStore — persistent desktop configuration using electron-store.
 *
 * Config location: %APPDATA%/agent-forge-desktop/config.json
 * Separate from the forge CLI config (~/.forge/).
 */

import Store from 'electron-store'

interface RemoteConfig {
  name: string
  baseUrl: string
  authToken: string
}

interface AppConfig {
  mode: 'local' | 'remote'
  local: {
    host: string
    port: number
    autoStart: boolean
    authToken: string
  }
  remotes: RemoteConfig[]
  ui: {
    theme: 'dark' | 'light'
  }
}

const defaults: AppConfig = {
  mode: 'local',
  local: {
    host: '127.0.0.1',
    port: 8765,
    autoStart: true,
    authToken: '',
  },
  remotes: [],
  ui: {
    theme: 'dark',
  },
}

export const configStore = new Store<AppConfig>({
  name: 'config',
  defaults,
})

export function getConfig(): AppConfig {
  return configStore.store
}

export function setConfig(partial: Partial<AppConfig>): void {
  configStore.set(partial as Record<string, unknown>)
}

export function getLocalConfig() {
  return configStore.get('local')
}

export function getUiConfig() {
  return configStore.get('ui')
}
