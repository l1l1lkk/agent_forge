import { ipcMain, BrowserWindow, dialog, shell, app } from "electron";
import path, { join } from "path";
import { spawn } from "child_process";
import http from "http";
import Store from "electron-store";
import __cjs_mod__ from "node:module";
const __filename = import.meta.filename;
const __dirname = import.meta.dirname;
const require2 = __cjs_mod__.createRequire(import.meta.url);
const DAEMON_HOST = "127.0.0.1";
const DAEMON_PORT = 8765;
class DaemonManager {
  constructor() {
    this.proc = null;
    this.logBuffer = [];
    this.maxLogLines = 500;
  }
  /** Check if the daemon is responding. */
  async isHealthy() {
    try {
      const result = await this._get("/api/health");
      if (result && result.status === "ok") {
        return result;
      }
    } catch {
    }
    return null;
  }
  /** Start the forge daemon. Returns true on success. */
  async start() {
    const existing = await this.isHealthy();
    if (existing) {
      this._log(`Daemon already running (v${existing.version})`);
      return true;
    }
    this._log("Starting forge daemon...");
    const cmd = process.platform === "win32" ? "forge" : "forge";
    const args = ["serve", "--host", DAEMON_HOST, "--port", String(DAEMON_PORT)];
    this.proc = spawn(cmd, args, {
      cwd: path.resolve(__dirname, "..", "..", ".."),
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PYTHONUNBUFFERED: "1" }
    });
    this.proc.stdout?.on("data", (data) => {
      this._log(data.toString());
    });
    this.proc.stderr?.on("data", (data) => {
      this._log(`[stderr] ${data.toString()}`);
    });
    this.proc.on("exit", (code) => {
      this._log(`Daemon exited with code ${code}`);
      this.proc = null;
    });
    this.proc.on("error", (err) => {
      this._log(`Daemon error: ${err.message}`);
      this.proc = null;
    });
    return this._waitForHealth(15e3);
  }
  /** Stop the daemon. */
  async stop() {
    if (!this.proc) {
      this._log("Daemon not running");
      return;
    }
    this._log("Stopping daemon...");
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        if (this.proc) {
          this.proc.kill("SIGKILL");
          this.proc = null;
        }
        resolve();
      }, 5e3);
      if (this.proc) {
        this.proc.on("exit", () => {
          clearTimeout(timeout);
          this.proc = null;
          this._log("Daemon stopped");
          resolve();
        });
        this.proc.kill("SIGTERM");
      } else {
        clearTimeout(timeout);
        resolve();
      }
    });
  }
  /** Restart the daemon. */
  async restart() {
    await this.stop();
    await new Promise((r) => setTimeout(r, 500));
    return this.start();
  }
  /** Get diagnostic logs. */
  getLogs() {
    return [...this.logBuffer];
  }
  /** Get daemon info (host/port). */
  getInfo() {
    return { host: DAEMON_HOST, port: DAEMON_PORT };
  }
  // ── private ────────────────────────────────────────────────
  _log(msg) {
    const line = `[${(/* @__PURE__ */ new Date()).toISOString()}] ${msg.trim()}`;
    this.logBuffer.push(line);
    if (this.logBuffer.length > this.maxLogLines) {
      this.logBuffer.shift();
    }
    console.log(`[DaemonManager] ${msg.trim()}`);
  }
  async _get(path2) {
    return new Promise((resolve, reject) => {
      const req = http.get(
        `http://${DAEMON_HOST}:${DAEMON_PORT}${path2}`,
        { timeout: 3e3 },
        (res) => {
          let data = "";
          res.on("data", (chunk) => data += chunk);
          res.on("end", () => {
            try {
              resolve(JSON.parse(data));
            } catch {
              resolve(null);
            }
          });
        }
      );
      req.on("error", reject);
      req.on("timeout", () => {
        req.destroy();
        reject(new Error("timeout"));
      });
    });
  }
  async _waitForHealth(timeoutMs) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 500));
      const health = await this.isHealthy();
      if (health) {
        this._log(`Daemon healthy (v${health.version})`);
        return true;
      }
    }
    this._log("Daemon failed to start within timeout");
    return false;
  }
}
const defaults = {
  mode: "local",
  local: {
    host: "127.0.0.1",
    port: 8765,
    autoStart: true,
    authToken: ""
  },
  remotes: [],
  ui: {
    theme: "dark"
  }
};
const configStore = new Store({
  name: "config",
  defaults
});
function getConfig() {
  return configStore.store;
}
function setConfig(partial) {
  configStore.set(partial);
}
function getLocalConfig() {
  return configStore.get("local");
}
const daemon$1 = new DaemonManager();
function registerIpcHandlers() {
  const { host, port } = daemon$1.getInfo();
  ipcMain.handle("daemon:health", async () => {
    return daemon$1.isHealthy();
  });
  ipcMain.handle("daemon:start", async () => {
    return daemon$1.start();
  });
  ipcMain.handle("daemon:stop", async () => {
    await daemon$1.stop();
  });
  ipcMain.handle("daemon:restart", async () => {
    return daemon$1.restart();
  });
  ipcMain.handle("daemon:logs", async () => {
    return daemon$1.getLogs();
  });
  ipcMain.handle("daemon:info", async () => {
    return daemon$1.getInfo();
  });
  ipcMain.handle("api:get", async (_event, apiPath) => {
    return _httpGet(`http://${host}:${port}${apiPath}`);
  });
  ipcMain.handle("api:post", async (_event, apiPath, body) => {
    return _httpPost(`http://${host}:${port}${apiPath}`, body);
  });
  ipcMain.handle("dialog:selectFolder", async () => {
    const win = BrowserWindow.getFocusedWindow();
    if (!win) return null;
    const result = await dialog.showOpenDialog(win, {
      properties: ["openDirectory"]
    });
    return result.canceled ? null : result.filePaths[0] || null;
  });
  ipcMain.handle("shell:openExternal", async (_event, url) => {
    await shell.openExternal(url);
  });
  ipcMain.handle("shell:openPath", async (_event, filePath) => {
    shell.openPath(filePath);
  });
  ipcMain.handle("config:get", async () => {
    return getConfig();
  });
  ipcMain.handle("config:set", async (_event, partial) => {
    setConfig(partial);
  });
  ipcMain.handle("config:getLocal", async () => {
    return getLocalConfig();
  });
}
function _httpGet(url) {
  return new Promise((resolve, reject) => {
    http.get(url, { timeout: 1e4 }, (res) => {
      let data = "";
      res.on("data", (chunk) => data += chunk);
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve(data);
        }
      });
    }).on("error", reject);
  });
}
function _httpPost(url, body) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(body || {});
    const req = http.request(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": String(Buffer.byteLength(postData)) },
      timeout: 1e4
    }, (res) => {
      let data = "";
      res.on("data", (chunk) => data += chunk);
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve(data);
        }
      });
    });
    req.on("error", reject);
    req.write(postData);
    req.end();
  });
}
let mainWindow = null;
const daemon = new DaemonManager();
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: "Agent Forge Desktop",
    backgroundColor: "#0f0f1a",
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL);
  } else {
    mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
  }
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}
app.whenReady().then(async () => {
  registerIpcHandlers();
  createWindow();
  const config = getLocalConfig();
  if (config.autoStart) {
    console.log("[Main] Auto-starting daemon...");
    const started = await daemon.start();
    console.log(`[Main] Daemon start: ${started ? "success" : "failed"}`);
  }
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
app.on("before-quit", async () => {
  await daemon.stop();
});
