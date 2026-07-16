# Workflows

## Setup

```bash
pip install -r requirements.txt     # pygame-ce, matplotlib, numpy — no venv
```

## Run a sim (two windows)

Always from inside the sim's folder — the bare-name imports depend on it.

```bash
cd natural_selection_sim && python3 main.py
cd dove_hawks_sim       && python3 main.py
cd rps_sim              && python3 main.py
```

Or `/sim natural_selection`, `/sim rps --tie-cost 0`.

Arena keys: `space` pause, `+`/`-` speed, `q`/`esc` quit. `--help` on any sim lists every knob.

## Run headless

```bash
python3 main.py --no-render --days 60 --seed 1
```

Prints a summary and no windows. This is how you check dynamics.

## Test

```bash
python3 -m pytest tests/ -q          # the rule checks, ~0.1s, from the repo root
```

## The validation gate — `/sim-check`

pytest **plus** the statistical checks below. Unit tests alone are not sufficient: a wrong port
passes them and produces the wrong emergent dynamic. These are the checks that actually catch it.

```bash
# hawk/dove reaches the 50/50 ESS from both directions (expect ~50%, ±6)
cd dove_hawks_sim
python3 main.py --no-render --days 120 --doves 10 --hawks 150 --seed 2    # -> ~55.7%
python3 main.py --no-render --days 120 --doves 150 --hawks 10 --seed 3    # -> ~54.3%

# natural selection: speed-only mutation drives speed up, others pinned
cd natural_selection_sim
python3 main.py --no-render --days 70 --seed 1 --no-mutate-size --no-mutate-sense
# -> avg speed ~1.4, size 1.00, sense 1.00

# RPS orbit direction (needs n>=3000; at n=800 drift swamps it)
# tie_cost 0.5 -> inward, 0 -> drift out, -0.5 -> outward
```

**Timing:** NS at 70 days takes ~40s; three seeds in one Bash call will blow a 2-minute timeout.
Run seeds one per call.

## Verifying the windows

Tests say nothing about whether anything rendered. Use the `verify` skill — it documents driving
the sims offscreen (`SDL_VIDEODRIVER=dummy`, `MPLBACKEND=Agg`) and capturing a frame, plus what to
look for in the arena, the feed, and each graph.

## Adding a rule

1. Read Primer's source for it (see @.claude/rules/global/primer-fidelity.md for the file map), or
   ask the `primer-fidelity-auditor` agent.
2. Add the constant to that sim's `config.py`, defaulted to Primer's value, commented with his
   constant name.
3. Implement in the sim core — headless, no rendering imports.
4. Add a test to `tests/test_rules.py` that would fail on a plausible wrong port.
5. Add an event type in `primer_common/events.py` if it should show in the play-by-play.
6. `/sim-check`.

## Git

No CI, no branch protection, no release process. `main` directly. `.gitignore` covers
`__pycache__/`, `.DS_Store`, `.idea/`, `.venv/`. If untracked junk starts appearing, check that
`.gitignore` still exists — it was deleted-but-unstaged once, which is exactly what that looks
like.
