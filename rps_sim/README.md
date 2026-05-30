# Rock-Paper-Scissors Simulation

Evolutionary population simulation where individuals adopt Rock, Paper, or Scissors strategies and reproduce/mutate based on payoffs.

## Running
From this folder:

```bash
python3 main.py
```

This opens live plots for:
- population count per strategy over time,
- total population size over time.

## Configuration
Adjust the values in `main()` before running:
- `patches`, `days`: control the spatial scale and simulation length.
- `starting_counts`: initial counts for each strategy.
- `true_mutation_chance`: probability a child mutates into a different strategy.
- `winner_result`, `loser_result`, `tie_result`: payoff matrix values for each encounter.

## Structure
- `main.py`: bootstraps the simulation, runs the day loop, and triggers the plotting.
- `simulation.py`: core engine that handles daily interactions, reproduction, and patch bookkeeping.
- `individual.py`: defines behavior for each strategy and mutation logic.
- `patch.py`: resolves pairwise battles and applies payoff rules to update counts.

## Notes
- Use the plots to spot cyclic dominance patterns; decreasing mutation or tweaking payoffs can highlight classic Rock-Paper-Scissors cycles.
- Logging or exporting data is easy—insert prints inside `simulation.py` when collecting stats to capture the numbers driving each plot.
