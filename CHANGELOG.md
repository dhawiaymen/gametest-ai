# Changelog

## 0.1.0 — Initial public release

### Available

See the README for supported functionality and deliberate limits. This version is an
early tool release, with no production certification or community adoption claim.

### Stabilization before release

- Reject malformed step types and oversized assertion data; make equality and inequality type-consistent.
- Bound browser diagnostics, sanitize XML control characters, check snapshot invariants and report asynchronous adapter timeouts.
- Intercept WebSocket upstream connections by default, detect HTTP failures, and provide a bundled demo.

- Add regression coverage, authentic screenshots and reproducible synthetic workloads.
- Add contribution, conduct, troubleshooting and roadmap documents.
- Verify extracted Windows executables before attaching release assets; include checksums
  and dependency notices. Record actual CI evidence with each build.
