/**
 * Preload script — exposes safe IPC API to the renderer via contextBridge.
 *
 * Security: only whitelisted methods are exposed.
 * No raw Node.js APIs leak to the renderer.
 */

import { contextBridge, ipcRenderer } from 'electron'

const forgeDesktop = {
  daemon: {
    health: (): Promise<unknown> => ipcRenderer.invoke('daemon:health'),
    start: (): Promise<boolean> => ipcRenderer.invoke('daemon:start'),
    stop: (): Promise<void> => ipcRenderer.invoke('daemon:stop'),
    restart: (): Promise<boolean> => ipcRenderer.invoke('daemon:restart'),
    logs: (): Promise<string[]> => ipcRenderer.invoke('daemon:logs'),
    info: (): Promise<{ host: string; port: number }> => ipcRenderer.invoke('daemon:info'),
  },
  api: {
    get: (path: string): Promise<unknown> => ipcRenderer.invoke('api:get', path),
    post: (path: string, body?: unknown): Promise<unknown> => ipcRenderer.invoke('api:post', path, body),
    patch: (path: string, body?: unknown): Promise<unknown> => ipcRenderer.invoke('api:patch', path, body),
    delete: (path: string): Promise<unknown> => ipcRenderer.invoke('api:delete', path),
  },
  dialog: {
    selectFolder: (): Promise<string | null> => ipcRenderer.invoke('dialog:selectFolder'),
  },
  shell: {
    openExternal: (url: string): Promise<void> => ipcRenderer.invoke('shell:openExternal', url),
    openPath: (filePath: string): Promise<void> => ipcRenderer.invoke('shell:openPath', filePath),
  },
  config: {
    get: (): Promise<unknown> => ipcRenderer.invoke('config:get'),
    set: (partial: Record<string, unknown>): Promise<void> => ipcRenderer.invoke('config:set', partial),
    getLocal: (): Promise<unknown> => ipcRenderer.invoke('config:getLocal'),
  },
}

contextBridge.exposeInMainWorld('forgeDesktop', forgeDesktop)

// Type declaration for renderer
export type ForgeDesktopAPI = typeof forgeDesktop
