@echo off
setlocal
cd /d "%~dp0"
if not exist browser-requirements.txt (
  echo This helper belongs in the built GameTestAI folder beside browser-requirements.txt.
  pause
  exit /b 1
)
py -3 -m venv .browser-setup
if errorlevel 1 goto :failed
".browser-setup\Scripts\python.exe" -m pip install -r browser-requirements.txt
if errorlevel 1 goto :failed
".browser-setup\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto :failed
echo Browser installed for the current user. You can now open GameTestAI.exe.
pause
exit /b 0
:failed
echo Browser setup failed. Install Python 3.11 or newer and check your network.
pause
exit /b 1
