# Plan: `aging_sim` — why we grow old

Port of Primer's diploid, sexually-reproducing creature sim and the deleterious-mutation model that
makes aging evolve out of nothing.

| | |
|---|---|
| **Video** | [Simulating the Evolution of Aging](https://www.youtube.com/watch?v=1_JbJTeLZJs) (2025-02-01) |
| **Primer's source** | `Primer-Learning/PrimerTools` (C#/Godot) → `Simulation/ContinuousSpaceTimeSims/Specific/CreatureSim/` |
| **Key files** | `CreatureSimSettings.cs` (96), `Genetics.cs` (207), `ReproductionStrategy.cs`, `Systems/CreatureSystem.cs` (370), `InitialPopulationGeneration.cs` (100), `TreeSim/FruitTreeSimSettings.cs` |
| **Archetype** | **Spatial + continuous-time.** Nearest to `natural_selection_sim`, but there is no day loop. |
| **Est. size** | **Large — 3–5× the other two plans.** Do it last. |

---

## 0. Read this first — the fidelity gap is real and it is the plan's central problem

Every other sim in this repo is pinned to source that *runs the shipped video*. This one cannot be,
and pretending otherwise would be the exact failure mode `.claude/rules/global/primer-fidelity.md`
exists to prevent.

What was verified by reading `main`:

- **The mechanism is complete and authoritative.** `DeleteriousTrait`, the diploid `Genome`, the
  expression mechanisms, `SexualReproduce`, and the per-step mortality formula are all fully present
  and unambiguous. Port them exactly.
- **The parameters are not.** `InitialPopulationGeneration.DefaultSpeedAndAwarenessDiploid` adds
  **no deleterious traits at all**, `MaxAge` is commented out, `DeleteriousMutationRate` defaults to
  `0`, and both default traits are constructed with `MutationIncrement: 0` — so on `main`, with
  defaults, **nothing mutates, nothing ages, and no creature ever dies of anything but starvation.**
  The sim is inert.
- **`AgingSimVideoSequence.cs` is ~80% commented out.** The repo is mid-refactor; the scene that
  produced the video no longer runs.

So the video's actual activation ages and mortality rates **are not in `main`**. Any number you pick
is *yours*, not Primer's. This breaks the repo's "defaults stay Primer's" rule, and the plan's job is
to make that break loud rather than silent.

### 0.1 Archaeology — do this before writing any code

Two leads, in priority order. **Do not skip to implementation.**

1. **Git history.** The video shipped 2025-02-01. Find the `PrimerTools` commit nearest that date and
   read `InitialPopulationGeneration.cs` and `AgingSimVideoSequence.cs` as they were *then*. That is
   the real authority and it very likely still exists in history.
   ```bash
   git clone https://github.com/Primer-Learning/PrimerTools && cd PrimerTools
   git log --until=2025-02-15 --oneline -- Simulation/ContinuousSpaceTimeSims/Specific/CreatureSim/
   git show <sha>:Simulation/ContinuousSpaceTimeSims/Specific/CreatureSim/InitialPopulationGeneration.cs
   ```
   Also check the `RockPaperScissors` repo — `InitialPopulationGeneration.cs` on `main` carries
   `using RockPaperScissors;`, so the two projects share code and the aging scene may live there.
2. **The commented-out code on `main` is strong evidence.** `InitialPopulationGeneration.cs:36–62`
   preserves the video's setup in comments:
   ```csharp
   // var maxAgeOptions = new float[] {20f, 40f, float.MaxValue};
   // genome.AddTrait(new Trait<float>("MaxAge", new List<float> { maxAgeOptions.RandomItem(rng) }, ...));
   // genome.AddTrait(new Trait<bool>("Antagonistic Pleiotropy Speed",
   //     new List<bool> { true, false }, alleles => alleles.RandomItem(rng), mutationIncrement: false));
   ```
   `{20, 40, float.MaxValue}` is almost certainly the video's MaxAge allele set (and note
   `ReferenceMaxAge = 20` corroborates it). Treat as *strong lead*, confirm against history, and
   **cite the line in the config comment** either way.

**If archaeology fails**, the fallback is explicit and documented, not quiet:

