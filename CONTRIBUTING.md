# Contributing to GameTest AI

Start with a small reproducible problem or a roadmap proposal. This is an early
project: no external adoption or contributor count is claimed.

## Development setup

Use Python 3.11–3.13 with Tcl/Tk. Fork and clone the repository, then create a venv:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Install the matching browser with `python -m playwright install chromium`.
On Linux, use `xvfb-run -a python -m pytest` to execute GUI tests. A skipped GUI
test is not evidence that the interface works. `constraints-release.txt` records
the build versions; normal development may test newer supported dependencies.

## Propose and review a change

1. Check existing issues; describe observed and expected behavior with minimal inputs.
2. Make a focused branch. Discuss schema changes and migrations before implementing them.
3. Add behavioral regression tests for a bug, including a failure case where useful.
4. Run the applicable tests and lint checks. State OS, Python version and any skipped tests.
5. Open a PR describing the problem, resulting behavior, evidence and remaining limits.

The maintainer reviews correctness, privacy, compatibility, dependency/license changes,
error handling and test quality. Passing CI is required for merge; it is not a substitute
for review. No self-approval or invented external review is claimed. Requests from the
maintainer should be addressed in follow-up commits before merge.

AI assistance is allowed when disclosed. Contributors remain responsible for understanding,
reviewing and testing their submission. Do not submit generated bulk issues, trivial PRs
for activity counts, fake testimonials, or copied code with incompatible licensing.

Contributions are under MIT. Do not upload secrets, private game assets, local models,
telemetry, build folders or user reports containing personal paths. See CODE_OF_CONDUCT.md
and SECURITY.md. First contributions can include a reproducible bug, a focused test,
a documented example or a roadmap item whose scope is agreed in its issue.
