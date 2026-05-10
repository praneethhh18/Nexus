# AWS Cost Safety — pre-deploy checklist

You have a $100 AWS credit. This doc keeps it from disappearing in a week.

## 1. Set billing alerts BEFORE provisioning anything

AWS Console → **Billing & Cost Management** → **Budgets** → **Create budget**:

| Threshold | Alert at |
|---|---|
| $5 (5% of credit) | Email — "you've started burning credit, monitor usage" |
| $25 (25% of credit) | Email — "halfway through the trial budget" |
| $50 (50% of credit) | Email + SMS — "investigate immediately" |
| $90 (90% of credit) | Email + SMS — "shut down or migrate to cheaper provider" |

Without these, you only learn about runaway cost on the next monthly bill.

## 2. Resources to NEVER enable accidentally

These auto-enabled "best practice" services drain credit silently:

| Resource | Always-on cost | Why we skip |
|---|---|---|
| **NAT Gateway** | $32/mo + data transfer | Single-instance setup uses public subnet — no NAT needed |
| **Application Load Balancer** | $22/mo | Caddy on the EC2 handles HTTPS + routing free |
| **RDS Multi-AZ** | 2× DB instance cost | Self-hosted Postgres on the EC2 instance for now |
| **CloudWatch Logs default retention** | $0.03/GB/mo, never deletes | Set 14-day retention on every log group |
| **Detached Elastic IP** | $3.60/mo per IP | Always attach EIPs to running instances; release when killing instances |
| **EBS Provisioned IOPS** | $0.065/IOPS-month | Default gp3 is plenty for our load |
| **S3 Cross-Region Replication** | 2× storage cost | Single-region is fine — backups go to S3 in same region |

## 3. Resources we DO use (and their costs)

| Resource | Monthly cost | Free tier covers? |
|---|---|---|
| EC2 t3.medium | ~$30 | No (t3.micro is free tier, but RAM is too tight) |
| EBS 30GB gp3 | ~$3 | Yes (free 30GB for 12 months) |
| Elastic IP (attached) | $0 | Yes (free while attached) |
| Route 53 hosted zone | $0.50 | No (but cheap) |
| Route 53 queries | ~$0.50/mo at low traffic | First 1B queries: $0.40/M |
| S3 (frontend + backups) | ~$0.50 | Yes (free 5GB for 12 months) |
| CloudFront | $0 at low traffic | Yes (free 1TB out + 10M HTTP requests for 12 months) |
| Data transfer out | ~$0-5 depending on volume | Yes (free 100GB/mo) |
| **Total** | **~$33/mo** | |

**Credit runway:** $100 / $33 = **~3 months** of free runway.

## 4. Per-customer cost guards (already in code)

These caps prevent ONE bad customer from blowing your provider bills:

### Cloud LLM tokens (NVIDIA / Bedrock / Groq / Claude)
File: `config/cloud_budget.py` → `CLOUD_TOKEN_DAILY_CAP`
Default: 1,000,000 tokens/business/day (generous)

**Tighten per pricing tier:**
```bash
# In production .env, override per tier — there is no per-business override
# in code yet (TODO), so the env applies to all. Set conservatively.
CLOUD_TOKEN_DAILY_CAP=500000
```

### Vox outbound calls
File: `nexuscaller-lab/voice_agent/server.py` → `VOX_DAILY_CALL_CAP`
Default: 200 calls/business/day

A single misconfigured CSV upload can no longer trigger 1,000+ Twilio calls.

### Per-IP rate limit
File: `api/reliability.py` → middleware
- Default: 120 req/min
- `/api/auth/*`: 30 req/min (slows brute-force)
- `/api/voice/*`: 20 req/min

## 5. Provider-side billing alerts (NOT AWS)

Set spending caps directly in each provider's dashboard. AWS billing alerts
WON'T catch these:

| Provider | Where | Why |
|---|---|---|
| **Twilio** | Console → Settings → Usage Triggers | Voice calls bill per minute |
| **NVIDIA NIM** | NGC → Subscription → Usage caps | LLM tokens |
| **AWS Bedrock** | CloudWatch alarm on `Bedrock` namespace | LLM tokens (separate from EC2 budget) |
| **Cartesia** | cartesia.ai → Billing → Spending limit | TTS chars/month |
| **Deepgram** | Console → Settings → Billing → Spending limit | STT minutes |
| **Resend** | resend.com → Settings → Plans | 3,000 emails/mo free, then $20/50k |
| **LiveKit Cloud** | cloud.livekit.io → Billing | Conference minutes |

**Recommended initial caps (you, on each provider):**
- Twilio: $50/mo
- NVIDIA NIM: $20/mo
- Cartesia: $25/mo
- Deepgram: $25/mo
- LiveKit: $30/mo (free tier covers a lot)

## 6. CloudWatch Logs retention (set in Terraform)

```hcl
resource "aws_cloudwatch_log_group" "nexusagent" {
  name              = "/nexusagent/app"
  retention_in_days = 14   # never use the default "Never expire"
}
```

Without this, logs accumulate forever at $0.03/GB/mo. After 6 months a
chatty app can have 50+ GB of logs costing $1.50/mo growing forever.

## 7. EBS snapshot retention

If you enable automatic EBS snapshots:

```hcl
resource "aws_dlm_lifecycle_policy" "daily_backup" {
  policy_details {
    schedule {
      retain_rule { count = 7 }  # keep last 7 only — not last 7 years
    }
  }
}
```

## 8. Pre-deploy checklist

Before running `terraform apply`:

- [ ] $100 credit confirmed in AWS Billing → Credits
- [ ] 4 billing alerts created ($5 / $25 / $50 / $90)
- [ ] Region set to `ap-south-1` (Mumbai — closest to India, no extra egress)
- [ ] No NAT Gateway in the Terraform module
- [ ] No Application Load Balancer in the Terraform module
- [ ] CloudWatch log retention set to 14 days
- [ ] Per-provider spending limits set on Twilio, NVIDIA, Cartesia, Deepgram, LiveKit
- [ ] `CLOUD_TOKEN_DAILY_CAP` set in production `.env`
- [ ] `VOX_DAILY_CALL_CAP` set in Vox lab `.env`

## 9. Monthly review (5 min)

First of every month:
1. AWS Billing → Cost Explorer → group by service
2. Anything new since last month? Either explain it or kill the resource
3. Detached EIPs? Release them
4. Old EBS snapshots? Delete if older than 30 days

## 10. Emergency shutdown

If the bill spikes unexpectedly:

```bash
# Stop the EC2 (preserves data on EBS, costs only EBS storage ~$3/mo)
aws ec2 stop-instances --instance-ids i-xxxxxx

# Or terminate (DESTROYS data — only if you have backup)
aws ec2 terminate-instances --instance-ids i-xxxxxx

# Drain S3 + delete bucket (data gone forever)
aws s3 rm s3://nexusagent-prod --recursive
aws s3 rb s3://nexusagent-prod
```

Stopping (not terminating) keeps the EC2 + data intact while bills drop to
EBS-only ($3/mo). Useful when investigating a billing issue.