```python
# NOT PRIMER'S VALUE. The video's deleterious-trait parameters are not present in
# PrimerTools@main -- InitialPopulationGeneration adds no DeleteriousTraits, and
# AgingSimVideoSequence.cs is commented out. See docs/plans/aging_sim.md section 0.
# These are OUR choice, tuned to reproduce the selection shadow qualitatively.
# The MECHANISM (Genetics.cs) is Primer's and is exact; only the seeding is ours.
deleterious_activation_ages: tuple = (...)
```

And `README.md` must say so in the source table — e.g. a `mechanism only` footnote — rather than
implying the same fidelity as the other three.

---

## 1. What it models

Medawar's **selection shadow**. Creatures carry diploid deleterious alleles, each with an
`ActivationAge` and a mortality rate that only applies *after* that age. Selection can see an allele
that kills you at 5 — its carriers reproduce less. It can barely see one that kills you at 40,
because almost nobody survives to 40 anyway. So late-acting deleterious alleles drift to high
frequency and early-acting ones get purged, and **aging emerges** from a population that started
with no concept of it.

That's the payoff, and it's a genuinely different result from anything else in the repo. It's also
why this sim needs **age structure**, which forces the diploid/sexual machinery.

---

## 2. Verified constants — `CreatureSimSettings.cs:9–28`

```csharp
private const float DefaultCreatureStepMaxLength = 10f;
private const float DefaultMaxAccelerationFactor = 0.1f;
private const float DefaultCreatureEatDistance = 2f;
private const float DefaultCreatureMateDistance = 2f;
private const float DefaultEatDuration = 1.5f;
private const float DefaultMaturationTime = 2f;
private const float DefaultBaseEnergySpend = 0.1f;
private const float DefaultGlobalEnergySpendAdjustmentFactor = 0.2f;
private const float DefaultMinEnergyGainFromFood = 0.5f;
private const float DefaultMaxEnergyGainFromFood = 1.5f;
private const float DefaultReproductionEnergyThreshold = 2f;
private const float DefaultReproductionEnergyCost = 1f;
private const float DefaultHungerThreshold = 4f;
private const float DefaultReproductionDuration = 1f;
private const float DefaultReferenceCreatureSpeed = 5f;
private const float DefaultReferenceAwarenessRadius = 5f;
private const float DefaultReferenceMaxAge = 20f;
private const float DefaultMutationProbability = 0.1f;
private const float DefaultMutationIncrement = 1f;
private const float DefaultDeleteriousMutationRate = 0f;
```

Defaults also bind `Reproduce = ReproductionStrategies.SexualReproduce` and
`InitializePopulation = InitialPopulationGeneration.DefaultSpeedAndAwarenessDiploid` (`:93–94`).

⚠️ **`MutationIncrement` in settings appears to be dead.** `Genome.Mutate` reads
`floatTrait.MutationIncrement` — the *trait's* increment (`Genetics.cs:171`), not the settings value.
Since both default traits are built with increment `0`, the settings' `1f` never applies. Verify
before porting; if confirmed, port it as a **per-trait** field and note the settings field is unused.

---

## 3. The rules

### 3.1 Energy cost (`CreatureSystem.cs:255–265`)

```csharp
var normalizedSpeed = creature.MaxSpeed / ReferenceCreatureSpeed;                 // /5
var normalizedAwarenessRadius = creature.AwarenessRadius / ReferenceAwarenessRadius; // /5
var energyCost = (BaseEnergySpend + GlobalEnergySpendAdjustmentFactor *
                  (normalizedSpeed * normalizedSpeed + normalizedAwarenessRadius))
                 / SimulationWorld.PhysicsStepsPerSimSecond;
creature.Energy -= energyCost;
```

i.e. `cost_per_second = 0.1 + 0.2 · (speed² + awareness)`, on **normalised** traits.

⚠️ **This is not `natural_selection_sim`'s equation.** NS uses `size³ · speed² + sense`. Here it's
additive, there's no size, awareness is **linear** while speed is **squared**, and the traits are
divided by their reference values first. Do not let the two cores' cost functions be "unified" — the
guard hook already warns on `energy_cost|size \*\* 3|speed \*\* 2` and will fire here; the note must
distinguish the two sims.

### 3.2 The per-step mortality formula — the single most important line

