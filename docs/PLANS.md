# Plan schema v1

The root object has exactly `version:1` and `scenarios`. Each scenario has
exactly `name` (unique) and `steps`. Plans allow 1–100 scenarios, 1–5000 steps
per scenario, and at most 20,000 total steps / 5 MB per file.

| Type | Exact additional fields | Behavior |
|---|---|---|
| reset | seed | Adapter reset, uint32 seed |
| game | action, dt | Adapter step; action allows x and/or tap; dt 0–10 seconds |
| click | selector | Playwright locator click |
| press | key | Playwright keyboard key/chord |
| wait | ms | 0–10000 milliseconds |
| assert | source, path, op, value | Compare snapshot value or DOM text |

For `assert`, source is `snapshot` or `text`. Snapshot paths are dotted keys
(including array indices, e.g. `items.0.x`); text paths are Playwright selectors.
Operators: eq, ne, gt, gte, lt, lte, contains. Values are JSON scalars other than
null. Missing paths and type-incompatible comparisons fail. Unknown fields,
non-finite numbers, and arbitrary execution actions are rejected.

Reset/game steps check state invariants automatically. A test with no explicit
assertions still checks browser errors and, for adapter steps, state validity;
it does not establish that the game is fun, fair, winnable, or feature-complete.
Scenarios are isolated. Both successful and failed scenarios receive screenshots
when the browser can capture them. `report.json` is the authoritative machine
record; HTML is a summary and `junit.xml` is for CI integrations.
