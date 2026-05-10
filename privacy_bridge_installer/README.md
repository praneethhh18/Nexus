# NexusAgent Privacy Bridge

Run this on **your laptop** to enable Privacy Mode in your NexusAgent
account. Sensitive AI prompts (anything touching customer data, contact
records, transcripts) will be computed on YOUR machine instead of cloud
LLMs — your data never leaves your laptop.

## Why use it

| | Standard (cloud) | Privacy Bridge |
|---|---|---|
| Where reasoning happens | Bedrock / NVIDIA cloud | **Your laptop's Ollama** |
| Customer data leaves your laptop | Yes (PII redacted) | **No** |
| Speed | ~800ms | ~2-10s (depends on your CPU) |
| Cost to NexusAgent | Per-token | None |
| Tier required | Free / Starter | Privacy / Business |

## One-time setup (5 min)

### 1. Install Ollama
- Mac: `brew install ollama` or download from https://ollama.com/download
- Windows: download installer from https://ollama.com/download
- Linux: `curl -fsSL https://ollama.com/install.sh | sh`

After install, Ollama runs as a service on `http://localhost:11434`.

### 2. Pull a model
```
ollama pull llama3.1:8b
```
(~5 GB download, takes 5-15 min depending on internet)

### 3. Install Cloudflare Tunnel (free, no account needed)
- Mac: `brew install cloudflared`
- Windows: download from https://github.com/cloudflare/cloudflared/releases
- Linux: see https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

Verify: `cloudflared --version`

### 4. Get your token
1. Open `https://app.nexusagent.in` → **Settings** → **Privacy Mode**
2. Click **Generate Bridge Token**
3. Copy the token (starts with `pb_`)

## Run the bridge

In a terminal:
```
node bridge.js --token pb_YOUR_TOKEN --base https://app.nexusagent.in
```

You'll see something like:
```
[bridge] checking Ollama...
[bridge] ✓ Ollama ok, 1 model(s) available
[bridge] starting Cloudflare Tunnel → http://127.0.0.1:11434
[bridge] ✓ tunnel up: https://random-name.trycloudflare.com
[bridge] registering with https://app.nexusagent.in/api/privacy-bridge/register
[bridge] ✓ registered. status: healthy

─────────────────────────────────────────────────────────
Privacy Bridge is live.
  Tunnel : https://random-name.trycloudflare.com
  Models : llama3.1:8b
  Status : healthy
```

**Keep this terminal open.** Closing it disconnects the bridge — sensitive
prompts will silently fall back to cloud-with-PII-redaction.

## What "sensitive prompts" means

Currently routed through your bridge:
- Drafting email replies that include customer names, phone, email
- Summarising voice call transcripts
- Generating contact memory facts
- SQL-querying your CRM data ("show me overdue invoices")

NOT routed (handled by cloud with redaction):
- Real-time voice synthesis (TTS) — needs cloud streaming
- Real-time speech-to-text (STT) — needs cloud streaming
- Anonymous routing decisions

## Troubleshooting

**`cloudflared: command not found`**
- Install Cloudflare Tunnel — see step 3 above.

**`Ollama not reachable at http://127.0.0.1:11434`**
- Run `ollama serve` (or restart the Ollama desktop app).

**`token not recognised`**
- Tokens are single-use until rotated. Generate a fresh one in Settings.

**`[bridge] ⚠ initial health check warning: ...`**
- The SaaS server tried to ping your tunnel and got an error. Check that
  Ollama is running and the cloudflared URL works in a browser.

## Running it as a background service

The CLI works for testing. For permanent privacy mode:

### macOS — launchd
Create `~/Library/LaunchAgents/in.nexusagent.privacy-bridge.plist`. See
the [launchd docs](https://www.launchd.info/) for the exact XML.

### Linux — systemd
```ini
# /etc/systemd/system/nexusagent-privacy-bridge.service
[Unit]
Description=NexusAgent Privacy Bridge
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/privacy_bridge_installer
ExecStart=/usr/bin/node bridge.js --token pb_YOUR_TOKEN --base https://app.nexusagent.in
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl enable --now nexusagent-privacy-bridge
```

### Windows — Task Scheduler
Create a basic task: trigger "At log on", action `node bridge.js --token ...`.

## Polished installer (Electron tray app)

The same code now ships as a one-click installer that lives in your system
tray — no terminal needed.

### Build

```
cd privacy_bridge_installer
npm install
npm run dist        # current OS only
npm run dist:win    # Windows .exe (NSIS one-click)
npm run dist:mac    # macOS .dmg (universal binary)
npm run dist:linux  # AppImage + .deb
```

Output lands in `dist/`. Copy the artifact onto your laptop, double-click,
done — the app installs itself, lives in the tray, runs at login.

### Bundling cloudflared (optional but recommended)

To make the installer truly zero-dependency, drop the cloudflared binary
into `bin/<os>/<arch>/` before building:

```
bin/win32/x64/cloudflared.exe
bin/darwin/x64/cloudflared
bin/darwin/arm64/cloudflared
bin/linux/x64/cloudflared
```

`electron-builder` ships the right binary for the target platform via
`extraResources`. If absent, the app falls back to `cloudflared` on PATH and
opens the download page in the user's browser if missing.

### What the user sees

1. Double-click the installer.
2. App installs silently, opens a tiny setup window asking for the bridge
   token.
3. They paste the token from `app.nexusagent.in → Settings → Privacy Mode`.
4. Window closes. A coloured dot appears in the system tray:
   - 🟢 green — registered + healthy
   - 🔵 blue — tunnel up, registering
   - 🟡 yellow — starting / waiting on Ollama
   - 🔴 red — needs setup or bridge down
5. App auto-starts at login. They never see a terminal.
