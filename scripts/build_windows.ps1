$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne "Windows_NT") { throw "Build Windows binaries on Windows." }
python -m pip install -c constraints-release.txt ".[dev]"
if ($LASTEXITCODE) { throw "Dependency installation failed" }
$env:PLAYWRIGHT_BROWSERS_PATH = "0"
python -m playwright install chromium
if ($LASTEXITCODE) { throw "Browser installation failed" }
python -m pytest --junitxml=build-tests.xml
if ($LASTEXITCODE) { throw "Tests failed" }
python -m PyInstaller --noconfirm --clean --onedir --windowed --name GameTestAI --collect-all gametest_ai launch.py
if ($LASTEXITCODE) { throw "Build failed" }
Copy-Item LICENSE,README.md,CHANGELOG.md -Destination dist/GameTestAI
Copy-Item examples -Destination dist/GameTestAI/examples -Recurse
python scripts/collect_licenses.py dist/GameTestAI
if ($LASTEXITCODE) { throw "License collection failed" }
python scripts/verify_distribution.py dist/GameTestAI GameTestAI gametest-ai
if ($LASTEXITCODE) { throw "Extracted executable verification failed; do not publish" }
Write-Host "Verified archives and checksums are in release-assets/."
