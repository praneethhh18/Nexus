/**
 * NexusAgent preload — the only bridge between the sandboxed renderer and
 * the Node-capable main process.
 *
 * Exposes a deliberately tiny surface on window.nexus so the renderer code
 * stays portable: the same calls fall back to no-ops when running in a
 * plain browser (where `window.nexus` is undefined).
 */
'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('nexus', {
  /** Fire a native OS notification. Returns {ok, error?}. */
  notify(payload) {
    return ipcRenderer.invoke('nexus:notify', payload || {});
  },
  /** Check whether a local Ollama daemon is reachable. */
  probeOllama() {
    return ipcRenderer.invoke('nexus:ollama/probe');
  },
  /** Open a URL in the user's default browser (never in an Electron webview). */
  openExternal(url) {
    return ipcRenderer.invoke('nexus:open-external', url);
  },
  /** True when running inside the Electron desktop app. */
  isDesktop: true,
});
