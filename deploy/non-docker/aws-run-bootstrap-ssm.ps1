param(
  [string]$Region = "ap-south-1",
  [string]$InstanceId = "i-0234c15417e801b14",
  [string]$Bucket = "nexusagent-deploy-111200748322-ap-south-1",
  [string]$Key = "nexusagent-src.tgz",
  [string]$LetsEncryptEmail = "admin@nexusagent.in",
  [switch]$SkipCertbot
)

$ErrorActionPreference = "Stop"

function Invoke-Aws {
  param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
  )

  $output = & aws @Args
  if ($LASTEXITCODE -ne 0) {
    throw "aws $($Args -join ' ') failed"
  }
  return $output
}

$url = Invoke-Aws s3 presign "s3://$Bucket/$Key" --region $Region --expires-in 3600
$skipValue = if ($SkipCertbot) { "1" } else { "0" }

$commands = @(
  "set -e",
  "mkdir -p /opt/nexusagent",
  "curl -fL '$url' -o /tmp/nexusagent-src.tgz",
  "rm -rf /opt/nexusagent/*",
  "tar -xzf /tmp/nexusagent-src.tgz -C /opt/nexusagent",
  "chown -R ubuntu:ubuntu /opt/nexusagent",
  "chmod -R u+rwX /opt/nexusagent",
  "cd /opt/nexusagent",
  "SKIP_CERTBOT=$skipValue LETSENCRYPT_EMAIL=$LetsEncryptEmail bash deploy/non-docker/aws-free-tier-bootstrap.sh"
)

$input = @{
  DocumentName = "AWS-RunShellScript"
  InstanceIds = @($InstanceId)
  Comment = "nexusagent-bootstrap"
  TimeoutSeconds = 7200
  Parameters = @{
    commands = $commands
  }
}

$inputFile = Join-Path $env:TEMP "nexusagent-ssm-bootstrap.json"
$input | ConvertTo-Json -Depth 6 | Set-Content -Path $inputFile -Encoding ascii

Invoke-Aws ssm send-command `
  --region $Region `
  --cli-input-json "file://$inputFile" `
  --query Command.CommandId `
  --output text
