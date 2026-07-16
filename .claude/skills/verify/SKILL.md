---
name: verify
description: Run and observe the three Primer simulations (natural selection, hawk/dove, RPS) — drive the pygame arena and matplotlib graphs, headless or offscreen.
---

# Verifying the Primer sims

Each sim opens **two** windows (pygame arena + matplotlib graphs), so a plain
`python3 main.py` will pop windows onto the user's screen and block. Prefer the
offscreen driver below — it runs the *real* `run()` loop and captures what it drew.

## Deps

`pygame-ce`, `matplotlib`, `numpy` are already installed system-wide. No venv.

## Rules-only check (fast)

```bash
cd /Users/anish_1_2_3/Documents/simulations
python3 -m pytest tests/ -q          # 36 rule checks vs Primer's source
```

Each sim has its own `config.py`/`individual.py`/`patch.py`/`simulation.py` and
imports them by bare name. `tests/test_rules.py` therefore purges `sys.modules`
between sims via `_load()` — don't "simplify" that away or the module cache will
serve whichever sim imported first.

## Headless behaviour (no windows)

Every sim takes `--no-render` and prints a summary. These are the checks that
actually catch a wrong port:

```bash
cd dove_hawks_sim
python3 main.py --no-render --days 120 --doves 10 --hawks 150 --seed 2   # -> ~50% hawks
python3 main.py --no-render --days 120 --doves 150 --hawks 10 --seed 3   # -> ~50% hawks

cd ../natural_selection_sim
python3 main.py --no-render --days 70 --seed 1 --no-mutate-size --no-mutate-sense
# -> avg speed climbs ~1.0 -> ~1.4, size/sense stay exactly 1.00
```

RPS orbit direction (radius from the simplex centre; needs n>=3000 to beat drift):
`tie_cost=0.5` -> inward, `0` -> drift out, `-0.5` -> outward. Don't "fix" this to
match the replicator claim that tie_cost>0 is unstable — it isn't; see the README.

Long runs are slow: NS at 70 days takes ~40s, and 3 seeds will blow a 2-min Bash
timeout. Run seeds one at a time.

## Driving the windows offscreen (the real surface)

`SDL_VIDEODRIVER=dummy` + `MPLBACKEND=Agg`, then monkeypatch `Arena.end_frame` to
save a PNG at frame N and stop. A ready driver lives at
`scratchpad/drive.py` in the session tmp dir; recreate it as:

```python
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["MPLBACKEND"] = "Agg"
# sys.path: repo root + the sim dir; import main; wrap arena_mod.Arena.end_frame
# to pygame.image.save(self.surface, ...) then self.running = False
# wrap graphs_mod.new_figure to keep the fig, stub graphs_mod.show
main.run(main.Config(days=6, seed=0))   # rps_sim uses num_days=
```

Then Read the PNGs. What to look for:

- **arena**: blobs drawn (NS blue; HD blue doves / red hawks; RPS red rock, blue
  paper, yellow scissors), green food, and for NS the world bounds + **gray blobs
  parked on the edge** (home).
- **feed** (bottom panel): encounters with real payoffs — HD `1.5 / 0.5`, `1 / 1`,
  `0 / 0`; RPS `2 / 0`, `0.5 / 0.5` — plus a `-- day N pop X (+b/-d)` summary.
  A feed showing *only* a day summary means the day loop dropped its events.
- **graphs**: NS 3D scatter + population line + speed histogram; HD dove/hawk
  lines; RPS bar chart + ternary triangle with the orange orbit point.

`plt.pause` under Agg warns "FigureCanvasAgg is non-interactive" — harmless, grep
it out.

## Gotchas

- NS's day loop is split `begin_day()` / `step()` / `finish_day()` precisely so the
  rendered and headless paths share the end-of-day logic. If you add a rendered
  path that re-implements survival/reproduction, birth/death events vanish from
  the feed. That bug already happened once.
- `Bash` resets cwd between calls; `cd x && cd ../y` chains break. Use one `cd` per
  call or absolute paths.
