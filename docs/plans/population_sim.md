# Plan: `population_sim` — competition, logistic growth, and the rules of evolution

Port of Primer's `Population` engine: replication, death, mutation, spontaneous generation, and the
crowding term that turns exponential growth into an S-curve.

| | |
|---|---|
| **Video** | [Simulating Competition and Logistic Growth](https://www.youtube.com/watch?v=uRTtlpD_U54) (2018-08-26) |
| **Primer's source** | `Helpsypoo/primerpython` → `blender_scripts/tools/population.py` (359 lines), `tools/creature.py` (17 lines), `constants.py` |
| **Video scenes** | `video_scenes/logistic_growth.py`, `replication_only.py`, `mutations.py`, `fecal_transplant.py` — verified as the complete set of importers |
| **Archetype** | **New: tick-based, non-spatial, no pairing.** Closest to `rps_sim` structurally, but there are no contests at all. |
| **Est. size** | Small–medium. The rules are ~80 lines of real logic. The work is in the data model. |

---

## 0. Why this one is worth doing first

**One core serves four scenes.** Primer's `gene_updates` mechanism retunes any gene property at any
tick, and that single hook is how he stages `logistic_growth.py`, `replication_only.py`,
`mutations.py` and `fecal_transplant.py` from the same engine. Porting `population.py` buys all four.

(Those four are the *verified complete* set of importers — grepped across all 18 scene files.
`why_things_exist.py` is **not** among them despite covering related ground: it imports `creature` and
`drawn_world` and never constructs a `Population`. An earlier draft of this plan claimed otherwise;
a fidelity audit caught it.)

It also fills a real gap: all three existing sims are **competitive** (creatures contest a scarce
resource). This one has no interaction at all — every creature independently rolls death and
replication, and the only coupling is through the population-wide crowding term. It's the repo's
first density-dependent sim, and it's where the S-curve comes from.

---

## 1. Verified constants — quoted from `constants.py` (lines 147–175)

```python
BASE_BIRTH_CHANCE = 0.001
BASE_DEATH_CHANCE = 0.001
BASE_REPLICATION_CHANCE = 0.001 #If this is higher than DEATH_CHANCE,
                                #it can get cray
DEFAULT_MUTATION_CHANCE = 0.5

INITIAL_CREATURES = 10
DEFAULT_POP_CAP = 3000
...
DEFAULT_WORLD_DURATION = 100
```

`DEFAULT_MUTATION_CHANCE = 0.5` is not a realistic rate — it's a *watch-mutation-happen* visual
default. Keep it; comment it as such.

Per-allele defaults, from `population.py:19–74` — every allele of every gene starts identical:

```python
"birth_modifier"      : 0,
"replication_modifier": 1,
"mutation_chance"     : DEFAULT_MUTATION_CHANCE,
"death_modifier"      : 1,
```

Genes and their alleles (`collections.OrderedDict`, and **the order is load-bearing** — see §4.4):

| gene | alleles |
|---|---|
| `color` | `creature_color_1` … `creature_color_4` |
| `shape` | `shape1`, `shape2` |
| `size` | `"1"`, `"0.5"` — **strings, not floats** |

`creature.py` in full (17 lines):

```python
class Creature(object):
    def __init__(self, size = '1', color = 'creature_color_1', shape = 'shape1'):
        self.alleles = {"size": size, "color": color, "shape": shape}
        self.birthday = None
        self.deathday = None
        self.name = None
        self.parent = None
        self.children = []
```

---

## 2. The rules

### 2.1 The tick loop (`population.py:137–142`)

```python
for t in range(0, self.duration):
    self.apply_updates(t)
    self.death(t)
    self.replicate(t)
    self.spontaneous_birth(t)
```

**The order is the rule.** Death resolves before replication, so a creature that dies at `t` cannot
replicate at `t` — except that it can, see §4.2. Do not reorder.

### 2.2 Modifiers are multiplicative across genes (`population.py:219–224`)

```python
for gene in cre.alleles:
    replication_chance *= self.genes[gene][cre.alleles[gene]]['replication_modifier']
    death_chance       *= self.genes[gene][cre.alleles[gene]]['death_modifier']
```

Starting from `BASE_*` = 0.001 and multiplying one factor per gene. With all modifiers at their
default `1`, `r == d == 0.001`.

### 2.3 The crowding term — this is the whole video

Identical expression in both halves (`population.py:225` and `:295`):

```python
crowding_rep_mod   = (replication_chance - death_chance) / self.pop_cap / 2
crowding_death_mod = (replication_chance - death_chance) / self.pop_cap / 2

# replicate if:  random() < replication_chance - crowding_rep_mod   * pop_size
# die       if:  random() < death_chance       + crowding_death_mod * pop_size
```

Primer's own comment explains the `/ 2`:

> `#Death chance is here because I decided to share the crowding effect evenly between replication and death. We need the death chance to calculate the overall effect.`

That's why *both* formulas need *both* chances. A port that computes the death crowding from
`death_chance` alone looks reasonable and is wrong.

The superseded version is left in a comment at `:282` — `crowding_death_mod = 1 + (pop_size / self.pop_cap) ** 10`.
It is **not** the rule. Don't resurrect it.

### 2.4 Carrying capacity is exactly `pop_cap` — the derivation

Worth writing into `config.py`, in the style of the `tie_cost` block. Let `r`, `d` be the
gene-modified replication and death chances and `c = (r − d) / cap / 2`. The population is at
equilibrium when the per-creature replication and death probabilities are equal:

```
r − c·N  =  d + c·N
r − d    =  2·c·N
N        =  (r − d) / (2c)
           = (r − d) / (2 · (r − d)/(2·cap))
           = cap
```

**`N* = pop_cap`, independent of `r` and `d`** — provided `r > d`. That's the check in §8, and it's a
much sharper test than "the curve looks S-shaped".

⚠️ **The corollary is the trap.** With Primer's *module* defaults, all modifiers are `1`, so
`r == d == 0.001`, hence `c == 0` and **there is no density dependence at all**. The default
`Population()` is a pure neutral random walk that drifts to extinction — no S-curve, no carrying
capacity. This is the same species of trap as `tie_cost = 0`: the interesting behaviour requires
`r > d`, which the *scenes* supply via `gene_updates`, not the module constants. §3.1 handles it.

### 2.5 Shipped scene parameters (verified from `video_scenes/logistic_growth.py`)

These are real, and they let you validate the port against Primer's own graph axes.

`sim_summary()` (lines 205–240):
```python
sim_duration = 60
initial_creature_count = 10           # creature_color_1, shape1
gene_updates = [
    ['shape', 'shape1', 'birth_modifier', 1, 0],
    ['size',  '1',      'birth_modifier', 1, 0],
    ['shape', 'shape1', 'mutation_chance', 0, 0],
    ['size',  '1',      'mutation_chance', 0, 0],
    ['color', 'creature_color_1', 'death_modifier', 18, 0],
    ['color', 'creature_color_1', 'replication_modifier', 30, 0],
    ['color', 'creature_color_1', 'mutation_chance', 0, 0],
]
# graph y_range = [0, 30]
```
⇒ `r = 0.001 × 30 = 0.03`, `d = 0.001 × 18 = 0.018`, `r − d = 0.012`. Over 60 ticks from 10:
`10 · e^{0.012·60} = 10 · e^{0.72} ≈ 20.5`. Primer's y-axis tops out at 30. ✔

`last_video()` (lines 55–90), the exponential recap:
```python
sim_duration = 100
initial_creature_count = 5            # creature_color_4, shape1
gene_updates = [..., ['color', 'creature_color_4', 'death_modifier', 10, 0],
                     ['color', 'creature_color_4', 'replication_modifier', 40, 0], ...]
# graph y_range = [0, 60]
```
⇒ `r = 0.04`, `d = 0.01`, `r − d = 0.03`. Over 100 ticks from 5: `5 · e^{3} ≈ 100`. y-axis 60. ✔

**Both reconstructions land inside Primer's own axis ranges.** That's the strongest available
evidence the model above is right — use it as the acceptance test for step 3 in §6.

Note `pop_cap` is never overridden in these scenes, so it stays 3000; neither run gets near it, which
is why they read as exponential.

### 2.6 Spontaneous birth (`population.py:172–190`)

```python
candidates = self.list_possible_genotypes()      # 4 x 2 x 2 = 16 creatures, one per genotype
for candidate in candidates:
    birth_chance = BASE_BIRTH_CHANCE
    for gene in candidate.alleles:
        birth_chance *= self.genes[gene][candidate.alleles[gene]]['birth_modifier']
    while birth_chance > 1:                      # whole part = guaranteed births
        sibling = deepcopy(candidate)
        self.birth(sibling, t + 1)
        birth_chance -= 1
    birth_roll = random()
    if birth_roll < birth_chance:
        self.birth(candidate, t + 1)
```

Life appears **from nothing**, once per genotype per tick. With `birth_modifier` defaulting to `0`,
the product is 0 and spontaneous birth is **off** — the scenes switch it on per-allele (see the
`birth_modifier, 1` updates in §2.5).

The `while birth_chance > 1` loop reads as a guard but is a feature, and the shipped scenes lean on it
hard. Verified `birth_modifier` values across the four importers: `logistic_growth.py` never exceeds
`1` (so spontaneous birth stays effectively off there), but `replication_only.py` goes up to **5000**,
`mutations.py` to **1000**, and `fecal_transplant.py` to **900**. At `birth_modifier = 1000`,
`birth_chance = 0.001 × 1000 = 1.0` — one guaranteed birth per genotype per tick. At 5000, five.
So the loop is the main path in those scenes, not an edge case. Test it (§7.11).

Equilibrium, from Primer's own comment at `constants.py:144`:
> `#BIRTH_CHANCE / (DEATH_CHANCE - REPLICATION_CHANCE)`

i.e. with spontaneous birth on and `d > r`, the population settles at `b / (d − r)`. A second free
analytic check.

### 2.7 Mutation on replication (`population.py:233–254`)

One roll per gene. Two accepted forms:

```python
chances = self.genes[gene][cre.alleles[gene]]['mutation_chance']
if isinstance(chances, (float, int)):
    if mutation_roll < chances:
        other_options = deepcopy(self.genes[gene])
        other_options.pop(cre.alleles[gene])          # cannot mutate to itself
        baby.alleles[gene] = choice(list(other_options.keys()))
    else:
        baby.alleles[gene] = cre.alleles[gene]
elif isinstance(chances, list):
    cumulative_chance = 0
    for chance, allele in zip(chances, self.genes[gene]):
        cumulative_chance += chance
        if mutation_roll < cumulative_chance:
            baby.alleles[gene] = allele
            break
        baby.alleles[gene] = cre.alleles[gene]
else:
    raise Warning('Mutation chance must be number or list')
```

- **Scalar form:** mutate with probability `chances`, uniformly among the *other* alleles. Never to
  itself. The `.pop()` is what guarantees that.
- **List form:** per-allele cumulative probabilities, zipped against the gene's allele order. This is
  the only reason `genes` is an `OrderedDict`.

### 2.8 `gene_updates` (`population.py:105–107`, `:167–170`)

```python
#Each update arg should be of the form
#update = [gene, allele, property, value, frame]
# e.g., ['shape', 'shape1', 'replication_modifier', 2, 20]

def apply_updates(self, t):
    for update in self.updates:
        if update[4] == t:
            self.genes[update[0]][update[1]][update[2]] = update[3]
```

Exact `==` on the tick, not `>=`. An update scheduled for a tick outside `range(duration)` never
fires. Port that literally.

---

## 3. Files to create

```
population_sim/
  config.py       # constants + the gene table + scene presets
  creature.py     # Creature: alleles dict, birthday/deathday, parent/children
  simulation.py   # class Simulation -- the Population port
  main.py         # CLI + two windows
```

Module names `config` / `creature` / `simulation` are **already in `_SHARED_NAMES`**. If you name a
module `population.py` instead, you **must** add it to `_SHARED_NAMES` in `tests/test_rules.py` or the
module cache will leak between sims.

### 3.1 `config.py` — resolving the "defaults must be Primer's" tension

Primer's *module* constants and his *scene* parameters disagree, and §2.4 shows the module defaults
produce nothing to look at. Resolve it explicitly:

- Dataclass fields default to **Primer's module constants** (`constants.py`). That satisfies
  `.claude/rules/global/primer-fidelity.md`.
- The **default scene preset** reproduces his shipped `sim_summary()` numbers, so
  `python3 main.py` shows the real thing.
- Everything stays a flag.

```python
"""Tunable parameters for the population / logistic growth sim.

Defaults are Primer's, from population.py and constants.py in Helpsypoo/primerpython
(the "Simulating Competition and Logistic Growth" video, 2018).
"""

from dataclasses import dataclass, field

GENES = {                       # allele order is load-bearing: the list form of
    "color": ("creature_color_1", "creature_color_2",   # mutation_chance zips against it
              "creature_color_3", "creature_color_4"),
    "shape": ("shape1", "shape2"),
    "size":  ("1", "0.5"),      # strings, matching Primer's allele keys
}

# Primer's shipped scenes, as gene_updates: [gene, allele, property, value, tick].
SCENES = {
    # video_scenes/logistic_growth.py :: sim_summary  -- r=0.03, d=0.018
    "summary": (
        ["shape", "shape1", "birth_modifier", 1, 0],
        ["size", "1", "birth_modifier", 1, 0],
        ["shape", "shape1", "mutation_chance", 0, 0],
        ["size", "1", "mutation_chance", 0, 0],
        ["color", "creature_color_1", "death_modifier", 18, 0],
        ["color", "creature_color_1", "replication_modifier", 30, 0],
        ["color", "creature_color_1", "mutation_chance", 0, 0],
    ),
    # video_scenes/logistic_growth.py :: last_video   -- r=0.04, d=0.01
    "exponential": (...),
    "bare": (),   # Primer's raw module defaults: r == d, no crowding, neutral drift
}


@dataclass
class Config:
    # -- Primer's constants ------------------------------------------------
    base_birth_chance: float = 0.001        # BASE_BIRTH_CHANCE
    base_death_chance: float = 0.001        # BASE_DEATH_CHANCE
    base_replication_chance: float = 0.001  # BASE_REPLICATION_CHANCE
    mutation_chance: float = 0.5            # DEFAULT_MUTATION_CHANCE -- a "watch it
                                            # happen" visual rate, not a realistic one
    pop_cap: int = 3000                     # DEFAULT_POP_CAP
    duration: int = 100                     # DEFAULT_WORLD_DURATION
    initial_creatures: int = 10             # INITIAL_CREATURES

    start_color: str = "creature_color_1"
    start_shape: str = "shape1"
    start_size: str = "1"

    # Crowding is shared evenly between replication and death:
    #   c = (r - d) / pop_cap / 2
    #   replicate if roll < r - c*N ;  die if roll < d + c*N
    # Setting r - c*N = d + c*N gives N* = pop_cap exactly, for ANY r > d. So the
    # carrying capacity is the cap itself, not a function of the rates.
    #
    # But with the module defaults every modifier is 1, so r == d == 0.001, c == 0,
    # and there is NO density dependence -- just a neutral walk to extinction. The
    # S-curve needs r > d, which the scenes supply via gene_updates. Same trap as
    # tie_cost = 0: the default is degenerate on purpose.
    scene: str = "summary"
    gene_updates: tuple = ()   # overrides `scene` when non-empty

    seed: int | None = None
    render: bool = True

    def genes(self):
        """Fresh per-run gene table. Primer deepcopies the class attribute so one
        Population can be re-simulated; we rebuild instead."""
        ...

    def updates(self):
        return self.gene_updates or SCENES[self.scene]
```

### 3.2 `creature.py`

Port `Creature` as-is, plus `_next_id` / `reset_ids()` and a `name` / `color` property per repo
convention. `color` maps the `color` allele onto the palette (§5).

Add `__slots__` — creatures are numerous (up to `pop_cap` = 3000) and this is a hot loop
(`.claude/rules/languages/python.md`). But **only if you drop the lineage log** (§4.1).

### 3.3 `simulation.py`

`class Simulation` with `self.rng = random.Random(config.seed)`, `self.log = EventLog()`,
`Creature.reset_ids()`. Methods mirroring Primer's: `apply_updates(t)`, `death(t)`, `replicate(t)`,
`spontaneous_birth(t)`, `list_possible_genotypes()`, `simulate_tick()`, `run_headless()`.

**Name the day loop `simulate_tick()`, not `simulate_day()`.** There is no day here — no dawn, no
foraging, no going home. Calling it a day would be a lie the arena then has to act out.

---

## 4. The data-model decision — read before writing code

This is the one place where a faithful port and a correct port pull apart. Decide deliberately,
write the decision into a comment, and pin it with a test.

### 4.1 Primer never removes creatures

`death()` sets `cre.deathday = t + 1` and nothing is ever deleted. `self.creatures` is a **full
lineage log**, and population size is derived by walking the entire history (`:305–316`):

```python
def count_creatures_at_t(self, t, creatures = None):
    count = 0
    for creature in creatures:
        if creature.birthday <= t:
            count += 1
        if creature.deathday != None and creature.deathday <= t:
            count -= 1
    return count
```

And that is called **once per creature inside `replicate()`** (`:226`), inside a per-tick loop —
O(N³)-ish. At `pop_cap = 3000` over 100 ticks this is unusable.

**Recommendation:** keep a live roster (`self.creatures` = alive only) plus a separate append-only
`self.history` for the graphs, and maintain `pop_size` incrementally. This repo's `EventLog` +
live-list architecture already assumes that shape.

**But the counting semantics must match exactly**, or the logistic curve shifts by a tick:
- a creature counts as alive at `t` when `birthday <= t`;
- it stops counting at `t` when `deathday <= t`;
- `birth()` and `replicate()` stamp `birthday = t + 1`, **not** `t`;
- `death()` stamps `deathday = t + 1`, **not** `t`.

So a creature born during tick `t` is *not* counted at `t`. Test it (§7.1).

### 4.2 The `alive` predicates genuinely differ

```python
# replicate(), :210
alive = [cre for cre in self.creatures if cre.deathday == None or cre.deathday > t]
# death(), :274
alive = [cre for cre in self.creatures if cre.deathday == None and cre.birthday <= t]
```

Not the same set. `replicate()` omits the `birthday <= t` filter, so **a creature born at `t + 1` is
eligible to replicate at `t`** — the tick it was conceived. `death()` also admits creatures whose
`deathday` was set this very tick under `or ... > t`… but it uses `and ... == None`, so it doesn't.

This is not a typo to normalise. It measurably shifts the growth rate. Reproduce it and test it
(§7.2). If you decide to *fix* it, that is a deliberate divergence and it belongs in the README, not
in a silent commit.

### 4.3 `pop_size` is sampled inconsistently

`death()` computes `pop_size` **once**, before its loop (`:277`). `replicate()` recomputes it
**per creature**, inside the loop (`:226`). So within a single tick, later replicators see a
population that already includes earlier replicators' babies; deaths all see the same snapshot.

Faithful port: keep the asymmetry. It's a real (small) bias toward density-dependence in replication.

### 4.4 Bugs in the source — decide explicitly

Per `.claude/rules/global/primer-fidelity.md`, Primer's source is the authority. These are places
where the source is *self-evidently* broken rather than surprising, which is a different case. My
recommendation for each:

1. **Loop-variable shadowing (`:263`).** Inside `replicate()`'s `for cre in alive:` loop, the naming
   block does `for cre in self.creatures:` — clobbering the outer `cre` mid-iteration. After the
   first baby, `cre.children.append(...)` appends to the *wrong* creature, and the next iteration's
   parent is corrupted. **Do not reproduce.** It affects only `name`/`children` bookkeeping, which we
   are replacing anyway (`_next_id`). Note it in the port comment.
2. **`for creature in alive:` (`:284`, `:200`, `:309`, `:326`)** shadows the imported `creature`
   *module*. Harmless there, but don't copy the shadowing. Our module is imported the same way.
3. **`main()` (`:350`)** references `self.duration` at module scope — it cannot run. Ignore.
4. **`import imp` (`:3`)** was removed in Python 3.12. The source doesn't run on our stack at all,
   so there is no "run Primer's script and compare outputs" option. Validation is analytic (§2.4,
   §2.5, §2.6) — state that plainly in the plan's acceptance criteria.

Anything you choose *not* to reproduce goes in a `# Deviation:` comment naming the line, so the next
fidelity audit doesn't flag it as a porting error.

---

## 5. `primer_common` additions

**`palette.py`** — Primer's four creature colours already exist under different role names. Add:

```python
# population_sim maps Primer's color_1..color_4 alleles onto his palette.
ALLELE_COLORS = (BLUE, ORANGE, YELLOW, RED)   # creature_color_1 .. _4
```

Verified: `constants.py` `color_scheme = 2` lists `[62,126,160]`, `[255,148,0]`, `[231,226,71]`,
`[214,59,80]` in that order — which is exactly `palette.BLUE/ORANGE/YELLOW/RED`. No new hex.

**`events.py`** — **no new event types needed.** Reuse:
- `Born(who, parent)` for replication; `Born(who, parent="spontaneous")` for abiogenesis.
- `Died(who, cause="died")`.
- `DaySummary(day=t, population=N, births, deaths, stats={...})` — the feed already prints
  `-- day N pop X (+b/-d)`, which is exactly right here.

Optionally add `Mutated(who, gene, frm, to)` — *Mutations* is one of the four videos this core
serves, and a mutation is otherwise invisible in the feed. Cheap and worth it.

---

## 6. Build order

1. **Config + gene table.** `Config`, `GENES`, `SCENES`, `genes()`, `updates()`. No sim yet.
2. **Creature + Simulation skeleton.** `simulate_tick()` with `apply_updates` → `death` →
   `replicate` → `spontaneous_birth`. Live roster (§4.1).
3. **Validate against Primer's axes.** This is the acceptance gate for the rules:
   - `--scene summary --duration 60 --initial-creatures 10 --seed N` ⇒ final ≈ **20**, and Primer's
     graph tops at 30.
   - `--scene exponential --duration 100 --initial-creatures 5` ⇒ final ≈ **100**, his graph tops at 60.
   Average ≥5 seeds; these are stochastic. If you're outside ~±40%, the crowding or the multiply is wrong.
4. **Carrying capacity.** Long run at `--scene exponential --duration 3000` ⇒ population parks at
   **3000** (`= pop_cap`). This is the §2.4 derivation, and it's the sharpest test in the plan.
5. **Mutation.** Scalar form, then the list form. Test the never-mutates-to-itself property.
6. **Spontaneous birth.** Turn `birth_modifier` on via a scene; check the `b / (d − r)` equilibrium.
7. **Rendering.** `main.py`, graphs, arena. Then run the `verify` skill and **look at a frame**.
8. **Gate.** `/sim-check` (§8) + docs (§9).

---

## 7. Tests to add — `tests/test_rules.py`

Banner + `def _pop(): return _load("population_sim", ("config", "creature", "simulation"))`.

1. `test_birthday_and_deathday_are_stamped_at_t_plus_one` — a creature born during tick `t` is not
   counted at `t`. Catches the off-by-one that shifts the whole curve.
2. `test_replicate_and_death_use_different_alive_predicates` — pin §4.2 explicitly, with a comment
   naming `population.py:210` and `:274`. This test exists to stop someone "unifying" them.
3. `test_crowding_is_shared_evenly_between_replication_and_death` — assert the *same* expression
   appears on both sides: with `r=0.04, d=0.01, cap=3000`, `c == (0.04-0.01)/3000/2 == 5e-6`, and the
   effective rates at `N=3000` are both `0.025`. A death-crowding computed from `d` alone fails.
4. `test_carrying_capacity_equals_pop_cap` — the §2.4 algebra as a unit test over several `(r, d)`
   pairs: solve `r − cN = d + cN` ⇒ `N == pop_cap`. Pure arithmetic, no simulation, instant.
5. `test_equal_rates_produce_zero_crowding` — `r == d` ⇒ `c == 0`. Pins the degenerate default so
   nobody "fixes" it by rescaling.
6. `test_modifiers_multiply_across_genes` — three genes at 2/3/5 ⇒ `0.001 * 30`.
7. `test_mutation_never_produces_the_same_allele` — `mutation_chance=1.0`, 200 children, assert the
   allele always changed. The `.pop()` at `:239` is what guarantees it; a naive `choice(all_alleles)`
   passes a weaker test.
8. `test_mutation_list_form_follows_allele_order` — a cumulative list `[0, 1, 0, 0]` must always
   produce `creature_color_2`. Pins the `OrderedDict` dependency.
9. `test_gene_update_fires_on_exact_tick` — an update at tick 20 has no effect at 19, applies at 20,
   and one scheduled past `duration` never fires (`==`, not `>=`).
10. `test_spontaneous_birth_is_off_by_default` — `birth_modifier = 0` ⇒ zero spontaneous births over
    a long run. Then with `birth_modifier = 1` on all three genes, births occur.
11. `test_spontaneous_birth_whole_part_is_guaranteed` — `birth_chance = 2.3` ⇒ ≥2 births every tick.
12. `test_all_sixteen_genotypes_are_birth_candidates` — `len(list_possible_genotypes()) == 4*2*2`.

---

## 8. The gate — `/sim-check`

Add a stage to `.claude/commands/bash/sim-check.sh` and renumber. The carrying-capacity check is the
one that matters — it's analytic, seed-robust, and catches every plausible crowding error:

```bash
echo ""
echo "N/N  population: carrying capacity settles at pop_cap"
o=$(cd population_sim && python3 main.py --no-render --scene exponential \
      --duration 3000 --pop-cap 500 --seed 1 2>/dev/null)
n=$(num "$o" 'pop [0-9.]+')
# N* = pop_cap exactly, for any r > d. Band is +/-20% for demographic noise.
if [ -z "$n" ]; then bad "no output"
elif awk "BEGIN{exit !($n > 400 && $n < 600)}"; then ok "settled at ${n} (cap 500)"
else bad "settled at ${n} -- expected ~500; crowding term is wrong"; fi
```

Use `--pop-cap 500` rather than 3000 to keep the runtime sane. The prediction `N* = cap` holds for
any cap, which is exactly why it's a good test.

---

## 9. Docs to update

- **`README.md`** — source-table row, a "### Population / logistic growth" section covering the
  `N* = pop_cap` derivation and the `r == d` degenerate default (mirroring how the `tie_cost` table is
  presented), and the allele colours.
- **`CLAUDE.md`** — `population_sim/` in *Where things live*.
- **`.claude/rules/global/primer-fidelity.md`** — `population.py`, `tools/creature.py` and
  `constants.py` are **already listed** in the authority-chain file map. Still to add once the port
  exists: a **Constants that are load-bearing** subsection — the shared crowding `/2`, `N* = cap`,
  `birth_modifier = 0` meaning abiogenesis is off, and `DEFAULT_MUTATION_CHANCE = 0.5` being a visual
  rate.
- **`.claude/hooks/pre-generation/primer-fidelity-guard.sh`** — a `note` for
  `crowding|pop_cap|birth_modifier|replication_modifier`, warning that crowding is deliberately split
  between birth and death and that `r == d` producing nothing is intentional.
- **Test count:** nothing to do — the hardcoded `36` is already gone from all seven files. Don't
  reintroduce a number.
