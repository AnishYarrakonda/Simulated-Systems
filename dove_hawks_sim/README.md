# Dove Hawks Simulation

Simulates competing Dove and Hawk populations across multiple patches, letting you observe equilibrium shifts as the payoff matrix plays out.

## Running
From this folder:

```bash
python3 main.py
```

The script requires `matplotlib` (usually available by default) and opens live plots showing:
- per-strategy population over time,
- total population over time.

Default parameters inside `main()`:
- `patches=100`, `days=1000`
- `doves=10`, `hawks=10`
- payoff values set to typical Hawk-Dove payoffs.

Adjust those values inside `main()` to run smaller experiments or tweak the aggression/mutation rates.

## Structure
- `main.py`: entry point that wires the simulation, runs the day loop, and renders the charts.
- `simulation.py`: orchestrates patches, tracks births/deaths, and collects stats.
- `individual.py`: defines Dove and Hawk behaviors (interactions, reproduction).
- `patch.py`: executes the payoff logic for each patch each day.

## Notes
- Use `main.py` as the single source of truth for parameters; it directly instantiates the simulation classes.
- Consider redirecting results to CSV (or hooking into `matplotlib` callbacks) if you need to export numbers for analysis.