`Genetics.cs:37–38`, with Primer's own comment:

```csharp
// Need to adjust for step size with an exponent to keep the results independent of step size (on average)
public float MortalityRatePerStep => 1 - Mathf.Pow(1 - MortalityRatePerSecond, 1f / SimulationWorld.PhysicsStepsPerSimSecond);
```

**The plausible wrong port is `rate / steps_per_second`.** It is linearly correct for small rates and
diverges badly for large ones, and it makes lifespan depend on your tick rate — which is precisely
what the exponent exists to prevent. This deserves a `primer-fidelity.md` entry and a dedicated test
(§7.2). It is this sim's `tie_cost`.

```csharp
public bool CheckForDeath(float age, Rng rng)
{
    if (!ExpressedValue || age < ActivationAge) return false;
    return rng.Random.NextDouble() < MortalityRatePerStep;
}
```

`DeleteriousTrait` is constructed with `ExpressionMechanisms.Bool.Dominant` and
`mutationIncrement: false`, and **throws unless it is diploid** (`:43–44`):

```csharp
if (alleles.Count != 2) throw new ArgumentException("DeleteriousTrait must be diploid (exactly 2 alleles)");
```

Dominant ⇒ `alleles.Any(a => a)` ⇒ **one bad allele is enough**. That's what makes the frequency
dynamics interesting; a recessive model gives a completely different answer.

### 3.3 Death, in order (`CreatureSystem.cs:320–360`)

```csharp
if (!creature.Alive)                                     return DeathCause.None;
if (creature.Energy < 0)                                 return DeathCause.Starvation;   // strictly < 0
var maxAgeTrait = creature.Genome.GetTrait<float>("MaxAge");
if (maxAgeTrait != null && maxAgeTrait.ExpressedValue < creature.Age)  return DeathCause.Aging;
foreach (var trait in creature.Genome.Traits.Values)     // every deleterious trait rolls, in order
    if (trait is DeleteriousTrait dt && dt.CheckForDeath(creature.Age, rng)) return DeathCause.Aging;
var apTrait = creature.Genome.GetTrait<bool>("Antagonistic Pleiotropy Speed");
if (apTrait is { ExpressedValue: true } && creature.Age > MaturationTime)
{
    var apDeathRate = 0.03f;                             // hardcoded, NOT in settings
    if (rng.Random.NextDouble() < 1 - Mathf.Pow(1 - apDeathRate, 1f / PhysicsStepsPerSimSecond))
        return DeathCause.Aging;
}
```

- `MaxAge` is **optional** — `GetTrait` returns null and the check is skipped. Keep it optional.
- Deleterious traits roll **sequentially and short-circuit** on the first hit. Each trait consumes an
  RNG draw only until one fires — so trait iteration order affects the RNG stream. Determinism
  requires a stable trait order (use an insertion-ordered dict).
- `apDeathRate = 0.03f` is an inline literal, not a setting. Lift it into `config.py` (that's what
  `config.py` is *for*), and comment that Primer hardcoded it.
- Death causes matter: the video's central chart is **death age by cause**. Keep the enum.

### 3.4 Mutation (`Genetics.cs:158–206`)

```csharp
case Trait<float> floatTrait:
    for each allele:
        if (rng < MutationProbability) {
            allele += rng < 0.5 ? -increment : +increment;   // fair coin, trait's own increment
            allele = Math.Max(0, allele);                    // clamped at 0, no upper bound
        }
case DeleteriousTrait dt:
    for each allele:
        if (rng < DeleteriousMutationRate) dt.Alleles[i] = !dt.Alleles[i];
case Trait<bool> boolTrait:
    if (boolTrait.MutationIncrement)                         // a BOOL used as an on/off switch
        for each allele: if (rng < MutationProbability) flip;
```

⚠️ **C# pattern-match order is the rule.** `DeleteriousTrait : Trait<bool>`, so the `DeleteriousTrait`
case *must* be tested before `Trait<bool>`. Python has no such dispatch — you must reproduce the
ordering by hand with explicit `isinstance` checks in the same sequence. Getting it backwards makes
deleterious alleles mutate at `MutationProbability` (0.1) instead of `DeleteriousMutationRate` (0) —
a silent 10%-per-allele flip that would swamp the selection shadow entirely. **Test it (§7.4).**

