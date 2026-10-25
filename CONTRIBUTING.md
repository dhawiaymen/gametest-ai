# Contributing to GameTest AI

This project is at its first public-release candidate (0.1.0). There is no
claim of established adoption. Small, reproducible fixes are welcome.

1. Fork the repository and create a focused branch.
2. Install Python 3.11+ and run `python -m pip install -e ".[dev]"`.
3. Run `python -m pytest` and `python -m ruff check .`.
4. Describe the problem, the change, and your actual validation in a pull request.

Keep platform-independent logic outside the GUI. Add behavioral regression
tests for bugs. Do not commit secrets, downloaded models, generated build
directories, personal images, or telemetry. AI-assisted contributions are
welcome; disclose material assistance, review the code, and report only checks
you actually performed. Contributions are licensed under MIT.

Before making breaking changes to JSON formats, discuss migration and schema
versioning. Be respectful and keep feedback specific to the work.
