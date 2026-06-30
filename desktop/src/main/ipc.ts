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

  ipcMain.handle('api:patch', async (_event, apiPath: string, body: unknown) => {
    return _httpPatch(`http://${host}:${port}${apiPath}`, body)
  })

  ipcMain.handle('api:delete', async (_event, apiPath: string) => {
    return _httpDelete(`http://${host}:${port}${apiPath}`)
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
        const payload = _parseHttpPayload(data)
        if (!res.statusCode || res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`GET ${url} failed with ${res.statusCode}: ${_formatHttpError(payload, data)}`))
          return
        }
        resolve(payload)
      })
    }).on('error', reject)
  })
}

function _httpPost(url: string, body: unknown): Promise<unknown> {
  return _httpJson(url, 'POST', body)
}

function _httpPatch(url: string, body: unknown): Promise<unknown> {
  return _httpJson(url, 'PATCH', body)
}

function _httpJson(url: string, method: 'POST' | 'PATCH', body: unknown): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(body || {})
    const req = http.request(url, {
      method,
      headers: { 'Content-Type': 'application/json', 'Content-Length': String(Buffer.byteLength(postData)) },
      timeout: 10000,
    }, (res) => {
      let data = ''
      res.on('data', (chunk: string) => (data += chunk))
      res.on('end', () => {
        const payload = _parseHttpPayload(data)
        if (!res.statusCode || res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`${method} ${url} failed with ${res.statusCode}: ${_formatHttpError(payload, data)}`))
          return
        }
        resolve(payload)
      })
    })
    req.on('error', reject)
    req.write(postData)
    req.end()
  })
}

function _httpDelete(url: string): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method: 'DELETE', timeout: 10000 }, (res) => {
      let data = ''
      res.on('data', (chunk: string) => (data += chunk))
      res.on('end', () => {
        const payload = _parseHttpPayload(data)
        if (!res.statusCode || res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(`DELETE ${url} failed with ${res.statusCode}: ${_formatHttpError(payload, data)}`))
          return
        }
        resolve(payload)
      })
    })
    req.on('error', reject)
    req.end()
  })
}

function _parseHttpPayload(data: string): unknown {
  try { return JSON.parse(data) }
  catch { return data }
}

function _formatHttpError(payload: unknown, fallback: string): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    return JSON.stringify((payload as { detail: unknown }).detail)
  }
  return fallback
}
