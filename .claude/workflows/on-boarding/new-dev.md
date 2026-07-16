# Onboarding — get running and make a first correct change

**Use when:** setting this repo up fresh, or picking it back up after a long gap.

## Phase 1 — Run something

```bash
pip install -r requirements.txt          # pygame-ce, matplotlib, numpy. No venv.
cd dove_hawks_sim && python3 main.py     # start here: fastest to show its point
```

Two windows open. The arena shows blue doves and red hawks walking to green bushes, pairing up and
resolving; the feed underneath prints each contest (`hawk#8 vs dove#47 -> 1.5 / 0.5`). The graph
window plots doves vs. hawks converging toward 50/50.

Keys: `space` pause, `+`/`-` speed, `q` quit.

Then try `/sim rps` (watch the ternary plot spiral inward) and `/sim ns` (creatures foraging a real
continuous world, turning grey when they reach the edge safely).

## Phase 2 — Understand the one idea

Every sim is **a headless core plus a renderer**. The core owns Primer's rules, emits events, and
imports no pygame or matplotlib. `primer_common/` consumes those events and draws.

That's why `--no-render` works on all three, why `tests/` can check every rule without a window,
and why you must never put rule logic in a rendered path.

Read `.claude/rules/global/architecture.md`, then `primer-fidelity.md`. The second one matters
more than it looks: several constants here look wrong to anyone who hasn't read Primer's source,
and the repo's main risk is someone "fixing" a correct value. **If you read one thing, make it the
tie_cost section.**

## Phase 3 — Make a change

1. Find Primer's rule in his source (`primer-fidelity.md` has the file map), or ask the
   `primer-fidelity-auditor` agent. Don't trust a summary — several are wrong.
2. Add the constant to that sim's `config.py`, defaulted to **his** value, commented with his
   constant name.
3. Implement in the core. Headless. Seeded `self.rng`, never module-level `random`.
4. Add a test to `tests/test_rules.py` that would fail on a *plausible* wrong port.
5. Add an event in `primer_common/events.py` if it should appear in the play-by-play.
6. `/sim-check`.

## Done criteria

- `/sim-check` passes: the rule checks, hawk/dove coexistence from both directions, NS speed drift,
  RPS orbit direction.
- If you touched rendering, you **looked at a frame** — use the `verify` skill. Tests say nothing
  about whether anything drew.

## Gotchas that will bite you

- A sim only runs from **inside its own folder** — the modules import by bare name.
- Two sims can't be imported into one process without purging `sys.modules` (`tests/_load()`).
- NS at 70 days ≈ 40s; don't chain three seeds into one command.
- RPS orbit direction needs **n>=3000**; at n=800 drift reads backwards.
