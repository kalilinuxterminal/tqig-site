@echo off
setlocal
cd /d "%~dp0"
set "TQIG_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%TQIG_PYTHON%" goto python_ready
set "TQIG_PYTHON=python"
:python_ready
if exist .venv\Scripts\python.exe goto dependencies
"%TQIG_PYTHON%" -m venv .venv
if errorlevel 1 goto failed
:dependencies
.venv\Scripts\python.exe -c "import pymobiledevice3,fastapi,uvicorn" >nul 2>nul
if not errorlevel 1 goto frontend
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if errorlevel 1 goto failed
:frontend
if exist node_modules\vite if exist node_modules\qrcode.react goto build
call npm ci
if errorlevel 1 goto failed
:build
call npm run build
if errorlevel 1 goto failed
echo.
echo TQIG - open http://127.0.0.1:8766/dashboard in Chrome or Edge.
echo Keep this helper running while controlling your iPhone.
echo Use Stop Simulation and verify real location before closing.
echo This is an unsigned engineering preview, not a signed consumer installer.
.venv\Scripts\python.exe -m backend.launch
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo TQIG could not start. See the error above and README.md.
pause
exit /b 1
