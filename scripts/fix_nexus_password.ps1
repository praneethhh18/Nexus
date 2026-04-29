# NexusAgent — clean reset of the nexus user + nexusagent database.
#
# The previous setup script's nested DO $$ block silently failed under
# PowerShell escaping, so the nexus role was never actually created. This
# script rebuilds from scratch using plain SQL — one statement at a time,
# no nested dollar-quoted blocks.
#
# It's destructive (drops + recreates the database) but that's fine since
# we haven't put any data in it yet.

$ErrorActionPreference = "Stop"

$PgRoot   = "C:\Program Files\PostgreSQL\18"
$Hba      = Join-Path $PgRoot "data\pg_hba.conf"
$Service  = "postgresql-x64-18"
$Psql     = Join-Path $PgRoot "bin\psql.exe"
$Port     = 5434

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Must run as Administrator." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ">> Switching to trust auth" -ForegroundColor Cyan
(Get-Content $Hba -Raw) -replace "scram-sha-256", "trust" | Set-Content $Hba -NoNewline
Restart-Service -Name $Service -Force
Start-Sleep -Seconds 3

Write-Host ">> Dropping any leftovers" -ForegroundColor Cyan
& $Psql -U postgres -h localhost -p $Port -d postgres -c "DROP DATABASE IF EXISTS nexusagent;" | Out-Null
& $Psql -U postgres -h localhost -p $Port -d postgres -c "DROP ROLE IF EXISTS nexus;" | Out-Null

Write-Host ">> Creating nexus role" -ForegroundColor Cyan
& $Psql -U postgres -h localhost -p $Port -d postgres -c "CREATE ROLE nexus WITH LOGIN PASSWORD 'nexuspw';"
if ($LASTEXITCODE -ne 0) { Write-Host "CREATE ROLE failed" -ForegroundColor Red; exit 2 }

Write-Host ">> Creating nexusagent database" -ForegroundColor Cyan
& $Psql -U postgres -h localhost -p $Port -d postgres -c "CREATE DATABASE nexusagent OWNER nexus;"
if ($LASTEXITCODE -ne 0) { Write-Host "CREATE DATABASE failed" -ForegroundColor Red; exit 3 }

& $Psql -U postgres -h localhost -p $Port -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE nexusagent TO nexus;" | Out-Null

Write-Host ">> Restoring secure auth" -ForegroundColor Cyan
(Get-Content $Hba -Raw) -replace "trust", "scram-sha-256" | Set-Content $Hba -NoNewline
Restart-Service -Name $Service -Force
Start-Sleep -Seconds 3

Write-Host ">> Verifying nexus login" -ForegroundColor Cyan
$env:PGPASSWORD = "nexuspw"
$ver = & $Psql -U nexus -h localhost -p $Port -d nexusagent -tAc "SELECT current_user || '@' || current_database();"
$env:PGPASSWORD = ""
if ($LASTEXITCODE -eq 0 -and $ver -match "nexus@nexusagent") {
    Write-Host "`n[ DONE ] Connected as: $ver" -ForegroundColor Green
    Write-Host "Tell Claude 'fixed' to continue.`n" -ForegroundColor Green
} else {
    Write-Host "Verification failed: $ver" -ForegroundColor Red
    exit 4
}

Read-Host "Press Enter to close"
