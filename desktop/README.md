# NexusAgent — Desktop

Electron wrapper around the React frontend. Ships with:

- Single-instance lock (second launch focuses the running window)
- System tray icon + context menu
- Global hotkey (`Cmd/Ctrl+Shift+N`) to toggle the window from anywhere
- Native OS notifications via IPC from the renderer
- Ollama detection + lightweight model manager
- Hardened `webPreferences` (no node integration, context-isolated preload)

## Install

From this folder:

```bash
npm install
```

You also need the FastAPI backend and Ollama running separately:

```bash
# Terminal 1 — backend
cd ..
uvicorn api.server:app --reload

# Terminal 2 — Ollama (one-time install from https://ollama.com/download)
ollama serve
```

## Dev

Runs against the Vite dev server at `http://localhost:5173`:

```bash
# Terminal 1 — Vite dev server
cd ../frontend
npm run dev

# Terminal 2 — Electron
cd ../desktop
npm run dev
```

## Production build

Bundles the React frontend + packages a native installer:

```bash
# Build the frontend first so the installer has something to ship
npm run build:frontend

# Then package for your OS
npm run dist:win      # Windows — NSIS installer
npm run dist:mac      # macOS — DMG
npm run dist:linux    # Linux — AppImage + .deb
```

Output lands in `dist/`.

## Code signing (follow-up)

The `package.json` build config disables macOS Gatekeeper assessment and
hardened runtime by default — unsigned builds will show the usual
"unidentified developer" warning on first run.

To sign later:

- **macOS**: Apple Developer ID (paid account), set `CSC_LINK` + `CSC_KEY_PASSWORD`
  env vars before `npm run dist:mac`
- **Windows**: EV code-signing certificate, set `WIN_CSC_LINK` + `WIN_CSC_KEY_PASSWORD`

See `electron-builder` docs: https://www.electron.build/code-signing

## Assets

The following files are expected but not checked in:

- `assets/icon.png`  — 512×512 base icon
- `assets/icon.ico`  — Windows icon
- `assets/icon.icns` — macOS icon bundle
- `assets/tray.png`  — 32×32 monochrome tray icon

Generate them from your brand SVG before the first `npm run dist`.

## Architecture

```
main.js        — main process entry; window + tray + IPC + lifecycle
preload.js     — secure bridge: exposes window.nexus to the renderer
tray.js        — builds the tray context menu (polls /api/health every 30s)
hotkey.js      — registers Cmd/Ctrl+Shift+N
ollama.js      — detects Ollama, lists / pulls / deletes models via :11434
```

The renderer is the same React app that runs in the browser; it detects
Electron via `window.nexus?.isDesktop` and can fire native notifications
through `window.nexus.notify({ title, body })`.

## What's deliberately NOT in this release

- **Auto-spawning the Python backend** — requires a PyInstaller bundle;
  follow-up work. Users start `uvicorn` themselves for now.
- **Auto-update** — hook is in place via electron-builder; needs a release
  feed URL before enabling.
- **Code signing** — documented above; needs paid certificates.

These are tracked in the Phase 5 block of `docs/NEXUSAGENT_COMPLETE_ROADMAP.md`.
