# Conventions

No formatter or linter is wired up. Match the surrounding code by hand.

## Style

- 4-space indent, ~92 col soft limit, double quotes, `snake_case`.
- Stdlib imports first, then third-party, then local — matching the existing files.
- Dataclasses for config; plain classes for entities.
- No type annotations in sim cores (the existing code has none). `config.py` uses them lightly for
  dataclass fields. Don't retrofit annotations onto untyped code as a drive-by.

## Comments — the important one

Comments explain **why**, and specifically why a value is what it is. This repo's whole risk is
someone "correcting" a correct constant, so a comment that pins a value to Primer's source is
doing real work:

```python
# Primer's cost equation: size^3 * speed^2 + sense, charged per step.
# The cubic on size and the square on speed are what make big and fast
# expensive enough to trade off against their benefits.
```

Don't write comments that restate the code (`# increment the day`), narrate the diff
(`# changed from Gaussian`), or address a reviewer. Do write them when a value is load-bearing,
non-obvious, or would look like a bug to someone who hasn't read Primer's source.

Where a constant comes from Primer, name his constant:

```python
mutation_chance: float = 0.05   # MUTATION_CHANCE, rolled per trait
fight_cost: float = 16 / 16     # FIGHT_COST = 1.0
```

## Naming

- Mirror Primer's vocabulary so his source stays greppable: `fight_chance`, `sense` (not
  `vision`), `energy_cost`, `num_games`, `tie_cost`, `win_magnitude`, `homebound`.
- `Patch` = a bush (hawk/dove) or a mango tree (RPS). Kept generic because both share the shape.
- Config fields are named after Primer's constants, lowercased.

## Config

Every Primer constant is a `config.py` dataclass field defaulted to **his** value, threaded through
as `self.config`. Never hardcode a rule constant inside logic — if it's a number Primer chose, it
belongs in `config.py` with a comment naming his constant.

Each `main.py` exposes the fields as CLI flags via argparse and takes `--no-render` + `--seed`.

## Randomness

Every sim takes a `seed` and owns a `random.Random(seed)` on the sim object, passed to entities as
`self.rng`. **Never call the module-level `random.*` in sim logic** — it breaks reproducibility,
and the statistical checks depend on seeded runs.

## Tests

`pytest`, all in `tests/test_rules.py`, no fixtures. Tests pin rules against Primer's source and
name the source constant in the assertion. Prefer a test that would fail on a *plausible* wrong
port (the 1.2× boundary, the two independent rolls, the `num_games` clamp) over one that restates
the code.

They must pass in isolation as well as together — `_load()` purges `sys.modules` between sims.

## Done means

`/sim-check`: pytest **plus** the statistical checks. A wrong port passes the unit tests happily —
only the emergent dynamic catches it. And if you touched rendering, actually look at a frame; the
tests say nothing about whether the arena drew anything.
