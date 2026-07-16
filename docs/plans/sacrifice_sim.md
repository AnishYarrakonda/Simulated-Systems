# Plan: `sacrifice_sim` — the evolution of sacrificing for family

Port of Primer's altruism layer: unconditional altruism, green beards, and kin selection.

| | |
|---|---|
| **Video** | [Simulating the Evolution of Sacrificing for Family](https://www.youtube.com/watch?v=iLX_r_WPrIw) (2021-08-28) |
| **Primer's source** | `Helpsypoo/primerpython` → `blender_scripts/tools/natural_sim.py` (1941 lines) |
| **Video scene** | `blender_scripts/video_scenes/inclusive_fitness.py` → `self.hamilton()`, `graph_type = 'kin_altruist'` |
| **Archetype** | **Spatial** — same shape as `natural_selection_sim` (`creature.py` + `environment.py`) |
| **Est. size** | Medium. The core already exists; this is a trait layer + one new creature state. |

---

## 0. Read this first — the authority correction

**The altruism sim is `natural_sim.py`, not `hamilton_basic.py`.**

`blender_scripts/tools/hamilton_basic.py` exists, is 109 lines, models Hamilton's rule with sibling
lookup and mating chances, and **is imported by no video scene.** It is a standalone side-experiment.
Two independent research passes recommended it as the source for this video. Both were wrong — it was
verified that `video_scenes/inclusive_fitness.py` imports `natural_sim`, and its `hamilton()` scene
plots `graph_type = 'kin_altruist'`, a trait that lives in `natural_sim.py`.

Consequences, and they are the whole shape of this plan:

- The shipped sim is **spatial**. Blobs forage in the 300×300 world, and altruism is a **detour** to
  hand a food to someone who has none. It is not an abstract mating-chance transfer.
- `sacrifice_sim` is therefore `natural_selection_sim` **plus a trait layer**, not a new archetype.
- If you want the analytic `r·B > C` toy, `hamilton_basic.py` is a fine *reference* — but it is not
  authority, and its defaults must not be presented as Primer's shipped values.

Record this in `.claude/rules/global/primer-fidelity.md` (see §8) so the next pass doesn't re-derive it.

---

## 1. What it models

A creature that has already eaten 2 food (so: survives *and* reproduces for certain) can spend part
of that certainty to save someone else's life. Giving away one food drops it to 1 — still alive, but
its reproduction is no longer guaranteed. The recipient goes from 0 food (dead) to 1 (alive).

That is Hamilton's rule with real numbers: a cost of ~0.5 expected offspring against a benefit of one
relative's entire survival. The video's arc is that **indiscriminate** altruism gets exploited,
**green-beard** altruism works but is brittle, and **kin** altruism is the stable answer.

---

## 2. Verified rules — quoted from `natural_sim.py`

### 2.1 Constants (lines 20–39)

```python
HELP_REP_BOOST = 0.5   #Reproduction chance improvement creatures get by helping
FAMILY_JUMPS = 3
KIN_ALTRUISM_RADIUS = 0
MUTATION_CHANCE = 0.05
MUTATION_VARIATION = 0.1
STARTING_ENERGY = 800   #1800
HOMEBOUND_RATIO = 2     # 1.5
SAMARITAN_RATIO = 1.1
```

`KIN_ALTRUISM_RADIUS = 0` is **dead** — the code path that used it is commented out (line 583) and
replaced by the family-tree walk. Keep it out of `config.py`; the live knob is per-creature
`kin_radius`.

### 2.2 The `samaritan` state (lines 552–555)

```python
if state == 'homebound' and \
        len(day.has_eaten[-1]) > 1 and \
        distance_left > distance_out * HOMEBOUND_RATIO * SAMARITAN_RATIO:
    state = 'samaritan'
```

Three conditions, all required: already homebound, **already holding 2 food**, and enough energy
margin to afford the detour (`2 × 1.1 = 2.2 ×` the distance out). Altruism is only ever paid for out
of surplus.

### 2.3 Who counts as "to be nice to" (lines 572–606)

Five mutually exclusive branches, in this `if/elif` order — **the order is the rule**:

```python
if self.altruist == True:          to_be_nice_to = close_creatures
elif self.green_beard == True:     to_be_nice_to = [x for x in close_creatures if x.green_beard == True]
elif self.a_gb == True:            to_be_nice_to = [x for x in close_creatures if x.gbo == True]
elif self.kin_altruist == True:    # family-tree walk, below
else:                              to_be_nice_to = [x for x in close_creatures if \
                                       ((x.size - self.size) ** 2 + (x.speed - self.speed) ** 2 + \
                                       (x.sense - self.sense) ** 2) ** (1/2) < self.kin_radius]
```

`close_creatures` = live creatures within `EAT_DISTANCE + BASE_SENSE_DISTANCE * self.sense` — the
same sense radius used for food.

The **`else`** branch is not a no-op: a creature with none of the four flags still helps anyone within
`kin_radius` in **trait space** (Euclidean over size/speed/sense). That's phenotype matching, and with
the default `kin_radius = 0` it helps nobody. This branch is why `kin_radius` must default to 0.

`a_gb` / `gbo` are the "falsebeard" pair — `a_gb` creatures help anyone *displaying* `gbo`, which lets
the video show beard-mimics exploiting beard-altruists. Port them; they're cheap and they're the
video's exploitation segment.

The kin branch (lines 585–598):

```python
fam = [self]
fam_to_check = [self]
for i in range(FAMILY_JUMPS):
    new_fam = []
    for cre in fam_to_check:
        if cre.parent != None and cre.parent not in fam:
            new_fam.append(cre.parent)
        for chi in cre.children:
            if chi not in fam:
                new_fam.append(chi)
    fam = fam + new_fam
    fam_to_check = new_fam
to_be_nice_to = [x for x in close_creatures if x in fam]
```

A breadth-first walk out to 3 jumps over `parent` / `children` edges. **`fam` includes `self`.** Note
`new_fam` can contain duplicates within one jump (the `not in fam` check tests the *previous* `fam`,
not `new_fam`), which is harmless for membership but means `fam` is not deduplicated. Reproduce it —
`x in fam` is unaffected.

### 2.4 The help action (lines 610–640)

```python
if state == 'samaritan':
    # nearest cre in to_be_nice_to with len(cre.days[-1].has_eaten[-1]) == 0
    if to_be_helped != None:
        if dist < EAT_DISTANCE:
            to_be_helped.days[-1].has_eaten[-1].append(self.days[-1].has_eaten[-1].pop())
            self.days[-1].has_helped += 1
            if distance_left < distance_out * HOMEBOUND_RATIO:
                state = 'homebound'
            else:
                state = 'foraging'
        else:
            new_heading = math.atan2(vec_to_help[1], vec_to_help[0])   # walk toward them
    else:
        state = 'homebound'   # nobody to help
```

Load-bearing details:
- Only creatures with **exactly 0 food** are candidates. You cannot top someone up from 1 to 2.
- The food **transfers out of the helper's stomach** — `pop()` then `append()`. It is not created.
- After helping, the helper re-evaluates: back to `foraging` if it still has margin, else `homebound`.
  So a rich creature can help **more than once** in a day, and `has_helped` counts each.
- Help only lands within `EAT_DISTANCE`; otherwise the creature *walks toward* the target, burning
  energy. A failed samaritan run is a real loss.

### 2.5 Reproduction (lines 1250–1259) — this is Hamilton's rule

```python
for par in parents:
    if len(par.days[-1].has_eaten[-1]) > 1:
        reproduction_chance = 1
    elif len(par.days[-1].has_eaten[-1]) > 0:
        reproduction_chance = par.days[-1].has_helped * HELP_REP_BOOST
    else:
        reproduction_chance = 0
    if random() < reproduction_chance:
        ...
```

Read that carefully — it changes the existing NS rule:

| food at end | helped | reproduction chance |
|---|---|---|
| 2+ | — | `1` (certain) |
| 1 | 0 | `0` |
| 1 | 1 | `0.5` |
| 1 | 2 | `1.0` |
| 0 | — | `0` (and dead anyway) |

So giving away one food costs exactly `1 − 0.5 = 0.5` expected offspring, and helping twice is fully
compensated. `has_helped * 0.5` is **not clamped** — help 3 times and `reproduction_chance = 1.5`,
which `random() < 1.5` treats as certainty. Leave it unclamped.

⚠️ In the current `natural_selection_sim`, a creature with 1 food simply survives and doesn't
reproduce. This table **supersedes** that inside `sacrifice_sim` only. Do not retrofit it into
`natural_selection_sim` — its video has no helping.

### 2.6 Mutation and inheritance (lines 1272–1310) — the trap

```python
child_altruist = False
if self.mutation_switches['altruist'] == True:
    if random() < self.mutation_chance:
        child_altruist = not par.altruist
    else:
        child_altruist = par.altruist
```

**A boolean trait is only inherited when its mutation switch is on.** With
`mutation_switches['altruist'] = False`, every child is born `altruist = False` — the parent's value
is *discarded*, not preserved. Same for `green_beard`, `gbo`, `a_gb`, `kin_altruist`.

`kin_radius` does **not** behave that way:

```python
kin_addition = 0
if self.mutation_switches['kin_radius'] == True:
    if random() < self.mutation_chance * 1.73:
        # Increase chance by a factor of root 3. Makes it so expected trait distance
        # change is equal to expected kin radius change.
        kin_addition = randrange(-1, 2, 2) * MUTATION_VARIATION
        if par.kin_radius + kin_addition < 0:
            kin_addition = 0
baby = Creature(..., kin_radius = par.kin_radius + kin_addition)
```

`kin_radius` is inherited **unconditionally** (`par.kin_radius + 0` when the switch is off), while the
booleans are not. That asymmetry is a genuine inconsistency in Primer's source and it is exactly the
sort of thing a "cleanup" would silently normalise. **Reproduce both behaviours.** §7 pins them.

The `1.73` is `√3`, and Primer says why: trait space is 3-dimensional (size, speed, sense), so a
±0.1 step on one of three axes moves the trait-space distance by an expected amount that a ±0.1 step
on the single `kin_radius` axis only matches if you roll `√3` times as often. Name it in the config
comment. Note also the negative clamp sets `kin_addition = 0` (freeze) rather than clamping the
result — a creature at `kin_radius = 0` rolling −0.1 simply stays at 0, it does not resample.

---

## 3. Files to create

`sacrifice_sim/` is standalone and self-contained, exactly like the other three. It copies the NS core
and adds the trait layer. **Yes, this duplicates `creature.py`/`environment.py` — that is the repo's
deliberate architecture** (`.claude/rules/global/architecture.md`: each sim mirrors Primer's per-video
layout and imports by bare name). Do not factor out a shared base.

```
sacrifice_sim/
  config.py        # NS config + the altruism block
  creature.py      # NS creature + traits, samaritan state, family walk
  environment.py   # NS environment + the help step and new reproduction rule
  main.py          # CLI + two windows
```

Module names are `config` / `creature` / `environment` — **all already in `_SHARED_NAMES`** in
`tests/test_rules.py`, so no test-loader change is needed.

### 3.1 `config.py`

Start from `natural_selection_sim/config.py` verbatim, then add:

```python
    # -- altruism (natural_sim.py) -----------------------------------------
    help_rep_boost: float = 0.5      # HELP_REP_BOOST, per help, unclamped
    family_jumps: int = 3            # FAMILY_JUMPS, BFS depth over parent/children
    samaritan_ratio: float = 1.1     # SAMARITAN_RATIO, on top of HOMEBOUND_RATIO

    # Starting trait values. Primer seeds these per-scene, not as module constants.
    start_altruist: bool = False
    start_green_beard: bool = False
    start_gbo: bool = False
    start_a_gb: bool = False
    start_kin_altruist: bool = False
    start_kin_radius: float = 0.0    # 0 => the phenotype-matching branch helps nobody

    # A trait is only INHERITED when its switch is on -- see natural_sim.py:1272.
    # Off means every child is born False, discarding the parent's value.
    # kin_radius is the exception: it inherits regardless. Not a typo.
    mutate_altruist: bool = False
    mutate_green_beard: bool = False
    mutate_gbo: bool = False
    mutate_a_gb: bool = False
    mutate_kin_altruist: bool = False
    mutate_kin_radius: bool = False

    kin_radius_mutation_factor: float = 1.73   # sqrt(3): trait space is 3-D, so a
                                               # kin_radius step must be rolled root-3
                                               # as often to match expected trait drift
```

Keep the NS defaults (`world_extent=150`, `starting_energy=800`, `food_count=100`, …) untouched.

### 3.2 `creature.py`

Add to `__init__`: `altruist`, `green_beard`, `gbo`, `a_gb`, `kin_altruist`, `kin_radius`,
`has_helped` (reset per day), `parent`, `children` (list).

⚠️ **`parent` / `children` create a strong reference cycle and a permanent lineage graph.** NS today
holds no such edges. At 100+ creatures over 100 days this retains every creature ever born. Two
options — pick one *deliberately* and comment it:
- Keep full edges (faithful, matches Primer, memory grows). Fine at the video's scale.
- Cap the retained depth at `family_jumps` (equivalent for behaviour, since the walk never looks
  further). **Recommended**, but only if a test pins that the reachable set is identical.

New methods:

```python
def is_kin_of(self, other, jumps)   # BFS, includes self, matches natural_sim.py:585
def to_be_nice_to(self, close_creatures)   # the five-branch if/elif, in order
def color(self)   # override: altruists tint toward GREEN, beards toward YELLOW
```

`choose_state()` gains the samaritan branch — but note the trigger lives *after* the homebound
decision, so implement it as a post-step on the existing state machine, not a new first-class branch.

### 3.3 `environment.py`

Two changes only:

1. **`step()`** — after `choose_state()`, if `state == 'samaritan'`, run the help logic: find the
   nearest 0-food creature in `to_be_nice_to`, walk toward it, and transfer on contact. Emit `Helped`.
2. **`finish_day()`** — replace the `n >= 2` reproduction test with the §2.5 table.

Everything else (movement, food, predation, day length) is unchanged from NS.

### 3.4 `main.py`

Copy `natural_selection_sim/main.py`. Flags: every field above as `--altruist`, `--green-beard`,
`--kin-altruist`, `--kin-radius`, `--mutate-altruist`, … plus the inherited NS flags, `--seed` and
`--no-render` last.

Graphs (`build_graphs`): population `LineGraph`, an **altruist-fraction `LineGraph`** (this is the
video's chart — `graph_type = 'kin_altruist'` in the scene), and the NS `Scatter3D` trait cloud.
Reuse `Histogram` for `kin_radius` when `--mutate-kin-radius` is on.

---

## 4. `primer_common` additions

**`palette.py`** — add role aliases, no hex anywhere else:

```python
ALTRUIST = GREEN
BEARD = YELLOW
SELFISH = BLUE      # = CREATURE, so a non-altruist looks like a plain NS blob
```

**`events.py`** — one new type. All fields need defaults (it's a `@dataclass` subclass of `Event`):

```python
@dataclass
class Helped(Event):
    helper: str = ""
    recipient: str = ""
    kind: str = "altruist"     # altruist | green_beard | a_gb | kin | phenotype
    helper_food_left: int = 0

    def line(self):
        return f"{self.helper} gave a food to {self.recipient} ({self.kind})"
```

Emit it from `environment.py`. **Never `print()` from a sim core** (`.claude/rules/layers/sim-cores.md`).

---

## 5. Build order

Work in this order; each step is independently verifiable.

1. **Scaffold.** Copy `natural_selection_sim/` → `sacrifice_sim/`. Run
   `cd sacrifice_sim && python3 main.py --no-render --days 10 --seed 1`. It must behave *identically*
   to NS. Baseline established.
2. **Traits, inert.** Add the six trait fields + `has_helped` to `Creature`, thread through
   `make_offspring` with the §2.6 switch semantics. No behaviour yet. Add the §7 inheritance tests —
   they should pass now.
3. **`to_be_nice_to`.** Implement the five-branch selector and the family walk. Still no behaviour
   change (nothing calls it). Add the family-walk and branch-order tests.
4. **Samaritan state + help.** Wire the trigger and the transfer. Emit `Helped`. Now
   `--altruist --mutate-altruist` should produce `Helped` lines in `--no-render` runs.
5. **Reproduction table.** Swap in §2.5. **This is the step that changes the dynamic** — re-run the
   NS baseline from step 1 and expect it to now differ (a 1-food helper can reproduce).
6. **Rendering.** `main.py` graphs + colours. Then run the `verify` skill and *look at a frame*.
7. **Gate.** `/sim-check` (§9) + docs (§8).

---

## 6. The emergent dynamic — what "correct" means

The unit tests will pass on a wrong port. These are the checks that catch it:

| run | expected |
|---|---|
| `--altruist --mutate-altruist` (indiscriminate) | altruists **rise then get exploited**; fraction does not fix at 1.0 |
| `--green-beard --mutate-green-beard` | beards **sweep** — helping only beards is self-reinforcing |
| `--green-beard --mutate-green-beard --gbo --a-gb --mutate-gbo --mutate-a-gb` | falsebeards invade and **crash** the beards |
| `--kin-altruist --mutate-kin-altruist` | kin altruists **stabilise at a positive fraction** — the video's punchline |
| all switches off (default) | identical to `natural_selection_sim`. **This is the regression check.** |

Run ≥3 seeds and report the spread — a single seed is an anecdote (`dynamics-analyst` agent).
Use it for the sweeps rather than doing them by hand.

⚠️ **Do not assert the textbook `r·B > C` threshold.** Two things break it here: `to_be_nice_to`
includes `self` via the family walk, and the benefit is a whole survival rather than a marginal
fitness increment. **Measure** the threshold with a `--help-rep-boost` sweep; don't predict it.

---

## 7. Tests to add — `tests/test_rules.py`

Add a `# ---- sacrifice` banner and `def _sac(): return _load("sacrifice_sim", ("config", "creature", "environment"))`.
No `_SHARED_NAMES` change needed.

Each test must fail on a *plausible* wrong port:

1. `test_help_rep_boost_table` — parametrise `(food, helped) -> chance`:
   `(2,0)->1`, `(1,0)->0`, `(1,1)->0.5`, `(1,2)->1.0`, `(0,0)->0`. Catches anyone who "helpfully"
   clamps or reuses the NS `n >= 2` rule.
2. `test_reproduction_chance_is_not_clamped` — `(1, 3) -> 1.5`. A `min(1, …)` passes every other test.
3. `test_boolean_traits_are_not_inherited_when_switch_is_off` — parent `altruist=True`,
   `mutate_altruist=False` ⇒ **child is `False`**, not `True`. This is the single most likely
   "bug fix" someone will apply. Name `natural_sim.py:1272` in the assertion comment.
4. `test_kin_radius_is_inherited_even_when_switch_is_off` — the asymmetric twin of #3.
5. `test_kin_radius_mutation_rolls_at_root_three` — with `mutation_chance=0.5`,
   `kin_radius_mutation_factor=1.73`, measure the mutation rate over ~4000 trials ≈ 0.865.
   Statistical, seeded, like `test_survival_and_reproduction_rolls_are_independent`.
6. `test_kin_radius_never_goes_negative` — parent at 0.0, always-mutate ⇒ child ∈ {0.0, 0.1}.
7. `test_family_walk_reaches_exactly_three_jumps` — build a 5-generation chain; assert
   grandparent-of-grandparent is **out** and 3-jumps-away is **in**. Catches an off-by-one.
8. `test_family_includes_self`.
9. `test_to_be_nice_to_branch_order` — a creature with `altruist=True` **and** `green_beard=True`
   helps *everyone* (the `altruist` branch wins). Catches anyone who reorders the `elif` chain.
10. `test_samaritan_requires_two_food_and_energy_margin` — boundary-test
    `distance_left` at just under and just over `distance_out * 2 * 1.1`.
11. `test_help_transfers_food_rather_than_creating_it` — conservation: helper loses exactly one,
    recipient gains exactly one, total constant.
12. `test_only_zero_food_creatures_are_helped` — a 1-food neighbour is not a candidate.

---

## 8. Docs to update

- **`README.md`** — add the row to the source table, a "### Sacrifice" section under *What each one
  does*, and the new colour roles.
- **`CLAUDE.md`** — add `sacrifice_sim/` to *Where things live*.
- **`.claude/rules/global/primer-fidelity.md`** — the §0 authority correction (`hamilton_basic.py` is
  **not** the source; `natural_sim.py` is) is **already landed** in the file map. Still to add once
  the port exists: a **Constants that are load-bearing** subsection for sacrifice — the
  `has_helped * 0.5` table, the switch-off-discards-the-trait rule, the `kin_radius` exception, and `√3`.
- **`.claude/hooks/pre-generation/primer-fidelity-guard.sh`** — add a `note` for
  `help_rep_boost|has_helped|kin_radius|family_jumps`, warning that the boolean traits are
  deliberately not inherited when their switch is off.
- **Test count:** nothing to do. The hardcoded `36` has been removed from all seven files that carried
  it — don't reintroduce a number (`.claude/rules/paths/tests.md`).

---

## 9. The gate — `/sim-check`

`.claude/commands/bash/sim-check.sh` is a real 4-stage script that exits non-zero on failure. Add a
**5th stage** and renumber the headers (`1/5` … `5/5`):

```bash
echo ""
echo "5/5  sacrifice: kin altruism persists, indiscriminate altruism does not"
o=$(cd sacrifice_sim && python3 main.py --no-render --days 60 --seed 1 \
      --kin-altruist --mutate-kin-altruist 2>/dev/null)
kin=$(num "$o" 'altruist [0-9.]+')
# Band deliberately wide: this is a coexistence check, not a point estimate.
if [ -z "$kin" ]; then bad "no output"
elif awk "BEGIN{exit !($kin > 0.05)}"; then ok "kin altruists persist at ${kin}"
else bad "kin altruists died out (${kin}) -- check the has_helped reproduction table"; fi
```

Add the **regression stage too** — with all switches off, `sacrifice_sim` must match
`natural_selection_sim`. That single check protects the whole port.

**Timing:** NS at 70 days ≈ 40s and `sacrifice_sim` is slower (the family walk is O(N) per samaritan).
Keep the gate run at ≤60 days and **one seed per Bash call** or you blow the 2-minute timeout.

---

## 10. Open questions to settle while implementing

1. **Lineage retention** (§3.2). Full edges vs. depth-capped. Decide, comment, and test-pin.
2. **`a_gb` / `gbo` naming.** Primer's names are opaque. Convention says mirror his vocabulary so his
   source stays greppable — keep `a_gb`/`gbo` as the field names, but give them a docstring
   explaining they are the falsebeard pair.
3. **Performance.** `to_be_nice_to` is O(N) per samaritan per step, on top of NS's already O(N×F)
   step. Measure before optimising (`.claude/rules/languages/python.md`). If it bites, the family set
   is recomputable once per day, not per step — it cannot change mid-day.
