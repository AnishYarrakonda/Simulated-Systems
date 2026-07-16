# Primer simulations

Three evolution simulations — natural selection, hawk/dove, and rock/paper/scissors — rebuilt to
match how [Primer](https://www.youtube.com/c/primerlearning) (Justin Helps) actually implemented
them. Each runs a headless sim core and renders two windows: a pygame arena with a live
play-by-play feed, and a matplotlib window of graphs. Personal project, active development.

## Core mandates (never violate)

- **Primer's source is the authority — not the videos, not summaries, not replicator theory.**
  Rules here are ported from Primer's published code
  ([`primerpython`](https://github.com/Helpsypoo/primerpython),
  [`RockPaperScissors`](https://github.com/Primer-Learning/RockPaperScissors)). If a change to a
  Primer-derived constant is proposed, check it against that source before touching it. Web
  summaries of these videos are frequently wrong — one cost us a near-miss regression (see below).
- **`tie_cost > 0` spirals INWARD.** This is the single most likely thing to get "helpfully"
  broken. A widely-repeated claim says `tie_cost=0.5` is unstable/outward. It is not — verified
  analytically and empirically at n=3000. Do not "fix" it. See
  @.claude/rules/global/primer-fidelity.md.
- **Never correlate the survival and reproduction rolls.** Primer draws two independent
  `random()`s. Sharing one roll silently distorts the equilibrium without raising anything.
- **Sim cores stay headless.** Rule logic must never import pygame or matplotlib. That split is
  what makes the rules testable and is how Primer structures his own code.
- **Verify by running, not by asserting.** A passing test suite does not prove the arena renders
  or the feed populates. Both have broken while tests stayed green.

## Stack

Python 3.13, `pygame-ce` (arena), `matplotlib` (graphs), `numpy`. No venv — deps are installed
system-wide. `pip install -r requirements.txt`.

## Where things live

- `natural_selection_sim/` — continuous 300×300 world; `creature.py`, `environment.py`
- `dove_hawks_sim/` — bush pairing; `individual.py`, `patch.py`, `simulation.py`
- `rps_sim/` — mango-tree pairing; same trio of files
- `primer_common/` — shared: `palette` (Primer's colours), `events`, `feed` (play-by-play),
  `arena` (pygame), `graphs` (matplotlib, incl. the ternary plot)
- `tests/test_rules.py` — the rule checks against Primer's source
- Each sim owns a `config.py` dataclass holding every tunable, defaulted to Primer's value.

Each sim has its own `config.py`/`individual.py`/`patch.py`/`simulation.py` and imports them by
**bare name**, so they only resolve when run from inside that sim's folder. See
@.claude/rules/global/architecture.md.

## Detailed rules (auto-loaded)

@.claude/rules/global/primer-fidelity.md
@.claude/rules/global/architecture.md
@.claude/rules/global/conventions.md
@.claude/rules/global/workflows.md

## Working here

- Commands: `/sim <name> [flags]` — run a sim with windows; `/sim-check` — the validation gate.
- Agents: `primer-fidelity-auditor` (does our rule match Primer's source?), `sim-verifier`
  (do the windows actually render?), `dynamics-analyst` (what dynamic emerges?).
- Skills: `verify` — how to drive the windows offscreen and what to look for.
- **Validate before pushing:** `/sim-check` (pytest + the statistical checks). Unit tests alone
  are not the gate — a wrong port passes them while producing the wrong dynamic.
