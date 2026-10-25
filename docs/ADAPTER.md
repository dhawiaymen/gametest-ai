# Adapter contract

GameScript Studio implements this interface. For another HTML game, expose:

```javascript
window.gameTest = {
  version: 1,
  reset(seed) { /* reset your engine */ return snapshot(); },
  step(action, dt) { /* apply input and advance simulation */ return snapshot(); },
  snapshot() { return {score: 0, time: 30, lives: 3, status: "running"}; }
};
```

The sample above describes signatures only; wire the methods to your real
engine. `action` accepts `x` (horizontal position) and `tap` (boolean). `dt` is
simulation seconds. Return a serializable object with finite numeric score,
time and lives; time/lives are nonnegative. status is running/won/lost. Additional
fields are available for dotted-path assertions.

Disable your normal animation-driven simulation in deterministic test mode,
otherwise it races with explicit steps. Keep rendering active after steps for
screenshots. Seed your game's RNG in reset. Return copies, not mutable aliases.
DOM-only tests do not need this interface. Remote URLs are not rewritten by the
runner: pass the appropriate test-mode query string explicitly.
