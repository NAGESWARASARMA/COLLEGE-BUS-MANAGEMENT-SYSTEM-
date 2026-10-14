@echo off
cd /d "%~dp0"

start "College Bus Website" cmd /k "py app.py"

timeout /t 5 /nobreak >nul

start "College Bus Camera Scanner" cmd /k "py scanner.py Arrival"