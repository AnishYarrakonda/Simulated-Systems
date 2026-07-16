---
description: Rules for the headless simulation cores — the layer that owns Primer's rules
globs: ["*_sim/creature.py", "*_sim/environment.py", "*_sim/individual.py", "*_sim/patch.py", "*_sim/simulation.py", "*_sim/config.py"]
alwaysApply: false
---

# Sim cores (headless layer)

This layer owns the rules. It must stay renderable-agnostic and deterministic under a seed.

## Hard constraints

- **No `import pygame`, no `import matplotlib`.** Ever. If you need something on screen, emit an
  event (`primer_common/events.py`) and let the arena/feed render it.
- **No `print()`.** Emit an event instead — that's what the play-by-play consumes.
- **No module-level `random.*`.** Use `self.rng` (a seeded `random.Random`). Reproducibility is
  what the statistical checks stand on.
- **No rule constants inline.** They live in `config.py`, defaulted to Primer's value, commented
  with his constant name.

## Determinism

Same seed + same config must give the same result. That means no iteration over unordered sets
where order affects outcome, and no wall-clock or PID-derived randomness.

## What "correct" means here

Not "the tests pass" — a wrong port passes the unit tests. Correct means the **emergent dynamic**
matches Primer's: the 50/50 ESS, the inward spiral, the speed drift. See
@.claude/rules/global/primer-fidelity.md.
