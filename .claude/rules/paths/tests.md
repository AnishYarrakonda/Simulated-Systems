---
description: Conventions for the rule-check test suite
globs: ["tests/**/*.py"]
alwaysApply: false
---

# tests/

Checks pinning our rules against Primer's published source. `pytest`, no fixtures, no mocks.

Don't quote the test count here or anywhere else — it goes stale the moment a sim is added, and a
stale count reads as "someone deleted tests". `pytest tests/ -q` prints the real number.

## What belongs here

Tests that would fail on a **plausible wrong port** — not tests that restate the code. The bar:
"if someone reimplemented this from the video instead of the source, would this catch them?"

Good examples already present:
- the 1.2× predation boundary tested at 1.19 / 1.2 / 2.0 / 1.0
- the two independent survival/reproduction rolls (a shared roll passes a naive test)
- the `num_games` clamp across N<=T, T<N<2T, N>=2T, with "nobody vanishes" accounting
- mutation deltas being exactly {−0.1, +0.1} rather than Gaussian

Name Primer's constant in the assertion or the comment so the test doubles as documentation:

```python
assert c.sense_radius == 10 + 25 * 2.0  # EAT_DISTANCE + BASE_SENSE_DISTANCE * sense
```

## The `_load()` helper — don't remove it

Each sim has identically-named modules imported by bare name, so the module cache would serve
whichever sim imported first. `_load(sim_dir, names)` purges `sys.modules` and re-imports from a
clean slate. Every test goes through it.

Tests must pass **in isolation** as well as together — run a `-k` subset for one sim to confirm you
haven't introduced order dependence.

## What does NOT belong here

- Rendering tests. Tests can't tell you the arena drew anything — use the `verify` skill.
- The statistical dynamics checks (ESS convergence, orbit direction, trait drift). They take tens
  of seconds and are stochastic. They live in `/sim-check`, not pytest.
