@echo off
:: ============================================================================
::  NexusAgent + NexusCaller — single-shot launcher
::  Boots: Ollama, NexusAgent API, App UI, Landing, WhatsApp bridge,
::         Vox worker (LiveKit), Voice server (lab).
::  Pre-flight checks for venv + node_modules so first-run never fails silently.
::  Stop everything with stop.bat or by pressing any key in this window.
:: ============================================================================
title NexusAgent Launcher
setlocal enabledelayedexpansion

set "NEXUS_DIR=C:\Users\Praneeth p\OneDrive\Desktop\NexusAgent"
set "LAB_DIR=C:\Users\Praneeth p\OneDrive\Desktop\nexuscaller-lab"
set "FRONT_DIR=%NEXUS_DIR%\frontend"
set "LAND_DIR=%NEXUS_DIR%\landing"
set "WA_DIR=%NEXUS_DIR%\whatsapp_bridge"

echo.
echo ============================================================
echo   NexusAgent + NexusCaller - Full Stack Launcher
echo ============================================================
echo.

:: ── 0. Pre-flight checks ──────────────────────────────────────────────────
echo [pre-flight] Checking project layout...

if not exist "%NEXUS_DIR%\venv\Scripts\activate.bat" (
    echo   ERROR: NexusAgent venv missing at %NEXUS_DIR%\venv
    echo          Run:  cd "%NEXUS_DIR%"  ^&^&  python -m venv venv  ^&^&  venv\Scripts\activate  ^&^&  pip install -r requirements.txt
    pause & exit /b 1
)
if not exist "%LAB_DIR%\venv\Scripts\activate.bat" (
    echo   ERROR: Lab venv missing at %LAB_DIR%\venv
    echo          Run:  cd "%LAB_DIR%"  ^&^&  python -m venv venv  ^&^&  venv\Scripts\activate  ^&^&  pip install -r requirements.txt
    pause & exit /b 1
)
if not exist "%NEXUS_DIR%\.env" (
    echo   WARNING: %NEXUS_DIR%\.env not found  -- using defaults
)
if not exist "%LAB_DIR%\.env" (
    echo   WARNING: %LAB_DIR%\.env not found  -- voice calls will not work
)

:: Auto-install npm deps if missing (first-run pain killer)
if not exist "%FRONT_DIR%\node_modules" (
    echo   App frontend node_modules missing -- running npm install...
    pushd "%FRONT_DIR%" && call npm install --silent && popd
)
if not exist "%LAND_DIR%\node_modules" (
    echo   Landing node_modules missing -- running npm install...
    pushd "%LAND_DIR%" && call npm install --silent && popd
)
if not exist "%WA_DIR%\node_modules" (
    echo   WhatsApp bridge node_modules missing -- running npm install...
    pushd "%WA_DIR%" && call npm install --silent && popd
)
echo   OK.
echo.

:: ── 1. Free stale ports ──────────────────────────────────────────────────
echo [1/8] Freeing ports 8000 8001 8765 5173 4000 3001...
call :kill_port 8000
call :kill_port 8001
call :kill_port 8765
call :kill_port 5173
call :kill_port 4000
call :kill_port 3001
taskkill /f /im ngrok.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: ── 2. Ollama ─────────────────────────────────────────────────────────────
echo [2/8] Checking Ollama (port 11434)...
curl -s -o nul http://localhost:11434/api/tags
if errorlevel 1 (
    echo       Ollama not running -- starting it...
    start "NEXUS_OLLAMA" /min cmd /c "ollama serve"
    call :wait_port 11434 20
) else (
    echo       Already running.
)