Note `Trait<bool>.MutationIncrement` is a *bool* used as "may this mutate at all", not an increment.
Ugly, faithful, comment it.

### 3.5 Sexual reproduction (`ReproductionStrategy.cs`)

```csharp
foreach (var traitName in genome1.Traits.Keys.Intersect(genome2.Traits.Keys))
{
    var currentParentIndex = rng.RangeInt(0, 2);         // random start parent
    var newAlleles = new List<float>();
    for (var i = 0; i < floatTrait1.Alleles.Count; i++)
    {
        var parentTrait = parentGenomes[currentParentIndex].Traits[traitName] as Trait<float>;
        newAlleles.Add(parentTrait.Alleles.RandomItem(rng));   // random allele from that parent
        currentParentIndex = 1 - currentParentIndex;           // then alternate
    }
    newGenome.AddTrait(new Trait<float>(traitName, newAlleles, floatTrait1.ExpressionMechanism, floatTrait1.MutationIncrement));
}
newGenome.Mutate(rng);
```

- One allele from each parent, in a **random order**, each drawn at random from that parent's pair.
  Standard Mendelian sampling.
- `Intersect` ⇒ **a trait present in only one parent is silently dropped.** Harmless while every
  creature has the same trait set, lethal if you ever add per-lineage traits. Comment it.
- The child's `DeleteriousTrait` is rebuilt via `CreateNew` inheriting **`deleteriousTrait1`'s**
  `ActivationAge` and `MortalityRatePerSecond` — parent 1's, arbitrarily. Fine while those are
  per-locus constants; a trap if they ever vary.
- `Mutate` runs **once, on the finished child genome**.
- Reproduction costs `ReproductionEnergyCost / 2` charged to **each** parent
  (`CreatureSystem.cs:148–149`), so the total is 1 and it's split.
- `IsOpenToMating`: `Energy >= ReproductionEnergyThreshold (2)` and mature (`Age >= MaturationTime`).

---

## 4. The port decision — do not port Godot

`CreatureSystem` is built on Godot's physics server: area collisions for detection, `deltaTime`
stepping, a `SimulationWorld` with `PhysicsStepsPerSimSecond`. **Do not reproduce that.** Port to a
fixed-timestep discrete loop, exactly as `natural_selection_sim` already does for `natural_sim.py`.

Decisions to make and comment:

1. **`PhysicsStepsPerSimSecond`.** Read the real value from `SimulationWorld.cs` (not fetched here —
   **do this first**, the mortality formula depends on it). Expose it as `steps_per_second` in
   `config.py`. The §3.2 exponent makes results step-size independent, so this is a fidelity knob,
   not a correctness one — and §7.2 tests exactly that.
2. **Collision detection → distance checks.** `CreatureEatDistance = 2`, `CreatureMateDistance = 2`
   in a `100 × 50` world (`AgingSimVideoSequence.cs:56`). Naive O(N²) is fine at video scale; measure
   before optimising (`.claude/rules/languages/python.md`).
3. **The `TreeSim`.** Creatures eat fruit from trees that grow on a schedule. That's a whole second
   system (`FruitTreeSimSettings.cs`, `TreeSystem.cs`, `FruitSystem.cs`). **Phase it** — §6 starts
   with uniformly scattered food and adds trees only if the dynamic needs them.
4. **No day loop.** There is no dawn/dusk, no going home, no `begin_day`/`finish_day`. Creatures live
   continuously and die whenever. The `arena.PHASES` tween and `Walker` **do not apply**. The frame
   loop advances `max(1, int(arena.speed))` steps, like NS's, but there is no day boundary to
   synchronise graphs to — pick a `record_interval` (in sim-seconds) and emit `DaySummary` on it.
   Reuse `DaySummary` with `day=` carrying the sim-time tick; it's the wrong field name but the right
   shape, and inventing a parallel event type is worse.

---

## 5. Files to create

```
aging_sim/
  config.py       # every constant in section 2, plus the OURS-not-Primer's block
  genome.py       # Trait, DeleteriousTrait, expression mechanisms, Genome, Mutate  <-- NEW module name
  creature.py     # CreatureComponent port: age, energy, position, state, genome
  environment.py  # the world: step(), eat, mate, death, recording
  main.py         # CLI + two windows
```

