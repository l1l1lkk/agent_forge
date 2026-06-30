import { contextBridge, ipcRenderer } from "electron";
const forgeDesktop = {
  daemon: {
    health: () => ipcRenderer.invoke("daemon:health"),
    start: () => ipcRenderer.invoke("daemon:start"),
    stop: () => ipcRenderer.invoke("daemon:stop"),
    restart: () => ipcRenderer.invoke("daemon:restart"),
    logs: () => ipcRenderer.invoke("daemon:logs"),
    info: () => ipcRenderer.invoke("daemon:info")
  },
  api: {
    get: (path) => ipcRenderer.invoke("api:get", path),
    post: (path, body) => ipcRenderer.invoke("api:post", path, body),
    delete: (path) => ipcRenderer.invoke("api:delete", path)
  },
  dialog: {
    selectFolder: () => ipcRenderer.invoke("dialog:selectFolder")
  },
  shell: {
    openExternal: (url) => ipcRenderer.invoke("shell:openExternal", url),
    openPath: (filePath) => ipcRenderer.invoke("shell:openPath", filePath)
  },
  config: {
    get: () => ipcRenderer.invoke("config:get"),
    set: (partial) => ipcRenderer.invoke("config:set", partial),
    getLocal: () => ipcRenderer.invoke("config:getLocal")
  }
};
contextBridge.exposeInMainWorld("forgeDesktop", forgeDesktop);
