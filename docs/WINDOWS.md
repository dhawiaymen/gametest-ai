# Windows support and distribution

Target: Windows 10/11 x64, Python 3.11 or newer with Tcl/Tk. The recommended
first-run path is Setup.cmd + Start.cmd. Each repository has its own .venv.
Use a writable folder, not Program Files. Paths containing spaces are supported.

The source implementation uses pathlib, Tkinter, and platform-independent
libraries. Development validation in the supplied record was performed on
Linux. Native Windows behavior is pending until the included CI runs on GitHub
or a maintainer performs a local Windows test. Do not advertise it as certified.

## Build a portable folder

Run `scripts/build_windows.ps1` on Windows from an environment with Python and
project dependencies. It runs the tests, then PyInstaller. The result is
`dist/GameTestAI/`. Distribute the **entire folder**, not just its .exe. Keep the
license and third-party notices with the binary. Builds are unsigned; no code
signing certificate or installer is included. PyInstaller is a build dependency,
not application code under this project's MIT license.

GameTest AI still requires a Playwright-managed Chromium installation for the
same Playwright version used in the build. The Windows build includes an
`Install-Browser.cmd` and a pinned browser-install requirement. Run that helper
on the destination machine before launching the executable. This requires
Python and network access once. A fully self-contained browser bundle is not
provided in 0.1.0; distribute from source for the simplest support path.

## Manual release validation

1. Run Setup.cmd from a fresh extraction with a path containing spaces.
2. Launch Start.cmd; open examples and complete the README workflow.
3. Confirm invalid input produces an understandable error and preserves inputs.
4. Run CLI --help and the automated tests; inspect artifacts.
5. Build the portable folder and repeat on a clean Windows user account.
6. Record OS, Python, dependency versions, commit, and actual results.

If `python -m tkinter` fails, repair Python and enable Tcl/Tk. If setup fails,
read the pip error instead of rerunning with administrator privileges blindly.
