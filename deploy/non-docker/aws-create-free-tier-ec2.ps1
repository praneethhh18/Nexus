param(
  [string]$Region = "ap-south-1",
  [string]$InstanceType = "t3.micro",
  [string]$KeyName = "nexusagent-free-tier",
  [string]$SecurityGroupName = "nexusagent-web",
  [string]$InstanceName = "nexusagent-prod",
  [string]$PemPath = "C:\tmp\nexusagent-free-tier.pem"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking AWS credentials..."
$identity = aws sts get-caller-identity --region $Region | ConvertFrom-Json
Write-Host "Using AWS account: $($identity.Account)"

Write-Host "Finding latest Ubuntu 24.04 AMI in $Region..."
$amiId = aws ec2 describe-images `
  --region $Region `
  --owners 099720109477 `
  --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" "Name=architecture,Values=x86_64" "Name=virtualization-type,Values=hvm" `
  --query "Images | sort_by(@, &CreationDate)[-1].ImageId" `
  --output text

if (-not $amiId -or $amiId -eq "None") {
  throw "Could not find Ubuntu AMI in $Region"
}
Write-Host "AMI: $amiId"

$vpcId = aws ec2 describe-vpcs --region $Region --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text
if (-not $vpcId -or $vpcId -eq "None") {
  throw "No default VPC found in $Region"
}
Write-Host "Default VPC: $vpcId"

$sgId = aws ec2 describe-security-groups `
  --region $Region `
  --filters "Name=group-name,Values=$SecurityGroupName" "Name=vpc-id,Values=$vpcId" `
  --query "SecurityGroups[0].GroupId" `
  --output text

if (-not $sgId -or $sgId -eq "None") {
  Write-Host "Creating security group $SecurityGroupName..."
  $sgId = aws ec2 create-security-group `
    --region $Region `
    --group-name $SecurityGroupName `
    --description "NexusAgent web and SSH access" `
    --vpc-id $vpcId `
    --query "GroupId" `
    --output text

  aws ec2 authorize-security-group-ingress --region $Region --group-id $sgId --protocol tcp --port 22 --cidr 0.0.0.0/0 | Out-Null
  aws ec2 authorize-security-group-ingress --region $Region --group-id $sgId --protocol tcp --port 80 --cidr 0.0.0.0/0 | Out-Null
  aws ec2 authorize-security-group-ingress --region $Region --group-id $sgId --protocol tcp --port 443 --cidr 0.0.0.0/0 | Out-Null
} else {
  Write-Host "Using existing security group: $sgId"
}

if (-not (Test-Path $PemPath)) {
  Write-Host "Creating key pair $KeyName at $PemPath..."
  New-Item -ItemType Directory -Force -Path (Split-Path $PemPath) | Out-Null
  aws ec2 create-key-pair `
    --region $Region `
    --key-name $KeyName `
    --query "KeyMaterial" `
    --output text | Set-Content -NoNewline -Path $PemPath
} else {
  Write-Host "Using existing PEM file: $PemPath"
}

Write-Host "Launching EC2 $InstanceType..."
$instanceId = aws ec2 run-instances `
  --region $Region `
  --image-id $amiId `
  --instance-type $InstanceType `
  --key-name $KeyName `
  --security-group-ids $sgId `
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3,DeleteOnTermination=true}" `
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$InstanceName}]" `
  --query "Instances[0].InstanceId" `
  --output text

Write-Host "Instance: $instanceId"
aws ec2 wait instance-running --region $Region --instance-ids $instanceId

Write-Host "Allocating and associating Elastic IP..."
$allocId = aws ec2 allocate-address --region $Region --domain vpc --query "AllocationId" --output text
aws ec2 associate-address --region $Region --allocation-id $allocId --instance-id $instanceId | Out-Null

$publicIp = aws ec2 describe-addresses --region $Region --allocation-ids $allocId --query "Addresses[0].PublicIp" --output text

Write-Host ""
Write-Host "EC2 is ready."
Write-Host "Instance ID: $instanceId"
Write-Host "Elastic IP : $publicIp"
Write-Host "PEM file   : $PemPath"
Write-Host ""
Write-Host "Create these DNS A records pointing to ${publicIp}:"
Write-Host "  nexusagent.in"
Write-Host "  www.nexusagent.in"
Write-Host "  nexus.nexusagent.in"
Write-Host "  vox.nexusagent.in"
Write-Host ""
Write-Host "SSH command:"
Write-Host "  ssh -i `"$PemPath`" ubuntu@$publicIp"
