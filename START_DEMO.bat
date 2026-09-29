@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The prepared environment is missing.
  echo Run SETUP_WINDOWS.bat once, then start this file again.
  pause
  exit /b 1
)

echo Starting Quantum Aircraft Loading demo...
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true
