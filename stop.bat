@echo off
echo Stopping NexusAgent services...
taskkill /fi "WINDOWTITLE eq NexusAgent API" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq NexusAgent UI" /f >nul 2>&1
echo Done.
