@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe goto missing
.venv\Scripts\python.exe -m backend.install_wifi
if errorlevel 1 goto failed
echo Wi-Fi runtime ready. Complete initial USB wireless setup in TQIG, then unplug USB.
pause
exit /b 0
:missing
echo Run Start-TQIG.cmd first.
:failed
pause
exit /b 1