⚠️ **`genome.py` is a new core module name.** It **must** be added to `_SHARED_NAMES` in
`tests/test_rules.py` or the module cache will serve it to other sims:

```python
_SHARED_NAMES = ("config", "creature", "environment", "genome", "individual", "patch", "simulation")
```

This is the only plan of the three that touches `_SHARED_NAMES`. Don't forget it — the failure mode is
~26 confusing unrelated test failures (`.claude/rules/languages/python.md`).

---

## 6. Build order — strictly phased, each phase independently verifiable

This is a large port. Do **not** try to land it in one go.

**Phase 1 — genetics, headless, no world.** `genome.py` only: `Trait`, `DeleteriousTrait`, the four
float + three bool expression mechanisms, `Genome.Mutate`, `SexualReproduce`. This is pure logic with
no world, and it is where every subtle rule lives. Write §7.1–§7.6 now; they should all pass before a
single creature exists. **Highest value per line in the whole plan.**

**Phase 2 — the world, no aging.** `creature.py` + `environment.py`: movement, energy spend, eating
scattered food, mating, starvation death. No deleterious traits. Acceptance: a population with
`MutationIncrement = 0` is demographically stable — it neither explodes nor dies out. If it can't
hold steady, the energy/food balance is wrong and every later result is noise.

**Phase 3 — trait evolution.** Give `MaxSpeed`/`AwarenessRadius` a non-zero `MutationIncrement`.
Acceptance: speed/awareness drift toward whatever the food density rewards — the NS-style sanity
check. Confirms selection actually works before you ask it to do something subtle.

**Phase 4 — aging.** Add `DeleteriousTrait`s at a spread of activation ages (§0.1). Acceptance: the
selection shadow (§8). **This is the phase that can fail for real** — if the parameters are wrong,
you get no shadow and no signal about why.

**Phase 5 — rendering + gate.** `main.py`, graphs, arena; then the `verify` skill on a real frame,
`/sim-check`, docs.

**Phase 6 (optional) — `TreeSim`.** Only if Phase 4's dynamic demonstrably needs clustered food.

---

## 7. Tests to add — `tests/test_rules.py`

Banner + `def _age(): return _load("aging_sim", ("config", "genome", "creature", "environment"))`.

1. `test_deleterious_trait_must_be_diploid` — 1 or 3 alleles raises. Pins `Genetics.cs:43`.
2. `test_mortality_rate_per_step_uses_the_exponent` — **the important one.**
   `rate=0.5, steps=10` ⇒ `1 - 0.5**0.1 ≈ 0.0670`, *not* `0.05`. Then the property that justifies it:
   simulate to a fixed sim-time at `steps=10` and `steps=100` and assert the survival curve matches
   within noise. A `rate / steps` port passes the first assertion's shape and **fails the second**.
3. `test_deleterious_expression_is_dominant` — `[True, False]` ⇒ expressed. `[False, False]` ⇒ not.
   A recessive port (`All`) passes a `[True, True]`-only test.
4. `test_deleterious_alleles_mutate_at_deleterious_rate_not_mutation_probability` — the §3.4
   dispatch-order trap. `MutationProbability=1.0`, `DeleteriousMutationRate=0.0` ⇒ deleterious
   alleles **never** flip while float traits always mutate. This is the single highest-value test here.
5. `test_no_death_before_activation_age` — boundary at `age = ActivationAge - ε` (no death, and
   **no RNG draw consumed**) and `+ ε`.
6. `test_float_allele_clamped_at_zero_with_no_upper_bound` — `Math.Max(0, allele)`.
7. `test_sexual_reproduction_takes_one_allele_from_each_parent` — parent A `[1,1]`, parent B `[9,9]`
   ⇒ child is always `[1,9]` or `[9,1]`, never `[1,1]`. Catches a clone-one-parent port.
8. `test_traits_present_in_only_one_parent_are_dropped` — pins the `Intersect`.
9. `test_energy_cost_squares_speed_and_not_awareness` — `speed=10, awareness=5` ⇒
   `0.1 + 0.2*(2² + 1) = 1.1` per second. Catches anyone importing NS's `size³·speed²+sense`.
