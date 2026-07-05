# NexusAgent Non-Docker Deployment

This is the deployment path when you do not want Docker.

## Domains

- `nexusagent.in` -> landing page (`landing/dist`)
- `www.nexusagent.in` -> landing page (`landing/dist`)
- `nexus.nexusagent.in` -> product frontend (`frontend/dist`) and backend `/api`
- `vox.nexusagent.in` -> NexusCaller/Vox server

## Server Assumption

Ubuntu 22.04/24.04 VPS with ports 80 and 443 open.

Install base packages:

```bash
sudo apt update
sudo apt install -y git nginx certbot python3-certbot-nginx python3.12-venv python3-pip nodejs npm postgresql postgresql-contrib
```

Use `/opt/nexusagent` for this repo:

```bash
sudo mkdir -p /opt/nexusagent
sudo chown -R ubuntu:ubuntu /opt/nexusagent
git clone <your-repo-url> /opt/nexusagent
cd /opt/nexusagent
```

## Backend

```bash
cd /opt/nexusagent
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
cp deploy/non-docker/production.env.example .env
nano .env
```

Set at minimum:

- `DATABASE_URL`
- `JWT_SECRET`
- `APP_BASE_URL=https://nexus.nexusagent.in`
- `NEXUS_PUBLIC_URL=https://nexus.nexusagent.in`
- `VOICE_CALLBACK_SECRET`
- `WHATSAPP_WEBHOOK_SECRET`

Apply migrations:

```bash
./venv/bin/python -m db.migrate
```

Install the service:

```bash
sudo cp deploy/non-docker/nexus-api.service /etc/systemd/system/nexus-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now nexus-api
sudo journalctl -u nexus-api -f
```

## Frontends

Build landing:

```bash
cd /opt/nexusagent/landing
npm ci
npm run build
```

Build product frontend:

```bash
cd /opt/nexusagent/frontend
npm ci
npm run build
```

## WhatsApp Bridge

```bash
cd /opt/nexusagent/whatsapp_bridge
npm ci
cp ../deploy/non-docker/whatsapp.env.example .env
nano .env
```

Set `NEXUS_WEBHOOK_SECRET` to the same value as `WHATSAPP_WEBHOOK_SECRET` in `/opt/nexusagent/.env`.

Install service:

```bash
sudo cp /opt/nexusagent/deploy/non-docker/nexus-whatsapp.service /etc/systemd/system/nexus-whatsapp.service
sudo systemctl daemon-reload
sudo systemctl enable --now nexus-whatsapp
sudo journalctl -u nexus-whatsapp -f
```

The first run needs QR pairing. Read the service logs and scan the QR with WhatsApp Linked Devices.

## Nginx And HTTPS

Point DNS A records to the VPS IP:

```text
nexusagent.in
www.nexusagent.in
nexus.nexusagent.in
vox.nexusagent.in
```

Install nginx config:

```bash
sudo cp /opt/nexusagent/deploy/non-docker/nginx-nexusagent.conf /etc/nginx/sites-available/nexusagent
sudo ln -sf /etc/nginx/sites-available/nexusagent /etc/nginx/sites-enabled/nexusagent
sudo nginx -t
sudo systemctl reload nginx
```

Issue certificates:

```bash
sudo certbot --nginx \
  -d nexusagent.in \
  -d www.nexusagent.in \
  -d nexus.nexusagent.in \
  -d vox.nexusagent.in
```

## NexusCaller / Vox

Run NexusCaller separately on `127.0.0.1:8765`, following the NexusCaller repo's setup.

NexusAgent expects:

```env
LAB_URL=http://127.0.0.1:8765
VOX_PUBLIC_URL=https://vox.nexusagent.in
NEXUS_PUBLIC_URL=https://nexus.nexusagent.in
VOICE_CALLBACK_SECRET=<same value in both repos>
```

## Smoke Checks

```bash
curl https://nexus.nexusagent.in/api/health
curl https://nexus.nexusagent.in/api/ready
curl https://vox.nexusagent.in/health
```

Then test in browser:

- `https://nexusagent.in`
- `https://nexus.nexusagent.in`
- Settings -> WhatsApp connect
- CRM contact -> Vox call
