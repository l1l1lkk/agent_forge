/**
 * Electron main process entry point.
 *
 * Creates the BrowserWindow, starts the daemon, registers IPC handlers.
 */

import { app, BrowserWindow } from 'electron'
import { join } from 'path'
import { registerIpcHandlers } from './ipc'
import { daemon } from './daemonSingleton'
import { getLocalConfig } from './configStore'

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'Agent Forge Desktop',
    backgroundColor: '#0f0f1a',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // Load renderer
  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// Auto-start daemon on app ready
app.whenReady().then(async () => {
  registerIpcHandlers()
  createWindow()

  const config = getLocalConfig()
  if (config.autoStart) {
    console.log('[Main] Auto-starting daemon...')
    const started = await daemon.start()
    console.log(`[Main] Daemon start: ${started ? 'success' : 'failed'}`)
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', async () => {
  await daemon.stop()
})
