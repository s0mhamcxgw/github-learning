@echo off
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0Launch-Codex.ps1"
if errorlevel 1 pause
