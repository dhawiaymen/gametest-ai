@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if errorlevel 1 (
  echo Install Python 3.11 or newer from python.org, including Tcl/Tk and the Python launcher.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto :failed
echo Setup complete. Open Start.cmd.
pause
exit /b 0
:failed
echo Setup failed. Read the error above. Check your Python installation and network.
pause
exit /b 1
