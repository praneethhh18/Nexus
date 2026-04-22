@echo off
title NexusAgent Launcher
echo.
echo  ========================================
echo   NexusAgent v2.0 - Starting...
echo  ========================================
echo.

:: Check Ollama
echo [1/3] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo       Ollama not running. Starting it...
    start "" ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo       Ollama is running.
)

:: Start API server
echo [2/3] Starting API server on port 8000...
start "NexusAgent API" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate && uvicorn api.server:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

:: Start Frontend
echo [3/3] Starting frontend on port 5173...
start "NexusAgent UI" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --port 5173"
timeout /t 3 /nobreak >nul

echo.
echo  ========================================
echo   NexusAgent is ready!
echo.
echo   Frontend:  http://localhost:5173
echo   API:       http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo  ========================================
echo.

:: Open browser
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo Press any key to stop all services...
pause >nul

:: Cleanup
taskkill /fi "WINDOWTITLE eq NexusAgent API" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq NexusAgent UI" /f >nul 2>&1
echo Services stopped.
