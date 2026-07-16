# Architecture

## The two-layer split

Every sim is two layers, and the boundary is strict:

```
  sim core (headless)                 rendering (primer_common)
  ------------------                  --------------------------
  creature/individual/patch     -->   arena.py    (pygame window)
  environment/simulation              feed.py     (play-by-play)
  config.py                           graphs.py   (matplotlib)
        |                                   ^
        +-- emits typed events ------------+
            (primer_common/events.py)
```

**Sim cores never import pygame or matplotlib.** They mutate state and append events to an
`EventLog`; the arena and feed consume those events. This is how Primer structures his own code
(his sim files render nothing — Blender/Godot scenes read them), and it's what lets
`tests/test_rules.py` exercise every rule without opening a window.

`primer_common/` imports *from* nothing in the sims. The dependency only points one way.

## Per-sim module layout

Each sim folder is standalone and self-contained:

```
<sim>/
  config.py       # dataclass of every tunable, defaulted to Primer's value
  main.py         # CLI + window wiring; --no-render runs headless
  ...cores        # creature/environment  OR  individual/patch/simulation
```

**Each sim has identically-named modules and imports them by bare name**
(`from config import Config`). That works when running `python3 main.py` from inside the sim's
folder — which is the only supported way to run one. It means:

- You cannot import two sims into one process without purging `sys.modules`.
  `tests/test_rules.py` handles this with `_load()`. Don't "simplify" it away.
- `main.py` does `sys.path.insert(0, <repo root>)` so `primer_common` resolves.

## The day loop

All three share the shape: set up the day → resolve interactions → survival/reproduction → record.

- **Hawk/dove and RPS** are non-spatial: blobs pair at a bush/tree and resolve instantly. `main.py`
  animates the walk purely for display via `arena.Walker`; the sim already finished. So the
  rendered and headless results are identical by construction.
- **Natural selection is spatial and real** — creatures move step by step and the outcome depends
  on it. Its day is therefore split into `begin_day()` / `step()` / `finish_day()` so the rendered
  loop and `simulate_day()` share the end-of-day logic.

⚠️ **Do not re-implement survival/reproduction in a rendered path.** That exact bug shipped once:
`main.py` carried its own copy of the end-of-day block and silently dropped every `Born`/`Died`
event, so the play-by-play showed only day summaries while the tests stayed green.

## Events

`primer_common/events.py` defines `Encounter`, `Ate`, `Predation`, `Born`, `Died`, `DaySummary`.
Each renders itself via `.line()`. `EventLog` keeps a rolling tail (400) for the feed.

To surface something new in the play-by-play, add an event type — don't print from a sim core.

## Data model

- **Natural selection**: `Creature` holds float `size`/`speed`/`sense`, plus per-day `energy`,
  `eaten` (caps at 2), `state` (`foraging`/`homebound`/`fleeing`), `home`, `alive`.
- **Hawk/dove**: `Individual` holds `fight_chance ∈ [0,1]`, rolled fresh per contest. Binary mode
  keeps it at 0 or 1; float mode lets it evolve and colours the blob by interpolation.
- **RPS**: `Individual` holds `strategies: list[int]` of alleles (0=R, 1=P, 2=S) and plays one
  uniformly at random per game. 1 allele = pure, 3 = mixed in thirds.
