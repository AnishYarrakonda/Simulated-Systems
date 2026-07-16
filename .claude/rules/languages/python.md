---
description: Python conventions for this repo
globs: ["**/*.py"]
alwaysApply: false
---

# Python

Python 3.13. No formatter, no linter, no venv — deps installed system-wide via
`requirements.txt`. Match surrounding style by hand.

## The import quirk you will hit

Each sim has its own `config.py` / `individual.py` / `patch.py` / `simulation.py` and imports them
**by bare name**. So:

- A sim only runs from **inside its own folder** (`cd rps_sim && python3 main.py`).
- `main.py` does `sys.path.insert(0, <repo root>)` so `primer_common` resolves.
- Two sims cannot be imported into one process without purging `sys.modules` — which is exactly
  what `tests/test_rules.py::_load()` does. Without it the module cache serves whichever sim
  imported first, and you get 26 confusing failures. Don't "simplify" that helper away.

Renaming the modules to be unique would remove the quirk, but each sim is meant to stay standalone
and mirror Primer's own per-video layout.

## Idioms in use

- `@dataclass` for config; plain classes for entities.
- `__slots__` where objects are numerous and hot (`Food`).
- `math` over `numpy` in per-step hot paths — the sims are step-loop bound, and numpy's per-call
  overhead loses at this scale. numpy is only a `requirements.txt` leftover; nothing imports it now.
- Class-level `_next_id` counters with a `reset_ids()` classmethod, so seeded runs give stable ids.

## Performance

The inner loop is `environment.step()`, which is O(creatures × food) per step with ~400+ steps a
day. It's fine at these sizes; don't add per-step allocation or per-step logging. If you need to
speed it up, a spatial hash on food is the obvious first move — but measure before doing it.
