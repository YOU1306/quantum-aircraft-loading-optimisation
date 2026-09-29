@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer and rerun this file.
  pause
  exit /b 1
)

python -m venv .venv
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto :failed

".venv\Scripts\python.exe" -m pytest
if errorlevel 1 goto :failed

echo.
echo Setup and tests completed. Double-click START_DEMO.bat.
pause
exit /b 0

:failed
echo.
echo Setup failed. Copy the error above when asking for help.
pause
exit /b 1
