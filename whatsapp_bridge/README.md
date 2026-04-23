# NexusAgent WhatsApp Bridge

Open-source WhatsApp bot for NexusAgent using [Baileys](https://github.com/WhiskeySockets/Baileys).
No Twilio, no Meta business verification, no paid API — just your own phone linked
as a "WhatsApp Web" device.

## What it does

- Listens for incoming WhatsApp messages on a phone number you control
- Forwards each message to your NexusAgent backend (`/api/whatsapp/inbound`)
- Sends the agent's reply back over WhatsApp, including PDF / .docx attachments
- Only handles 1-to-1 chats (ignores groups & broadcasts)

## Setup

### 1. Install Node dependencies

```bash
cd whatsapp_bridge
npm install
```

### 2. Configure `.env`

```bash
cp .env.example .env
```

Open `.env` and set `NEXUS_WEBHOOK_SECRET`. Get the secret by:
- **Web UI**: Log into NexusAgent as an **admin** user → *Settings → WhatsApp → Copy bridge secret*
- **Or**: read `data/.whatsapp_secret` in the repo root (auto-generated on first backend run)

### 3. Start the bridge

```bash
npm start
```

The first time you run it, you'll see a QR code in your terminal. On your phone:

1. Open WhatsApp
2. Settings → Linked Devices → Link a Device
3. Scan the QR

After that, the bridge runs silently and forwards messages. Session is cached in `./auth/`.

### 4. Link your NexusAgent account to your phone number

1. In NexusAgent web UI, go to *Settings → WhatsApp*
2. Click *Generate link code*
3. From the phone you want to use, text that 6-character code to the WhatsApp number running the bridge
4. You're linked — try asking the bot "what are my tasks today?"

## Commands

Once linked, any free-text message goes straight to the agent. A few built-ins:

- `help` — show what the bot can do
- `/business` — list businesses you belong to
- `/business Acme` — switch active business for this phone
- `/unlink` — disconnect this phone

## How security works

- The backend only accepts inbound messages with the right `X-Nexus-Secret` header. Anyone else hitting `/api/whatsapp/inbound` gets a 401.
- Phones aren't authenticated by phone number alone — they must send a one-time link code issued from your web login.
- Every action (emails, deletions, invoices) still goes through the **Approvals queue** — the WhatsApp agent cannot autonomously do anything irreversible without your OK on the web UI.
- Attachments the bridge downloads from `/api/whatsapp/attachment` are constrained to `outputs/` on the server. You can't exfiltrate arbitrary files by asking the bot politely.

## Troubleshooting

| Problem | Fix |
|---|---|
| `NEXUS_WEBHOOK_SECRET is required` | Set it in `.env` from the web UI |
| QR keeps disappearing | Your phone timed out; just run `npm start` again |
| `Couldn't reach the NexusAgent backend` | Backend isn't running on `NEXUS_API_URL` |
| Want to switch phone | Delete `whatsapp_bridge/auth/`, restart, scan new QR |
| Logged out unexpectedly | Scan QR again. If it keeps happening, don't leave more than one device paired as a "NexusAgent" client |

## Limits

- Baileys is an unofficial WhatsApp Web client. Meta can theoretically ban the phone, but for low-volume personal assistant use this is very rare.
- WhatsApp messages are capped at 4096 characters. Long answers are truncated with a "full answer on the web UI" note.
- Voice messages aren't processed yet (v1 is text-only).
- Groups and broadcasts are intentionally ignored to avoid leaking business data into shared chats.
