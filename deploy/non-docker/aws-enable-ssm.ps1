param(
  [string]$Region = "ap-south-1",
  [string]$InstanceId = "i-0234c15417e801b14",
  [string]$RoleName = "nexusagent-ssm-ec2-role",
  [string]$InstanceProfileName = "nexusagent-ssm-ec2-profile"
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

$trustPolicy = @'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
'@

$tmpPolicy = Join-Path $env:TEMP "nexusagent-ec2-trust-policy.json"
Set-Content -Path $tmpPolicy -Value $trustPolicy -Encoding ascii

$roleExists = $true
try {
  Invoke-Aws iam get-role --role-name $RoleName | Out-Null
} catch {
  $roleExists = $false
}

if (-not $roleExists) {
  Write-Host "Creating IAM role $RoleName..."
  Invoke-Aws iam create-role --role-name $RoleName --assume-role-policy-document "file://$tmpPolicy" | Out-Null
} else {
  Write-Host "IAM role $RoleName already exists."
}

Write-Host "Attaching AmazonSSMManagedInstanceCore..."
Invoke-Aws iam attach-role-policy `
  --role-name $RoleName `
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore | Out-Null

$profileExists = $true
try {
  Invoke-Aws iam get-instance-profile --instance-profile-name $InstanceProfileName | Out-Null
} catch {
  $profileExists = $false
}

if (-not $profileExists) {
  Write-Host "Creating instance profile $InstanceProfileName..."
  Invoke-Aws iam create-instance-profile --instance-profile-name $InstanceProfileName | Out-Null
  Start-Sleep -Seconds 8
}

$profile = Invoke-Aws iam get-instance-profile --instance-profile-name $InstanceProfileName | ConvertFrom-Json
$hasRole = $profile.InstanceProfile.Roles | Where-Object { $_.RoleName -eq $RoleName }
if (-not $hasRole) {
  Write-Host "Adding role to instance profile..."
  Invoke-Aws iam add-role-to-instance-profile `
    --instance-profile-name $InstanceProfileName `
    --role-name $RoleName | Out-Null
  Start-Sleep -Seconds 12
}

$assoc = Invoke-Aws ec2 describe-iam-instance-profile-associations `
  --region $Region `
  --filters "Name=instance-id,Values=$InstanceId" `
  --query "IamInstanceProfileAssociations[0]" `
  --output json | ConvertFrom-Json

if ($assoc -and $assoc.AssociationId) {
  Write-Host "Replacing existing instance profile association..."
  Invoke-Aws ec2 replace-iam-instance-profile-association `
    --region $Region `
    --association-id $assoc.AssociationId `
    --iam-instance-profile Name=$InstanceProfileName | Out-Null
} else {
  Write-Host "Associating instance profile with EC2..."
  Invoke-Aws ec2 associate-iam-instance-profile `
    --region $Region `
    --instance-id $InstanceId `
    --iam-instance-profile Name=$InstanceProfileName | Out-Null
}

Write-Host "SSM role/profile is attached. Wait 1-3 minutes, then check:"
Write-Host "aws ssm describe-instance-information --region $Region"
