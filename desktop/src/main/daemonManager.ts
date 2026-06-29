/**
 * DaemonManager — manages forge daemon lifecycle from Electron main process.
 *
 * Responsibilities:
 *  - Health check (GET /api/health)
 *  - Auto-start forge serve if not running
 *  - Stop / restart
 *  - Capture stdout/stderr for diagnostics
 *  - Port conflict detection
 */

import { spawn, ChildProcess } from 'child_process'
import { app } from 'electron'
import http from 'http'
import path from 'path'

const DAEMON_HOST = '127.0.0.1'
const DAEMON_PORT = 8765

export interface HealthStatus {
  status: string
  version: string
  uptime?: number
}

export class DaemonManager {
  private proc: ChildProcess | null = null
  private logBuffer: string[] = []
  private maxLogLines = 500

  /** Check if the daemon is responding. */
  async isHealthy(): Promise<HealthStatus | null> {
    try {
      const result = await this._get('/api/health')
      if (result && result.status === 'ok') {
        return result as HealthStatus
      }
    } catch {
      // Daemon not running or not responding
    }
    return null
  }

  /** Start the forge daemon. Returns true on success. */
  async start(): Promise<boolean> {
    // Check if already healthy
    const existing = await this.isHealthy()
    if (existing) {
      this._log(`Daemon already running (v${existing.version})`)
      return true
    }

    this._log('Starting forge daemon...')

    // Spawn forge serve
    const cmd = process.platform === 'win32' ? 'forge' : 'forge'
    const args = ['serve', '--host', DAEMON_HOST, '--port', String(DAEMON_PORT)]

    this.proc = spawn(cmd, args, {
      cwd: path.resolve(__dirname, '..', '..', '..'),
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    })

    this.proc.stdout?.on('data', (data: Buffer) => {
      this._log(data.toString())
    })

    this.proc.stderr?.on('data', (data: Buffer) => {
      this._log(`[stderr] ${data.toString()}`)
    })

    this.proc.on('exit', (code: number | null) => {
      this._log(`Daemon exited with code ${code}`)
      this.proc = null
    })

    this.proc.on('error', (err: Error) => {
      this._log(`Daemon error: ${err.message}`)
      this.proc = null
    })

    // Wait for health check
    return this._waitForHealth(15_000)
  }

  /** Stop the daemon. */
  async stop(): Promise<void> {
    if (!this.proc) {
      this._log('Daemon not running')
      return
    }

    this._log('Stopping daemon...')

    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        if (this.proc) {
          this.proc.kill('SIGKILL')
          this.proc = null
        }
        resolve()
      }, 5000)

      if (this.proc) {
        this.proc.on('exit', () => {
          clearTimeout(timeout)
          this.proc = null
          this._log('Daemon stopped')
          resolve()
        })
        this.proc.kill('SIGTERM')
      } else {
        clearTimeout(timeout)
        resolve()
      }
    })
  }

  /** Restart the daemon. */
  async restart(): Promise<boolean> {
    await this.stop()
    // Small delay to let the port free
    await new Promise((r) => setTimeout(r, 500))
    return this.start()
  }

  /** Get diagnostic logs. */
  getLogs(): string[] {
    return [...this.logBuffer]
  }

  /** Get daemon info (host/port). */
  getInfo() {
    return { host: DAEMON_HOST, port: DAEMON_PORT }
  }

  // ── private ────────────────────────────────────────────────

  private _log(msg: string) {
    const line = `[${new Date().toISOString()}] ${msg.trim()}`
    this.logBuffer.push(line)
    if (this.logBuffer.length > this.maxLogLines) {
      this.logBuffer.shift()
    }
    console.log(`[DaemonManager] ${msg.trim()}`)
  }

  private async _get(path: string): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const req = http.get(
        `http://${DAEMON_HOST}:${DAEMON_PORT}${path}`,
        { timeout: 3000 },
        (res) => {
          let data = ''
          res.on('data', (chunk: string) => (data += chunk))
          res.on('end', () => {
            try {
              resolve(JSON.parse(data))
            } catch {
              resolve(null)
            }
          })
        }
      )
      req.on('error', reject)
      req.on('timeout', () => {
        req.destroy()
        reject(new Error('timeout'))
      })
    })
  }

  private async _waitForHealth(timeoutMs: number): Promise<boolean> {
    const deadline = Date.now() + timeoutMs
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 500))
      const health = await this.isHealthy()
      if (health) {
        this._log(`Daemon healthy (v${health.version})`)
        return true
      }
    }
    this._log('Daemon failed to start within timeout')
    return false
  }
}
