@echo off
cd /d "%~dp0"
if exist "AionPulse.exe" (
    start "" "AionPulse.exe"
) else if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "app.py" --capture --overlay
) else (
    start "" pythonw.exe "app.py" --capture --overlay
)
