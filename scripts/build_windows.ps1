$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne "Windows_NT") { throw "Build Windows binaries on Windows." }
python -m pip install ".[dev]"
if ($LASTEXITCODE) { throw "Dependency installation failed" }
python -m playwright install chromium
if ($LASTEXITCODE) { throw "Browser installation failed" }
python -m pytest
if ($LASTEXITCODE) { throw "Tests failed" }
python -m PyInstaller --noconfirm --clean --onedir --windowed --name GameTestAI --collect-all gametest_ai launch.py
if ($LASTEXITCODE) { throw "Build failed" }
Copy-Item LICENSE,README.md -Destination dist/GameTestAI
python -c "import importlib.metadata,pathlib; pathlib.Path('dist/GameTestAI/browser-requirements.txt').write_text('playwright==' + importlib.metadata.version('playwright') + '\n', encoding='utf-8')"
if ($LASTEXITCODE) { throw "Browser requirements could not be written" }
Copy-Item scripts/Install-Browser.cmd -Destination dist/GameTestAI
Write-Host "Build ready in dist/GameTestAI. Review docs/WINDOWS.md before distribution."
