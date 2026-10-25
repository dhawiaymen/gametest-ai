# Executed validation

## Baseline

The original published commit had a successful [GitHub Actions run](https://github.com/dhawiaymen/gametest-ai/actions/runs/40241622124). This was rechecked on 26 October 2026 before changes. No releases existed then.

## Stabilization checks executed locally

- **43 pytest tests passed, zero failures and zero skips**, including Tk GUI checks,
  on Linux / Python 3.12.14 with a virtual display.
- Studio generated-runtime tests execute Node.js. GameTest browser checks execute real
  Playwright 1.51.0 / Chromium 134 headless shell available in the test environment.
- AssetFlow tests were also run against Pillow 13.0.0. The screenshot/demo environment
  uses Pillow 12.3.0. Both results must be distinguished from native Windows results.
- A cross-project integration exported tap/catch/dodge and executed 101 adapter steps
  for each in GameTest; all three scenarios passed.
- pip-audit reported no known advisories for the separately recorded current dependency
  environment, including Playwright 1.64.1 and Pillow 13.0.0.

The current Playwright 1.64.1 browser download was corrupt in this local environment;
no successful local test of that exact new pair is claimed. An attempted mismatched
browser/driver run was abandoned. CI installs the matching version and remains the
release gate. A previous local display setup failed; the final test count above comes
from the subsequent successful displayed run.

## Native Windows and final revision

The workflow attached to this revision runs the OS/Python matrix and extracted-EXE
checks. Consult that run and the release's `windows-verification.json` for the exact
commit, platform, checks and archive digest. A configured workflow is not evidence of
success until its run completes. Manual consumer-desktop/DPI/accessibility testing
remains outstanding.

[Authentic demo](DEMO.md) · [Reproducible benchmark](demo/benchmark.json)

A Windows/Python 3.11 run skipped the bundled-demo GUI test after Tk initialization failed. That release run was cancelled. GUI tests now use a main-thread interpreter cleanup fixture and fail in CI if a display cannot be constructed. Workbench destruction also releases owned Tk variables immediately; demo cleanup is verified.
