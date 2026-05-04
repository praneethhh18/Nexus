@echo off
title NexusAgent — Full Stack Launcher
setlocal enabledelayedexpansion

set NEXUS_DIR=C:\Users\Praneeth p\OneDrive\Desktop\NexusAgent
set LAB_DIR=C:\Users\Praneeth p\OneDrive\Desktop\nexuscaller-lab
set FRONT_DIR=%NEXUS_DIR%\frontend
set LAND_DIR=%NEXUS_DIR%\landing

echo.
echo  ============================================================
echo   NexusAgent — Full Stack
echo   API · App · Landing · Vox Agent · Voice Server · ngrok
echo  ============================================================
echo.

:: ── 1. Free up ports from any prior run ─────────────────────────────────────
echo [1/7] Freeing ports 8000, 8765, 5173, 4000 + stale ngrok...
call :kill_port 8000
call :kill_port 8765
call :kill_port 5173
call :kill_port 4000
taskkill /f /im ngrok.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: ── 2. Ollama ────────────────────────────────────────────────────────────────
echo [2/7] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo       Ollama not running — starting it...
    start "" ollama serve
    timeout /t 4 /nobreak >nul
) else (
    echo       Ollama is already running.
)

:: ── 3. NexusAgent API ────────────────────────────────────────────────────────
echo [3/7] Starting NexusAgent API  (port 8000)...
start "NexusAgent · API (8000)" cmd /k ^
  "cd /d "%NEXUS_DIR%" && call venv\Scripts\activate && uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 4 /nobreak >nul

:: ── 4. NexusAgent App Frontend ───────────────────────────────────────────────
echo [4/7] Starting App frontend  (port 5173)...
start "NexusAgent · App (5173)" cmd /k ^
  "cd /d "%FRONT_DIR%" && npm run dev -- --port 5173"
timeout /t 3 /nobreak >nul

:: ── 5. Landing Page ──────────────────────────────────────────────────────────
echo [5/7] Starting Landing page  (port 4000)...
start "NexusAgent · Landing (4000)" cmd /k ^
  "cd /d "%LAND_DIR%" && npm run dev"
timeout /t 3 /nobreak >nul

:: ── 6. Vox Agent worker (LiveKit STT/LLM/TTS) ───────────────────────────────
echo [6/7] Starting Vox Agent worker  (registers with LiveKit Cloud)...
start "NexusAgent · Vox worker" cmd /k ^
  "cd /d "%LAB_DIR%" && call venv\Scripts\activate && python -m voice_agent.agent dev"
timeout /t 4 /nobreak >nul

:: ── 7. Voice-agent FastAPI server (port 8765) ────────────────────────────────
echo [7/7] Starting Voice-agent server  (port 8765)...
start "NexusAgent · Voice server (8765)" cmd /k ^
  "cd /d "%LAB_DIR%" && call venv\Scripts\activate && uvicorn voice_agent.server:app --host 0.0.0.0 --port 8765 --reload"
timeout /t 3 /nobreak >nul

:: ── Optional: ngrok ──────────────────────────────────────────────────────────
:: Uncomment if you need a public URL for the voice server (e.g. for Twilio webhooks)
:: start "ngrok · tunnel (8765)" cmd /k "ngrok http 8765"

echo.
echo  ============================================================
echo   All services launched!
echo.
echo   Landing page     :  http://localhost:4000
echo   App frontend     :  http://localhost:5173
echo   NexusAgent API   :  http://localhost:8000/docs
echo   Voice server     :  http://localhost:8765/health
echo   Vox worker       :  check "NexusAgent · Vox worker" window
echo.
echo   NOTE: Vox worker needs LIVEKIT_URL/KEY/SECRET in
echo         nexuscaller-lab\.env to connect to LiveKit Cloud.
echo  ============================================================
echo.

:: Open browser tabs
timeout /t 2 /nobreak >nul
start http://localhost:4000
start http://localhost:5173

echo Press any key to STOP all services...
pause >nul

:: ── Cleanup ──────────────────────────────────────────────────────────────────
echo.
echo Stopping all services...
taskkill /fi "WINDOWTITLE eq NexusAgent · API (8000)*"         /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NexusAgent · App (5173)*"         /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NexusAgent · Landing (4000)*"     /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NexusAgent · Vox worker*"         /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NexusAgent · Voice server (8765)*" /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq ngrok · tunnel*"                  /f /t >nul 2>&1
call :kill_port 8000
call :kill_port 8765
call :kill_port 5173
call :kill_port 4000
taskkill /f /im ngrok.exe >nul 2>&1
echo Done. All services stopped.
exit /b 0


:kill_port
set PORT=%~1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    echo   - killing PID %%a on port %PORT%
    taskkill /f /pid %%a >nul 2>&1
)
exit /b 0
