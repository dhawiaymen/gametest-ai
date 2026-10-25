# Windows installation and distribution

Target: Windows 10/11 x64. Native CI uses the actual `windows-latest` runner;
it does not certify every Windows version, GPU, DPI setting or antivirus product.

## Portable application

Download the ZIP from the repository's Releases page, extract everything into a
writable directory (for example `D:\DevTools\GameTestAI`), and launch `GameTestAI.exe` in
the extracted application folder. Python is not required for the portable build.
Chromium is bundled with GameTest AI; no browser cache from a development machine is required. Local Ollama/model installation is optional.

The executable is unsigned. Verify its SHA-256 against the release's `SHA256SUMS.txt`:

```powershell
Get-FileHash .\downloaded-file.zip -Algorithm SHA256
```

Do not disable antivirus or run as administrator to work around a failed launch.
Keep the entire `_internal` and `licenses` directories with the EXE.

## Run from source

Install Python 3.11–3.13 including Tcl/Tk and the Python launcher, then run `Setup.cmd`
and `Start.cmd`. Setup uses the network once for dependencies. Source development is
also supported on Linux. See the README for the CLI and application-specific requirements.

## Build and release gate

`scripts/build_windows.ps1` installs constrained dependencies, executes the tests,
builds with PyInstaller, collects dependency notices, creates a ZIP, extracts it into
a different path containing spaces, then launches the extracted EXE's smoke check.
The check opens Tk and runs a real core operation. Any failure stops publication.
`release-assets/windows-verification.json` records the checks and archive digest.
The release workflow additionally requires all six OS/Python test jobs and rechecks
SHA-256 before creating the tag and release. Existing releases are never replaced.

A hosted runner is not a clean consumer Windows desktop. Manual checks still needed:
high DPI (125–200%), low-resolution laptops, accessibility/screen readers, a standard
fresh user account, antivirus behavior, and older supported Windows installations.
