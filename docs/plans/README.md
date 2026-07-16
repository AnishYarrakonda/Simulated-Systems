# Plans — the next three sims

Three Primer simulations researched and specced for implementation. Each plan is written against the
existing repo's conventions and is meant to be executable in a later session without re-doing the
research.

Read `.claude/rules/global/primer-fidelity.md` first. The point of these plans is that the rules match
Primer's published source, and every plan quotes that source with file and line.

| Plan | Video | Primer's source | Archetype | Size |
|---|---|---|---|---|
| [`sacrifice_sim`](sacrifice_sim.md) | [Sacrificing for Family](https://www.youtube.com/watch?v=iLX_r_WPrIw) (2021) | `primerpython` `tools/natural_sim.py` | spatial (extends NS) | medium |
| [`population_sim`](population_sim.md) | [Competition and Logistic Growth](https://www.youtube.com/watch?v=uRTtlpD_U54) (2018) | `primerpython` `tools/population.py` + `constants.py` — one core, four scenes | tick-based, non-spatial | small–medium |
| [`aging_sim`](aging_sim.md) | [The Evolution of Aging](https://www.youtube.com/watch?v=1_JbJTeLZJs) (2025) | `Primer-Learning/PrimerTools` `CreatureSim/` | spatial, continuous-time | large |

**Recommended order: `population_sim` → `sacrifice_sim` → `aging_sim`**, easiest and most analytically
checkable first.

## Why these three

The selection rule was: **a shipped video *and* published source.** Both are required. The video gives
an emergent dynamic to validate against (which is what `/sim-check` tests, and the only thing that
catches a wrong port); the source gives the rules. Candidates that have one but not the other were
rejected:

| Rejected | Why |
|---|---|
| **Centipede** (`tools/centipede.py`) | Source is complete and clean, but **no video and no scene imports it**. It's an abandoned experiment, so there is no dynamic on tape to check a port against. Cheap to build if you want it anyway — full round-robin, two integer genes, ~150 lines. |
| **Teamwork** | Video exists; **no source in either repo**. `EvoGameTheorySim.cs` is hardcoded to RPS and is not a retargetable payoff engine. Porting this from a summary would violate the authority chain — it needs the video watched and specced by hand. |
| **`hawk_dove_basic.py`** | A *variant* of the existing hawk/dove with fixed-population, score-proportional reproduction (11 buckets, `DEFAULT_NUM_CREATURES = 11000`). Belongs as a `--reproduction score-proportional` **mode** on `dove_hawks_sim`, not a fourth sim. Independently confirms `SUCKER_FRACTION = 1/4`. |
| **`market_sim.py`** | Fully published supply/demand price discovery, but no reproduction, mutation, or fitness. It's economics, not evolution — off-thesis, and it shares nothing with the `Individual`/`Patch` shape. `Helpsypoo/primereconomy` (Unity) is the same story. |

## Two findings that changed the repo's rules

Both are **already applied** to `.claude/rules/global/primer-fidelity.md` — read the file map there,
not this summary, when you start a port.

1. **The altruism sim is `natural_sim.py`, not `hamilton_basic.py`.** Two independent research passes
   recommended `hamilton_basic.py` for the Sacrifice video. It is imported by **no** video scene —
   `video_scenes/inclusive_fitness.py` imports `natural_sim`, and its `hamilton()` scene plots
   `graph_type = 'kin_altruist'`, a trait defined in `natural_sim.py`. The shipped sim is therefore
   **spatial**, and `sacrifice_sim` is a trait layer on the natural-selection core. See
   [`sacrifice_sim.md` §0](sacrifice_sim.md).

2. **The authority chain was incomplete.** It mapped only `natural_sim.py`, `hawk_dove.py` and
   `EvoGameTheorySim.cs`. It now covers `tools/population.py`, `tools/creature.py`, `constants.py`,
   `tools/market_sim.py`, `tools/hawk_dove_basic.py`, the two unshipped files
   (`hamilton_basic.py`, `centipede.py`), and the whole **`Primer-Learning/PrimerTools`** repo — a
   third source repo, and the only home of the Aging sim.

   The general rule it now carries: **a file existing in `tools/` doesn't mean it shipped.**
   `video_scenes/` is what settles it. That test is what caught finding #1.

## Verification status

Everything in these plans was read from raw source, not from summaries. Line counts, constants and
formulas were quoted directly from `raw.githubusercontent.com`.

The `population_sim` model was additionally checked against Primer's own graph axes: his shipped
`sim_summary` scene (`r=0.03, d=0.018`, 60 ticks, 10 creatures) predicts ~20.5 against his
`y_range=[0,30]`, and `last_video` (`r=0.04, d=0.01`, 100 ticks, 5 creatures) predicts ~100 against
his `y_range=[0,60]`. Both land inside his ranges, which is independent confirmation that the
crowding term is understood correctly.

**One caveat, flagged loudly:** `aging_sim`'s *mechanism* is authoritative but its *parameters* are
not — `PrimerTools@main` is mid-refactor and the video's deleterious-trait setup is commented out.
[`aging_sim.md` §0](aging_sim.md) opens with git archaeology to recover them and specifies exactly how
to document the gap if that fails.
