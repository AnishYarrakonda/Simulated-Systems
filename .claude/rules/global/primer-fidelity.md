# Primer fidelity

The whole point of this repo is that the rules match Primer's. Every constant below was read from
his published source. If you're about to change one, read this first.

## The authority chain

1. **Primer's source code** — the only authority. Three repos, not two:
   - [`Helpsypoo/primerpython`](https://github.com/Helpsypoo/primerpython) — the Blender era.
     Rules live in `blender_scripts/tools/`; `video_scenes/` says which ones actually shipped.
   - [`Primer-Learning/RockPaperScissors`](https://github.com/Primer-Learning/RockPaperScissors)
     (`EvoGameTheorySim.cs`) — the 2024 video, Godot/C#. `addons/Old sims/SimRunner*.cs` are earlier
     drafts of the same sim; no new rules.
   - [`Primer-Learning/PrimerTools`](https://github.com/Primer-Learning/PrimerTools) — the current
     C#/Godot toolkit, and the **only** source for the 2025 Aging sim
     (`Simulation/ContinuousSpaceTimeSims/Specific/CreatureSim/`). Actively refactored, so pin a
     commit near the video's date rather than reading `main`.
2. **The videos** — useful context, but the code is what shipped. Where the narration and the code
   disagree, the code wins. (Hawk-vs-hawk is *narrated* as risky fighting; the code applies a
   deterministic `FIGHT_COST = 1.0` with no injury roll.)
3. **Everything else** — blog posts, AI summaries, "evolutionary game theory says…". Treat as
   leads to verify, never as evidence. Several are outright wrong.

### The file map — and which files are not authority

A file existing in `tools/` does **not** mean it shipped. `video_scenes/` is what settles it: if no
scene imports a tool, it is an abandoned experiment with no dynamic on tape, and it cannot be used to
justify a rule.

| File | Video | Status |
|---|---|---|
| `tools/natural_sim.py` | Natural Selection (2018), **Sacrificing for Family (2021)** | shipped — `video_scenes/natural_selection.py`, `inclusive_fitness.py` |
| `tools/hawk_dove.py` | Aggression (2019) | shipped — `video_scenes/aggression.py` |
| `tools/population.py` + `tools/creature.py` + `constants.py` | Logistic Growth (2018) and the replication/mutation segments | shipped — imported by exactly four scenes: `logistic_growth.py`, `replication_only.py`, `mutations.py`, `fecal_transplant.py`. **Not** `why_things_exist.py`, which imports `creature` and `drawn_world` only and never touches the `Population` engine. |
| `tools/market_sim.py` | Supply and Demand | shipped — `video_scenes/supply_and_demand.py`. Economics: no reproduction, mutation, or fitness. |
| `EvoGameTheorySim.cs` | Rock/Paper/Scissors (2024) | shipped |
| `PrimerTools` `CreatureSim/` | Aging (2025) | shipped, but see the caveat below |
| `tools/hawk_dove_basic.py` | — | **variant**, not imported by `aggression.py`. Fixed population, score-proportional reproduction over 11 buckets, `DEFAULT_NUM_CREATURES = 11000`. Independently confirms `SUCKER_FRACTION = 1/4`. A *mode*, not a sim. |
| `tools/hamilton_basic.py` | — | **NOT SHIPPED.** See below. |
| `tools/centipede.py` | — | **NOT SHIPPED.** No scene imports it, no centipede video exists. |

**`hamilton_basic.py` is not the source for "Sacrificing for Family".** It is a standalone
side-experiment that no scene imports, and two independent research passes have now recommended it
anyway — which is exactly why this row exists. The shipped altruism sim is **`natural_sim.py`**:
`video_scenes/inclusive_fitness.py` imports `natural_sim` and its `hamilton()` scene plots
`graph_type = 'kin_altruist'`, a trait defined in `natural_sim.py` alongside `HELP_REP_BOOST = 0.5`,
`FAMILY_JUMPS = 3` and `SAMARITAN_RATIO = 1.1`.

The consequence is structural, not cosmetic: the real sim is **spatial**. Altruism is a blob with two
food taking a detour to hand one to a starving relative, paying with its own certainty of
reproduction. It is not the abstract mating-chance transfer `hamilton_basic.py` models. Build the
spatial version — see @docs/plans/sacrifice_sim.md.

**`PrimerTools@main` cannot reproduce the Aging video.** The mechanism (`Genetics.cs`) is complete and
authoritative, but the seeding is not: `InitialPopulationGeneration` adds no `DeleteriousTrait`s,
`MaxAge` is commented out, `DeleteriousMutationRate` defaults to `0`, and both default traits are
built with `MutationIncrement: 0` — so nothing mutates and nothing ages. `AgingSimVideoSequence.cs` is
mostly commented out. Recover the video's parameters from git history near 2025-02-01; if that fails,
any value you pick is **ours, not Primer's**, and must be labelled that way rather than defaulted
silently. See @docs/plans/aging_sim.md.

## The tie_cost sign — do not "fix" this

`rps_sim` defaults to `tie_cost = 0.5`, which makes the population **spiral inward** to
(1/3, 1/3, 1/3). A common claim — including from confident-sounding research — is that
`ε = -tie_cost < 0` makes the interior equilibrium unstable, so it should spiral *outward*. That
reasoning is wrong.

Derivation. Payoffs are `A = C - tie_cost*I`, where `C` is the zero-sum cyclic RPS matrix. Take
`V = x_r * x_p * x_s`. Since `C` is antisymmetric with zero column sums, `x·Cx = 0` and
`sum((Cx)_i) = 0`, so:

```
d(ln V)/dt = tie_cost * (3 * sum(x_i^2) - 1)  >= 0   for tie_cost > 0
```

`sum(x_i^2) >= 1/3` with equality only at the centre, so V strictly increases toward the centre.
V peaks at the centre ⇒ **positive tie_cost is stabilising**.

Intuition: paying to tie means a *common* strategy meets itself often and pays for it. That's
negative frequency dependence, which favours rare strategies. Primer's scene is literally named
`FindStability`.

Measured (n=3000, radius from the simplex centre, 60 days):

| `tie_cost` | radius | behaviour |
|---|---|---|
| `-0.5` | 0.531 → 0.680 | outward |
| `0` | 0.372 → 0.466 | neutral orbit; drift walks a finite population out to fixation |
| `0.5` | 0.225 → 0.110 | **inward, stable** |

If you change this, re-measure at n>=3000 — at n=800 drift swamps the signal and you'll misread it.

## Constants that are load-bearing

**Natural selection** (`natural_sim.py`):
- `energy_cost = size^3 * speed^2 + sense`, per step. Exponents are not interchangeable — an
  earlier version had `0.02*(vision^3 + size^2 + speed)^0.15`, which inverts the trade-off.
- day length is **dynamic**: `max(ceil(STARTING_ENERGY(800) / energy_cost))` over all creatures.
- sense radius = `EAT_DISTANCE(10) + BASE_SENSE_DISTANCE(25) * sense`.
- predation at exactly `prey.size * 1.2 <= predator.size`; **prey is immune once home**; the prey's
  stomach contents transfer *plus* the prey itself counts as one food.
- eating caps at **2**. Reaching the edge with 0 food is **not** home — it still dies.
- mutation is **discrete**: 5% per trait, delta exactly ±0.1. Not Gaussian.
- homebound state **latches** and targets the **nearest wall**, not the start point.
- food is uniform over the **whole** world, not just the middle.

**Hawk/dove** (`hawk_dove.py`):
- share/share `1,1`; fight/share `1.5,0.5`; fight/fight `0,0`; alone `2`.
  Hawk-vs-dove is **not** `2/0` — the dove keeps a quarter. Coding it as 2/0 kills the doves and
  you get no equilibrium.
- survival and reproduction are **two independent rolls**.
- **no population cap.** Primer has none; a cap pins the population artificially.
- 121 creatures / 61 bushes ⇒ exactly one blob eats alone.
- Expect the **50/50 mixed ESS**: E[Dove]=1−0.5p, E[Hawk]=1.5−1.5p ⇒ p=0.5.

**RPS** (`EvoGameTheorySim.cs`):
- `num_games = clamp(N - trees, 0, trees)`; leftovers eat alone (2 offspring) if a tree is free,
  else starve. So N<=T ⇒ everyone doubles; N>=2T ⇒ the surplus starves.
- reward **is** expected offspring: `floor(r)` children plus one more with probability `frac(r)`.
- generations **do not overlap** — parents never survive.

## Changing a Primer constant

Allowed — they're all exposed as tunable params, which is the point. But:

1. Default values stay Primer's. Tune via `config.py` args or CLI flags, don't edit the default.
2. If you believe a default is wrong, check Primer's source before changing it, and say which file
   and line you checked.
3. Re-run `/sim-check`. The statistical checks — not the unit tests — are what catch a wrong port.
