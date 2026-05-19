@echo off
:: ============================================================================
::  Stop everything started by start.bat (NexusAgent + NexusCaller stack).
:: ============================================================================
title NexusAgent Stop
echo.
echo Stopping NexusAgent + NexusCaller stack...

taskkill /fi "WINDOWTITLE eq NEXUS_API"     /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_APP"     /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_LANDING" /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_VOX"     /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_VOICE"   /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_WA"      /f /t >nul 2>&1
taskkill /fi "WINDOWTITLE eq NEXUS_OLLAMA"  /f /t >nul 2>&1

for %%P in (8000 8001 8765 5173 4000 3001) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%P " ^| findstr "LISTENING"') do (
        echo   - killing PID %%a on port %%P
        taskkill /f /pid %%a >nul 2>&1
    )
)

taskkill /f /im ngrok.exe >nul 2>&1
echo Done.
timeout /t 2 /nobreak >nul
exit /b 0
