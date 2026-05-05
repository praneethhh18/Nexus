@echo off
title NexusAgent Full Stack
setlocal enabledelayedexpansion

set "NEXUS_DIR=C:\Users\Praneeth p\OneDrive\Desktop\NexusAgent"
set "LAB_DIR=C:\Users\Praneeth p\OneDrive\Desktop\nexuscaller-lab"
set "FRONT_DIR=%NEXUS_DIR%\frontend"
set "LAND_DIR=%NEXUS_DIR%\landing"
set "WA_DIR=%NEXUS_DIR%\whatsapp_bridge"

echo.
echo  ============================================================
echo   NexusAgent -- Full Stack Launcher
echo   API  App  Landing  Vox Worker  Voice Server  WhatsApp
echo  ============================================================
echo.

:: ── 1. Free stale processes on all ports ─────────────────────────────────
echo [1/8] Freeing ports 8000 8765 5173 4000 3001...
call :kill_port 8000
call :kill_port 8765
call :kill_port 5173
call :kill_port 4000
call :kill_port 3001
taskkill /f /im ngrok.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: ── 2. Ollama ─────────────────────────────────────────────────────────────
echo [2/8] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo       Ollama not running -- starting it...
    start "" ollama serve
    timeout /t 4 /nobreak >nul
) else (
    echo       Ollama already running.
)

:: ── 3. NexusAgent API ─────────────────────────────────────────────────────
echo [3/8] Starting NexusAgent API (port 8000)...
start "NEXUS_API" cmd /k "cd /d "%NEXUS_DIR%" && call venv\Scripts\activate && uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 4 /nobreak >nul

:: ── 4. App Frontend ───────────────────────────────────────────────────────
echo [4/8] Starting App frontend (port 5173)...
start "NEXUS_APP" cmd /k "cd /d "%FRONT_DIR%" && npm run dev -- --port 5173"
timeout /t 3 /nobreak >nul

:: ── 5. Landing Page ───────────────────────────────────────────────────────
echo [5/8] Starting Landing page (port 4000)...
start "NEXUS_LANDING" cmd /k "cd /d "%LAND_DIR%" && npm run dev"
timeout /t 3 /nobreak >nul

:: ── 6. Vox Agent Worker ───────────────────────────────────────────────────
echo [6/8] Starting Vox Agent worker (LiveKit)...
start "NEXUS_VOX" cmd /k "cd /d "%LAB_DIR%" && call venv\Scripts\activate && python -m voice_agent.agent dev"
timeout /t 4 /nobreak >nul

:: ── 7. Voice-agent Server ─────────────────────────────────────────────────
echo [7/8] Starting Voice-agent server (port 8765)...
start "NEXUS_VOICE" cmd /k "cd /d "%LAB_DIR%" && call venv\Scripts\activate && uvicorn voice_agent.server:app --host 0.0.0.0 --port 8765 --reload"
timeout /t 3 /nobreak >nul

:: ── 8. WhatsApp Bridge ────────────────────────────────────────────────────
echo [8/8] Starting WhatsApp bridge (port 3001)...
start "NEXUS_WA" cmd /k "cd /d "%WA_DIR%" && node server.js"
timeout /t 3 /nobreak >nul

echo.
echo  ============================================================
echo   All services launched!
echo.
echo   Landing page   : http://localhost:4000
echo   App frontend   : http://localhost:5173
echo   NexusAgent API : http://localhost:8000/docs
echo   Voice server   : http://localhost:8765/health
echo   WhatsApp bridge: http://localhost:3001/health
echo   Vox worker     : watch "NEXUS_VOX" window for "registered worker"
echo   WhatsApp       : watch "NEXUS_WA" window -- scan QR if first run
echo  ============================================================
echo.

timeout /t 2 /nobreak >nul
start http://localhost:4000
start http://localhost:5173

echo Press any key to STOP all services...
pause >nul

:: ── Cleanup ───────────────────────────────────────────────────────────────
echo.
echo Stopping all services...
taskkill /fi "WINDOWTITLE eq NEXUS_API"    /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_APP"    /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_LANDING" /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_VOX"    /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_VOICE"  /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_WA"     /f /t >nul 2>&1
call :kill_port 8000
call :kill_port 8765
call :kill_port 5173
call :kill_port 4000
call :kill_port 3001
taskkill /f /im ngrok.exe >nul 2>&1
echo Done.
exit /b 0


:kill_port
set "_P=%~1"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%_P% " ^| findstr "LISTENING"') do (
    echo   - killing PID %%a on port %_P%
    taskkill /f /pid %%a >nul 2>&1
)
exit /b 0
