# GameTest AI roadmap

This is a proposal list, not a delivery promise. Reliability and reproducible bugs take
priority over feature count. Discuss a concrete use case before starting large changes.

## Current release

- Reject malformed step types and oversized assertion data; make equality and inequality type-consistent.
- Bound browser diagnostics, sanitize XML control characters, check snapshot invariants and report asynchronous adapter timeouts.
- Intercept WebSocket upstream connections by default, detect HTTP failures, and provide a bundled demo.

## Candidate contributions

- [ ] Stress-plan progress and replay documentation.
- [ ] Process-isolated hard timeouts for synchronous infinite JavaScript loops.
- [ ] Baseline image comparisons with explicit tolerances and real sample games.

## Feedback and evidence

For each accepted improvement record its issue, minimal reproduction, fix PR and test.
Ask early testers which task they tried, whether they completed it, their OS and the
first obstacle. Record distinct willing testers only with consent; do not identify
anonymous downloads as users. No telemetry is installed in the applications.

Track real stars/forks, external merged PRs, resolved user bugs and release asset download
counts with a dated GitHub snapshot. Raw asset downloads include possible repeats/automation
and are not unique users. Exclude maintainer validation downloads from adoption claims.
Never buy/exchange stars, create fake accounts, manufacture testimonials, or submit
trivial contributions to reach an eligibility threshold.
