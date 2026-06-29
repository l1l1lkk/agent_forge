/**
 * IPC handlers — exposes safe APIs from main process to renderer.
 *
 * Security: only whitelisted operations are exposed. No raw fs/exec access.
 */

import { ipcMain, dialog, shell, BrowserWindow } from 'electron'
import { daemon } from './daemonSingleton'
import { getConfig, setConfig, getLocalConfig, getUiConfig } from './configStore'
import http from 'http'

export function registerIpcHandlers(): void {
  const { host, port } = daemon.getInfo()

  // ── Daemon ──────────────────────────────────────────────

  ipcMain.handle('daemon:health', async () => {
    return daemon.isHealthy()
  })

  ipcMain.handle('daemon:start', async () => {
    return daemon.start()
  })

  ipcMain.handle('daemon:stop', async () => {
    await daemon.stop()
  })

  ipcMain.handle('daemon:restart', async () => {
    return daemon.restart()
  })

  ipcMain.handle('daemon:logs', async () => {
    return daemon.getLogs()
  })

  ipcMain.handle('daemon:info', async () => {
    return daemon.getInfo()
  })

  // ── HTTP proxy (renderer → daemon) ──────────────────────

  ipcMain.handle('api:get', async (_event, apiPath: string) => {
    return _httpGet(`http://${host}:${port}${apiPath}`)
  })

  ipcMain.handle('api:post', async (_event, apiPath: string, body: unknown) => {
    return _httpPost(`http://${host}:${port}${apiPath}`, body)
  })

  // ── Dialog ──────────────────────────────────────────────

  ipcMain.handle('dialog:selectFolder', async () => {
    const win = BrowserWindow.getFocusedWindow()
    if (!win) return null
    const result = await dialog.showOpenDialog(win, {
      properties: ['openDirectory'],
    })
    return result.canceled ? null : result.filePaths[0] || null
  })

  // ── Shell ───────────────────────────────────────────────

  ipcMain.handle('shell:openExternal', async (_event, url: string) => {
    await shell.openExternal(url)
  })

  ipcMain.handle('shell:openPath', async (_event, filePath: string) => {
    shell.openPath(filePath)
  })

  // ── Config ──────────────────────────────────────────────

  ipcMain.handle('config:get', async () => {
    return getConfig()
  })

  ipcMain.handle('config:set', async (_event, partial: Record<string, unknown>) => {
    setConfig(partial)
  })

  ipcMain.handle('config:getLocal', async () => {
    return getLocalConfig()
  })
}

// ── HTTP helpers ──────────────────────────────────────────────

function _httpGet(url: string): Promise<unknown> {
  return new Promise((resolve, reject) => {
    http.get(url, { timeout: 10000 }, (res) => {
      let data = ''
      res.on('data', (chunk: string) => (data += chunk))
      res.on('end', () => {
        try { resolve(JSON.parse(data)) }
        catch { resolve(data) }
      })
    }).on('error', reject)
  })
}

function _httpPost(url: string, body: unknown): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(body || {})
    const req = http.request(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': String(Buffer.byteLength(postData)) },
      timeout: 10000,
    }, (res) => {
      let data = ''
      res.on('data', (chunk: string) => (data += chunk))
      res.on('end', () => {
        try { resolve(JSON.parse(data)) }
        catch { resolve(data) }
      })
    })
    req.on('error', reject)
    req.write(postData)
    req.end()
  })
}
