# primer-fidelity-auditor memory

Verified findings. One fact per entry. Cite the source file.

- `hawk_dove.py`: `FOOD_VALUE=2`, `SHARE_FRACTION=1/2`, `HAWK_TAKE_FRACTION=3/4`,
  `SUCKER_FRACTION=1/4`, `FIGHT_FRACTION=1/2`, `FIGHT_COST=16/16`. So share/share 1/1,
  fight/share **1.5/0.5**, fight/fight 0/0, alone 2. Our `dove_hawks_sim/config.py` matches.
- `hawk_dove.py`: survival/reproduction are two independent rolls —
  `if score > random()` then `if score > 1 + random()`. Not one shared roll.
- `hawk_dove.py`: `DEFAULT_NUM_CREATURES=121`, video scene `World(food_count=61)`. No population
  cap anywhere in his code.
- `natural_sim.py` L378-382: `cost = size^3 * speed^2 + sense`, per step. Confirmed verbatim.
- `natural_sim.py`: `PREDATOR_SIZE_RATIO=1.2`, `BASE_SENSE_DISTANCE=25`, `EAT_DISTANCE=10`,
  `STARTING_ENERGY=800`, `MUTATION_CHANCE=0.05`, `MUTATION_VARIATION=0.1` (delta is exactly ±0.1,
  discrete — `randrange(-1,2,2) * MUTATION_VARIATION`), `HOMEBOUND_RATIO=2`.
- `natural_sim.py`: day length is dynamic — `max(ceil(STARTING_ENERGY / energy_cost))`.
  `DEFAULT_DAY_LENGTH=600` is only a fallback. Food is uniform over the whole world.
- `EvoGameTheorySim.cs`: `numGames = clamp(N - NumTrees, 0, NumTrees)`; reward IS expected
  offspring (`floor(r)` + `frac(r)` chance); generations do not overlap.
- **tie_cost sign — settled.** `tie_cost > 0` spirals INWARD (stable). A prior research pass
  claimed outward via `ε = -tie_cost`; that reasoning is wrong. `d(ln V)/dt = t*(3*sum(x^2) - 1)`
  with `V = x_r*x_p*x_s` is >= 0 for t > 0, and V peaks at the centre. Measured at n=3000:
  0.5 → r 0.225→0.110 (in), 0 → drift out, −0.5 → 0.531→0.680 (out). Primer's scene:
  `FindStability`. **Do not re-open this without new source evidence.**
- Primer's palette (`constants.py`, `color_scheme = 2`): bg `#2F3336`, text `#F3F2F0`,
  blob/dove/paper `#3E7EA0`, hawk/rock `#D63B50`, scissors `#E7E247`, food `#698F3F`.
- Narration vs. code: the video narrates hawk-vs-hawk as risky fighting, but the code applies a
  deterministic `FIGHT_COST` with no injury roll. Code wins.
