# AWS Free-Tier Deployment

This is the cheapest practical AWS shape for NexusAgent without Docker.

## What To Use

Use one small Ubuntu EC2 instance for:

- FastAPI backend
- product frontend static files
- landing static files
- WhatsApp bridge
- nginx + HTTPS
- local PostgreSQL

This avoids paying for separate load balancers, ECS, NAT gateways, and extra managed services. It is not the most scalable setup, but it is the best fit for "free/credits first".

AWS currently describes the new Free Tier as up to `$200` credits over 6 months for new accounts. RDS PostgreSQL free-plan usage is listed for eligible `db.t3.micro` / `db.t4g.micro`, but the cheapest deployment is still usually local Postgres on the EC2 box until traffic grows.

Sources:

- https://aws.amazon.com/free/
- https://aws.amazon.com/rds/free/

## Recommended EC2

Start with:

- Ubuntu 22.04 or 24.04
- `t3.micro` or `t4g.micro`
- 20-30 GB gp3 EBS
- Security group inbound: `22`, `80`, `443`

Important: `t4g.micro` is ARM. It can be cheaper, but some Python wheels can be fussier. If you want fewer install surprises, use `t3.micro`.

## DNS

Create A records pointing to the EC2 public IP:

```text
nexusagent.in
www.nexusagent.in
nexus.nexusagent.in
vox.nexusagent.in
```

## Bootstrap

SSH to the EC2 instance, then:

```bash
git clone https://github.com/praneethhh18/Nexus.git /opt/nexusagent
cd /opt/nexusagent
export LETSENCRYPT_EMAIL="you@example.com"
bash deploy/non-docker/aws-free-tier-bootstrap.sh
```

If the repo is private, clone it manually with your GitHub credentials first, then run the script from `/opt/nexusagent`.

## NexusCaller

The bootstrap clones NexusCaller into `/opt/nexuscaller-lab` and installs two services:

```bash
sudo systemctl status nexus-vox-server
sudo systemctl status nexus-vox-worker
```

`nexus-vox-server` must listen on `127.0.0.1:8765`; nginx proxies `vox.nexusagent.in` to that port. NexusAgent expects:

```env
LAB_URL=http://127.0.0.1:8765
VOX_PUBLIC_URL=https://vox.nexusagent.in
NEXUS_PUBLIC_URL=https://nexus.nexusagent.in
VOICE_CALLBACK_SECRET=<same secret in both repos>
```

Fill `/opt/nexuscaller-lab/.env` with the LiveKit/Twilio/STT/TTS/LLM keys required by NexusCaller, then restart:

```bash
sudo systemctl restart nexus-vox-server nexus-vox-worker nginx
```

## Smoke Checks

```bash
curl https://nexus.nexusagent.in/api/ready
curl https://nexus.nexusagent.in/api/health
```

For logs:

```bash
sudo journalctl -u nexus-api -f
sudo journalctl -u nexus-whatsapp -f
sudo journalctl -u nexus-vox-server -f
sudo journalctl -u nexus-vox-worker -f
sudo tail -f /var/log/nginx/error.log
```

## Cost Guardrails

Set AWS Billing alerts immediately:

- AWS Budgets: monthly budget `$1`
- Alert at 50%, 80%, 100%
- Keep only ports `22`, `80`, `443` open
- Avoid NAT Gateway, ALB, ECS/Fargate, CloudWatch high-volume logs, and oversized RDS

For real users, move Postgres to RDS later. For first launch, local Postgres is enough and keeps the bill tiny.
