# Natural Selection Simulation

Models evolving creatures with traits like size, speed, and vision as they compete for food inside a bounded environment.

## Running
From this directory:

```bash
python3 main.py
```

The simulation renders `matplotlib` figures showing:
- 3D scatter of trait distributions,
- trait averages over time,
- total population count over time.

## Configuration
The main parameters live near the top of `main()`:
- `edge_length`: side length of the square grid.
- `days`: number of simulated days.
- `food_per_tick`: food spawned per tick.
- `starting_population`: initial creature count.
- `ticks_per_day`, `vision_accuracy`: control movement frequency and sensory noise.

Tune these to observe faster evolution, denser populations, or starvation scenarios.

## Structure
- `main.py`: boots the environment, loops through days, and plots stats.
- `environment.py`: grid management, food spawning, and the daily step loop.
- `creature.py`: movement, seeking, and reproduction logic; tracks size/speed/vision.
- `tile.py`: per-cell state, including food amount and occupant reference.

## Notes
- Traits are stored as floats and mutated when creatures reproduce; inspect `creature.py` for mutation mechanics.
- Use the visual output to spot regime shifts, then pause the script to explore the saved data (the plots update as the simulation runs).
