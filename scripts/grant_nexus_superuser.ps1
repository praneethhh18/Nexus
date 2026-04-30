# Grant the `nexus` user temporary superuser so the data migration can use
# session_replication_role to bypass FK ordering constraints. Required for
# the SQLite -> Postgres data migration only; you can revoke after.

$ErrorActionPreference = "Stop"

$PgRoot   = "C:\Program Files\PostgreSQL\18"
$Hba      = Join-Path $PgRoot "data\pg_hba.conf"
$Service  = "postgresql-x64-18"
$Psql     = Join-Path $PgRoot "bin\psql.exe"
$Port     = 5434

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Must run as Administrator." -ForegroundColor Red
    Read-Host "Press Enter"; exit 1
}

Write-Host ">> Switching to trust auth (temporary)" -ForegroundColor Cyan
(Get-Content $Hba -Raw) -replace "scram-sha-256", "trust" | Set-Content $Hba -NoNewline
Restart-Service -Name $Service -Force
Start-Sleep -Seconds 3

Write-Host ">> Granting SUPERUSER to nexus (for migration)" -ForegroundColor Cyan
& $Psql -U postgres -h localhost -p $Port -d postgres -c "ALTER ROLE nexus WITH SUPERUSER;"
if ($LASTEXITCODE -ne 0) { Write-Host "GRANT failed" -ForegroundColor Red; exit 2 }

Write-Host ">> Restoring secure auth" -ForegroundColor Cyan
(Get-Content $Hba -Raw) -replace "trust", "scram-sha-256" | Set-Content $Hba -NoNewline
Restart-Service -Name $Service -Force
Start-Sleep -Seconds 3

Write-Host "`n[ DONE ] nexus is now SUPERUSER. Tell Claude 'super-granted'.`n" -ForegroundColor Green
Read-Host "Press Enter to close"
