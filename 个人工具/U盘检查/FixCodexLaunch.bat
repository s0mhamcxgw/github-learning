@echo off
chcp 65001 >nul
echo ============================================
echo   Codex Fix and Launch
echo   Run this as Administrator
echo ============================================
echo.
echo [1/3] Killing stale Codex processes...
taskkill /F /IM ChatGPT.exe /T 2>nul
taskkill /F /PID 9440 /T 2>nul
echo.
echo [2/3] Waiting for cleanup...
timeout /t 3 /nobreak >nul
echo.
echo [3/3] Launching Codex...
start "" explorer.exe "shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App"
echo.
echo Done. If Codex still does not open, reboot the PC.
echo.
pause
