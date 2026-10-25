# Architecture

`schema.py` validates bounded JSON plans, comparisons, and deterministic input
generation. `server.py` temporarily serves local game files on loopback.
`runner.py` uses Playwright contexts for scenario isolation and records failures,
screenshots, and JSON/HTML/JUnit reports. User strings are passed to fixed
Playwright operations or serialized arguments, never concatenated into code.
`ai.py` is an optional local Ollama HTTP client; its output passes the same
schema validator. `gui.py` uses background threads and a main-thread event queue.

Roadmap candidates: visual comparison with explicit baselines, richer engine
adapters, action shrinking for failing random sequences, replay controls, and
measured model-generated plan quality. None is claimed as implemented.
