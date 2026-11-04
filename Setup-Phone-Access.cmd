@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe goto missing
.venv\Scripts\python.exe -m backend.install_phone_access
if errorlevel 1 goto failed
echo Open TQIG Dashboard and choose Enable phone access.
pause
exit /b 0
:missing
echo Run Start-TQIG.cmd first to prepare TQIG.
:failed
pause
exit /b 1
