/**
 * Preload script for the setup window.
 *
 * Exposes a narrow API surface to the renderer (setup.html / setup.js) over
 * Electron's contextBridge. The renderer never gets `require`, `process`,
 * or any direct Node access — all privileged work goes through these
 * named IPC channels (handled in main.js).
 *
 * Renderer code uses:
 *   window.bridge.settingsLoad()
 *   window.bridge.settingsSave({...})
 *   window.bridge.bridgeRestart()
 *   window.bridge.ollamaProbe()
 *   window.bridge.ollamaPull(modelName)
 */
'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('bridge', {
  settingsLoad:   ()         => ipcRenderer.invoke('settings:load'),
  settingsSave:   (payload)  => ipcRenderer.invoke('settings:save', payload),
  bridgeRestart:  ()         => ipcRenderer.invoke('bridge:restart'),
  ollamaProbe:    ()         => ipcRenderer.invoke('ollama:probe'),
  ollamaPull:     (model)    => ipcRenderer.invoke('ollama:pull', model),
});
