# NexusAgent — one-shot Postgres setup script.
#
# What this does:
#   1. Backs up pg_hba.conf (already done by Claude — just safety net)
#   2. Switches local auth to "trust" so we can connect without a password
#   3. Restarts PostgreSQL so the change takes effect
#   4. Creates the `nexus` user with password 'nexuspw'
#   5. Creates the `nexusagent` database owned by `nexus`
#   6. Restores pg_hba.conf back to scram-sha-256 (passwords required again)
#   7. Restarts PostgreSQL one more time so secure auth is back on
#
# After this script finishes, the postgres superuser still has whatever
# password it had before (we never changed it). You can keep ignoring it —
# the app uses the new `nexus` user from now on.
#
# REQUIREMENTS: must run as Administrator (Windows service control).

$ErrorActionPreference = "Stop"

$PgRoot   = "C:\Program Files\PostgreSQL\18"
$Hba      = Join-Path $PgRoot "data\pg_hba.conf"
$Backup   = "$Hba.bak"
$Service  = "postgresql-x64-18"
$Psql     = Join-Path $PgRoot "bin\psql.exe"
$Port     = 5434

function Write-Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "   OK: $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "   ERR: $msg" -ForegroundColor Red }

# ── 1. Sanity check (admin?)
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Err "This script must run as Administrator. Right-click the file -> Run as administrator."
    Read-Host "Press Enter to exit"
    exit 1
}

# ── 2. Backup (idempotent)
Write-Step "Backing up pg_hba.conf"
if (-not (Test-Path $Backup)) { Copy-Item $Hba $Backup }
Write-Ok "Backup at $Backup"

# ── 3. Switch to trust auth
Write-Step "Switching local auth to 'trust' (temporary)"
(Get-Content $Hba -Raw) `
    -replace "scram-sha-256", "trust" |
    Set-Content $Hba -NoNewline
Write-Ok "Auth = trust"

# ── 4. Restart Postgres
Write-Step "Restarting PostgreSQL service"
Restart-Service -Name $Service -Force
Start-Sleep -Seconds 3
Write-Ok "Service restarted"

# ── 5. Create user + database (silently; ignore "already exists")
Write-Step "Creating user 'nexus' and database 'nexusagent'"
$sql = @"
DO `$`$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='nexus') THEN
    CREATE ROLE nexus WITH LOGIN PASSWORD 'nexuspw';
  ELSE
    ALTER ROLE nexus WITH PASSWORD 'nexuspw';
  END IF;
END
`$`$;
"@

# Run the role create/update against the postgres maintenance DB
& $Psql -U postgres -h localhost -p $Port -d postgres -v ON_ERROR_STOP=1 -c $sql
if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create/update role nexus."; exit 2 }

# Database creation can't be in a DO block — separate call. Idempotent via SELECT.
$dbExists = & $Psql -U postgres -h localhost -p $Port -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='nexusagent'"
if ($dbExists -ne "1") {
    & $Psql -U postgres -h localhost -p $Port -d postgres -c "CREATE DATABASE nexusagent OWNER nexus"
    if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create database."; exit 3 }
} else {
    & $Psql -U postgres -h localhost -p $Port -d postgres -c "ALTER DATABASE nexusagent OWNER TO nexus"
}
& $Psql -U postgres -h localhost -p $Port -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE nexusagent TO nexus" | Out-Null
Write-Ok "User + database ready"

# ── 6. Restore secure auth
Write-Step "Restoring scram-sha-256 auth"
(Get-Content $Hba -Raw) `
    -replace "trust", "scram-sha-256" |
    Set-Content $Hba -NoNewline
Write-Ok "Auth = scram-sha-256"

# ── 7. Restart Postgres again
Write-Step "Restarting PostgreSQL one more time (lock down)"
Restart-Service -Name $Service -Force
Start-Sleep -Seconds 3
Write-Ok "Service restarted with secure auth"

# ── 8. Verify with the new user
Write-Step "Verifying nexus@nexusagent connection"
$env:PGPASSWORD = "nexuspw"
$ver = & $Psql -U nexus -h localhost -p $Port -d nexusagent -tAc "SELECT current_user, current_database()"
$env:PGPASSWORD = ""
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Connected as: $ver"
    Write-Host "`n[ DONE ] Postgres is set up. Tell Claude 'done' to continue.`n" -ForegroundColor Green
} else {
    Write-Err "Verification failed. Restore $Backup over $Hba and restart the service."
    exit 4
}

Read-Host "Press Enter to close"
