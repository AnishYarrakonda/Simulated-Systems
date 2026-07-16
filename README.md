# Primer simulations

Three evolution simulations rebuilt to match how [Primer](https://www.youtube.com/c/primerlearning)
(Justin Helps) actually implemented them, with a live arena you can watch, a
play-by-play feed, and the graphs he pairs with each video.

The rules here are ported from Primer's own published source, not reconstructed
from the videos:

| Sim | Video | Primer's source |
|---|---|---|
| `natural_selection_sim` | [Simulating Natural Selection](https://www.youtube.com/watch?v=0ZGbIKd0XrM) | [`primerpython`](https://github.com/Helpsypoo/primerpython) `tools/natural_sim.py` |
| `dove_hawks_sim` | [Simulating the Evolution of Aggression](https://www.youtube.com/watch?v=YNMkADpvO4w) | [`primerpython`](https://github.com/Helpsypoo/primerpython) `tools/hawk_dove.py` |
| `rps_sim` | [Simulating the Evolution of Rock, Paper, Scissors](https://www.youtube.com/watch?v=tCoEYFbDVoI) | [`RockPaperScissors`](https://github.com/Primer-Learning/RockPaperScissors) `EvoGameTheorySim.cs` |

## Running

```bash
pip install -r requirements.txt

cd natural_selection_sim && python3 main.py
cd dove_hawks_sim       && python3 main.py
cd rps_sim              && python3 main.py
```

Each opens **two windows**: a pygame arena (blobs, with the play-by-play feed
underneath) and a matplotlib window with the live graphs.

Arena keys: `space` pause, `+`/`-` speed, `q`/`esc` quit.
Every sim takes `--no-render` to run headless, and `--help` lists every knob.

## What each one does

### Natural selection
Continuous 300x300 world. Creatures start on a random wall, forage for food
scattered over the whole map, and must reach **any** wall to survive. 0 food =
death, 1 = survive, 2 = survive + reproduce; eating caps at 2.

- `energy_cost = size^3 * speed^2 + sense`, charged per step
- day length is dynamic: `max(ceil(800 / energy_cost))` over all creatures
- sense radius = `10 + 25 * sense`
- creatures eat each other at `size >= prey.size * 1.2`; prey is immune once home,
  and its stomach contents transfer to the predator
- mutation is discrete: 5% per trait, delta exactly +/-0.1

Graphs: population line, speed histogram (0.0-2.2 in 0.1 bins), 3D trait scatter.

```bash
python3 main.py --no-mutate-size --no-mutate-sense   # speed only -> speed climbs
python3 main.py --famine-day 20                      # food 100 -> 10
```

### Hawk / Dove
121 creatures, 61 bushes. Each bush holds 2 food and fits 2 blobs, so exactly one
blob eats alone. Payoffs: share/share `1,1`; fight/share `1.5,0.5`; fight/fight
`0,0`; alone `2`.

Survival and reproduction are **two independent rolls** (`score > random()` and
`score > 1 + random()`) — that detail is what makes the equilibrium work. There is
no population cap.

Converges to the **50/50 mixed ESS** from either direction:

```bash
python3 main.py --doves 10 --hawks 150    # -> ~50/50
python3 main.py --doves 150 --hawks 10    # -> ~50/50
python3 main.py --trait-mode float --mutation-chance 0.01   # continuous aggression
```

### Rock / Paper / Scissors
Blobs carry alleles (1 = pure strategy, 3 = mixed in thirds) and play one at
random per game. `num_games = clamp(N - trees, 0, trees)` trees host a pair; blobs
left over eat alone (2 offspring) if a tree is free, and starve otherwise. Reward
**is** expected offspring count. Generations do not overlap.

Graphs: R/P/S bar chart and the ternary/simplex plot tracing the orbit.

`--tie-cost` is the knob, and its sign is worth knowing:

| `tie_cost` | behaviour |
|---|---|
| `0.5` (default) | spirals **inward** to (1/3,1/3,1/3) — stable |
| `0` | neutral orbit; drift walks a finite population out to fixation |
| `-0.5` | spirals **outward** |

Paying to tie means a common strategy meets *itself* often and pays for it, which
favours rare strategies. Writing the payoffs as `C - tie_cost*I` and taking
`V = x_r*x_p*x_s` gives `d(ln V)/dt = tie_cost*(3*sum(x^2) - 1) >= 0`, and V peaks
at the centre — so a positive tie cost is stabilising. Measured at n=3000:

```
tie_cost=-0.5: r 0.531 -> 0.680   (outward)
tie_cost= 0.0: r 0.372 -> 0.466   (drift)
tie_cost= 0.5: r 0.225 -> 0.110   (inward)
```

## Layout

- `primer_common/` — shared: `palette` (Primer's colours), `events`, `feed`
  (play-by-play), `arena` (pygame), `graphs` (matplotlib incl. the ternary plot)
- `tests/` — rule checks against Primer's source: `python3 -m pytest tests/ -q`

Sim cores are headless and emit events; the arena and feed consume them. That's
the same split Primer uses, and it's what makes the rules testable without a
window.

## Colours

Primer's palette (`constants.py`, `color_scheme = 2`): background `#2F3336`, text
`#F3F2F0`, blobs/doves/paper `#3E7EA0`, hawks/rock `#D63B50`, scissors `#E7E247`,
food `#698F3F`.
