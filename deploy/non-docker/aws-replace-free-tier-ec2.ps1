param(
  [string]$Region = "ap-south-1",
  [string]$OldInstanceId = "i-0234c15417e801b14",
  [string]$InstanceType = "t3.micro",
  [string]$KeyName = "nexusagent-free-tier",
  [string]$InstanceName = "nexusagent-prod-replacement",
  [string]$InstanceProfileName = "nexusagent-ssm-ec2-profile",
  [string]$AllocationId = ""
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

Write-Host "Checking AWS credentials..."
$identity = Invoke-Aws sts get-caller-identity --region $Region | ConvertFrom-Json
Write-Host "Using AWS account: $($identity.Account)"

Write-Host "Reading old instance networking..."
$old = Invoke-Aws ec2 describe-instances `
  --region $Region `
  --instance-ids $OldInstanceId `
  --query "Reservations[0].Instances[0].{SubnetId:SubnetId,SecurityGroupId:SecurityGroups[0].GroupId,PublicIp:PublicIpAddress}" `
  --output json | ConvertFrom-Json

if (-not $old.SubnetId -or -not $old.SecurityGroupId) {
  throw "Could not read subnet/security group from $OldInstanceId"
}

if (-not $AllocationId) {
  if (-not $old.PublicIp) {
    throw "Old instance has no public IP. Pass -AllocationId explicitly."
  }

  $AllocationId = Invoke-Aws ec2 describe-addresses `
    --region $Region `
    --public-ips $old.PublicIp `
    --query "Addresses[0].AllocationId" `
    --output text
}

if (-not $AllocationId -or $AllocationId -eq "None") {
  throw "Could not find Elastic IP allocation id."
}

Write-Host "Finding latest Ubuntu 24.04 AMI in $Region..."
$amiId = Invoke-Aws ec2 describe-images `
  --region $Region `
  --owners 099720109477 `
  --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" "Name=architecture,Values=x86_64" "Name=virtualization-type,Values=hvm" `
  --query "Images | sort_by(@, &CreationDate)[-1].ImageId" `
  --output text

if (-not $amiId -or $amiId -eq "None") {
  throw "Could not find Ubuntu AMI in $Region"
}

$userDataPath = Join-Path $env:TEMP "nexusagent-replacement-user-data.sh"
@'
#!/usr/bin/env bash
set -euxo pipefail

if [[ ! -f /swapfile ]]; then
  fallocate -l 4G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=4096
  chmod 600 /swapfile
  mkswap /swapfile
fi

swapon /swapfile || true
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
sysctl vm.swappiness=20
grep -q '^vm.swappiness=20' /etc/sysctl.conf || echo 'vm.swappiness=20' >> /etc/sysctl.conf

snap start amazon-ssm-agent || systemctl restart snap.amazon-ssm-agent.amazon-ssm-agent.service || true
'@ | Set-Content -Path $userDataPath -Encoding ascii

Write-Host "Launching replacement EC2 $InstanceType with first-boot swap..."
$newInstanceId = Invoke-Aws ec2 run-instances `
  --region $Region `
  --image-id $amiId `
  --instance-type $InstanceType `
  --key-name $KeyName `
  --subnet-id $old.SubnetId `
  --security-group-ids $old.SecurityGroupId `
  --iam-instance-profile "Name=$InstanceProfileName" `
  --user-data "file://$userDataPath" `
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3,DeleteOnTermination=true}" `
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$InstanceName}]" `
  --query "Instances[0].InstanceId" `
  --output text

Write-Host "New instance: $newInstanceId"
Invoke-Aws ec2 wait instance-running --region $Region --instance-ids $newInstanceId | Out-Null

Write-Host "Moving Elastic IP allocation $AllocationId to replacement instance..."
Invoke-Aws ec2 associate-address `
  --region $Region `
  --allocation-id $AllocationId `
  --instance-id $newInstanceId `
  --allow-reassociation | Out-Null

$publicIp = Invoke-Aws ec2 describe-addresses `
  --region $Region `
  --allocation-ids $AllocationId `
  --query "Addresses[0].PublicIp" `
  --output text

Write-Host ""
Write-Host "Replacement EC2 is ready for bootstrap."
Write-Host "Old instance : $OldInstanceId"
Write-Host "New instance : $newInstanceId"
Write-Host "Elastic IP   : $publicIp"
Write-Host ""
Write-Host "Wait for SSM online:"
Write-Host "  aws ssm describe-instance-information --region $Region --query `"InstanceInformationList[?InstanceId=='$newInstanceId']`""
Write-Host ""
Write-Host "Then run:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\deploy\non-docker\aws-run-bootstrap-ssm.ps1 -Region $Region -InstanceId $newInstanceId -SkipCertbot"
Write-Host ""
Write-Host "Do not terminate the old instance until the replacement is verified."
