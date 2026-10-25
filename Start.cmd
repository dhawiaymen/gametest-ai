@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please run Setup.cmd first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m gametest_ai gui
if errorlevel 1 pause