10. `test_reproduction_cost_is_split_between_parents` — each pays `1/2`, total `1`.
11. `test_death_check_order` — a creature that is both starving and past `MaxAge` reports
    **`Starvation`** (energy is checked first).
12. `test_starvation_is_strictly_below_zero` — `Energy == 0` survives.

---

## 8. The emergent dynamic — and how it can lie to you

**The selection shadow:** plot the final frequency of each deleterious allele against its
`ActivationAge`. It must be **increasing** — late-acting alleles common, early-acting rare.

The measurement traps, which matter more here than in any other sim:

- **Drift will fake it.** Deleterious alleles at high activation ages are nearly neutral, and nearly
  neutral + finite population = random walk. A single run showing high late-allele frequency proves
  nothing. Run **many seeds** and test that the *slope* is positive and seed-independent — the same
  discipline `dynamics-analyst` applies to the RPS orbit, and the same reason RPS needs n≥3000.
- **Include a control.** An allele with `ActivationAge = 0` and one at `ActivationAge > max observed
  lifespan` bracket the effect. The first must be purged; the second must drift freely. If the
  bracket doesn't separate, you have no signal and tuning the middle is pointless.
- **Population size is the confound.** Selection strength scales with `N`; the shadow needs `N` large
  enough that early-acting alleles are actually purged rather than lost to drift. If Phase 4 shows
  nothing, **raise `N` before touching any rule.**

---

## 9. The gate — `/sim-check`

Add a stage to `.claude/commands/bash/sim-check.sh`, renumber, and keep it cheap:

```bash
echo ""
echo "N/N  aging: the selection shadow (late-acting alleles outlive early-acting ones)"
# Slope of final allele frequency vs. activation age must be positive.
# Averaged over seeds -- a single seed is drift, not signal.
```

**Budget warning.** This sim is continuous-time with O(N²) neighbour checks; it will be the slowest
thing in the repo by a wide margin. The gate must stay under ~60s or it stops being run. If the
honest check can't fit, put a **reduced** version in `sim-check.sh` and the full multi-seed sweep in a
`docs/` note that the `dynamics-analyst` agent runs on demand. Do not silently shrink it into
meaninglessness — `.claude/rules/global/workflows.md` is explicit that the statistical check, not
pytest, is what catches a wrong port.

---

## 10. Docs to update

- **`README.md`** — source-table row **with the mechanism-only caveat from §0**, a "### Aging"
  section, and the death-cause colours.
- **`CLAUDE.md`** — `aging_sim/` in *Where things live*; note it's the only sim without a day loop.
- **`.claude/rules/global/primer-fidelity.md`** — **already landed:** `Primer-Learning/PrimerTools` is
  now in the authority chain, and the `main`-is-mid-refactor caveat (no `DeleteriousTrait`s, `MaxAge`
  commented out, `MutationIncrement: 0`) is recorded with the "ours, not Primer's" rule. Still to add
  once the port exists:
  - The `MortalityRatePerStep` exponent under **Constants that are load-bearing**, with the
    "`rate / steps` is the plausible wrong port" warning.
  - The §3.4 pattern-match ordering trap.
- **`.claude/hooks/pre-generation/primer-fidelity-guard.sh`** — a `note` for
  `mortality_rate|activation_age|deleterious`, warning against linearising the exponent. Also update
  the existing `energy_cost|size \*\* 3|speed \*\* 2` note, which will now fire on `aging_sim` with
  advice meant for `natural_selection_sim` (§3.1).
- **Test count:** nothing to do — the hardcoded `36` is already gone from all seven files. Don't
  reintroduce a number.

---

## 11. Honest recommendation

Build `sacrifice_sim` and `population_sim` first. They are faithful, cheap, and each has a crisp
analytic check. Come to `aging_sim` afterwards, and **start with §0.1 archaeology** — if the video's
parameters turn up in git history, this becomes a normal (if large) port. If they don't, it becomes a
reconstruction, and the repo should say so out loud rather than quietly implying a fidelity it
doesn't have.

The mechanism is worth porting either way: diploid sexual genetics with dominance is an axis no other
sim here has, and `genome.py` is reusable.