:: ── 3. NexusAgent API (port 8000) ─────────────────────────────────────────
echo [3/8] Starting NexusAgent API (port 8000)...
start "NEXUS_API" powershell -NoProfile -NoExit -Command "$env:SENTRY_DSN=''; $env:NEXUS_SKIP_SAMPLE_DOCS='1'; Set-Location -LiteralPath '%NEXUS_DIR%'; .\venv\Scripts\python.exe -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload --reload-dir api --reload-dir agents --reload-dir config --reload-dir rag --reload-dir workflows"
venv\Scripts\python.exe scripts\wait_for_url.py http://127.0.0.1:8000/api/ready 600 "NexusAgent API"
if errorlevel 1 (
    echo.
    echo ERROR: NexusAgent API did not become ready.
    echo        Check the NEXUS_API window for the Python traceback.
    echo        The browser was not opened because the app would show HTTP 502.
    pause
    exit /b 1
)

:: ── 4. App frontend (port 5173) ───────────────────────────────────────────
echo [4/8] Starting App frontend (port 5173)...
start "NEXUS_APP" powershell -NoProfile -NoExit -Command "Set-Location -LiteralPath '%FRONT_DIR%'; npm.cmd run dev -- --port 5173"
call :wait_port 5173 25

:: ── 5. Landing site (port 4000) ───────────────────────────────────────────
echo [5/8] Starting Landing site (port 4000)...
start "NEXUS_LANDING" cmd /k "cd /d ""%LAND_DIR%"" && npm run dev -- --port 4000"
call :wait_port 4000 15

:: ── 6. Vox worker (LiveKit Agent worker) ─────────────────────────────────
echo [6/8] Starting Vox Agent worker (LiveKit)...
start "NEXUS_VOX" cmd /k "cd /d ""%LAB_DIR%"" && call venv\Scripts\activate.bat && python -m voice_agent.agent dev"
timeout /t 3 /nobreak >nul

:: ── 7. Voice-agent server (port 8765, lab API for precall + cockpit) ─────
echo [7/8] Starting Voice-agent server (port 8765)...
start "NEXUS_VOICE" cmd /k "cd /d ""%LAB_DIR%"" && call venv\Scripts\activate.bat && uvicorn voice_agent.server:app --host 0.0.0.0 --port 8765"
call :wait_port 8765 20

:: ── 8. WhatsApp bridge (port 3001) ────────────────────────────────────────
echo [8/8] Starting WhatsApp bridge (port 3001)...
start "NEXUS_WA" cmd /k "cd /d ""%WA_DIR%"" && node server.js"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo   All services launched.
echo.
echo   App frontend     http://localhost:5173
echo   Landing page     http://localhost:4000
echo   API docs         http://localhost:8000/docs
echo   Voice server     http://localhost:8765/health
echo   WhatsApp bridge  http://localhost:3001/health
echo   Vox worker       window "NEXUS_VOX" -- wait for "registered worker"
echo   WhatsApp         window "NEXUS_WA"  -- scan QR if first run
echo ============================================================
echo.

timeout /t 2 /nobreak >nul
start "" http://localhost:5173

echo.
echo Press any key in THIS window to STOP everything...
pause >nul

call :stop_all
echo.
echo Done.
exit /b 0


:: ── Helpers ───────────────────────────────────────────────────────────────
:kill_port
set "_P=%~1"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%_P% " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
exit /b 0

:wait_port
:: Wait up to N seconds for a port to start LISTENING. Doesn't fail the launcher
:: if the port never comes up -- the user can still see the service window's error.
set "_P=%~1"
set "_N=%~2"
set /a _i=0
:wait_port_loop
netstat -aon | findstr ":%_P% " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo       Port %_P% is up.
    exit /b 0
)
set /a _i+=1
if %_i% geq %_N% (
    echo       (timeout waiting for port %_P% -- check the service window)
    exit /b 0
)
timeout /t 1 /nobreak >nul
goto wait_port_loop

:stop_all
echo.
echo Stopping all services...
taskkill /fi "WINDOWTITLE eq NEXUS_API"     /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_APP"     /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_LANDING" /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_VOX"     /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_VOICE"   /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_WA"      /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_OLLAMA"  /f /t >nul 2>&1
call :kill_port 8000
call :kill_port 8001
call :kill_port 8765
call :kill_port 5173
call :kill_port 4000
call :kill_port 3001
taskkill /f /im ngrok.exe >nul 2>&1
exit /b 0
