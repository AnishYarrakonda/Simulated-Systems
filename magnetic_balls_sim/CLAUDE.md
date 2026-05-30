# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the simulation

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

There are no tests or linting configuration in this project.

## Architecture

The simulation is a pygame desktop app split into five focused modules:

- **`main.py`** — entry point; owns the game loop, wires events from `pygame_gui` to `Simulation` and `UI`, calls `renderer.draw` each frame.
- **`simulation.py`** — owns all ball state as numpy arrays (`px`, `py`, `vx`, `vy`, `hue`). `step(dt)` runs one physics tick: forces → damping → speed cap → integrate → wall resolve → collision resolve. `restart()` re-samples hues and places balls on a grid.
- **`physics.py`** — stateless numpy functions called by `Simulation.step`. `apply_forces` computes the O(n²) all-pairs hue-coupled interaction using fully vectorized array ops (no Python loops). `resolve_walls` and `resolve_collisions` are also vectorized.
- **`renderer.py`** — draws the sim canvas. Balls are blitted from a 256-entry hue sprite cache (`_sprite_cache`) rather than calling `gfxdraw` per ball each frame, which is what keeps high ball counts smooth.
- **`ui.py`** — sidebar built with `pygame_gui`. Exposes slider/button/dropdown elements as attributes so `main.py` can compare incoming UI events directly against them.
- **`distributions.py`** — hue samplers (Uniform / Gaussian / Bimodal); returns a `list[float]` in `[0, 1)`.
- **`config.py`** — all tunable constants (window size, physics defaults, FPS).

## Force model

Ball interactions are governed by `k(a, b) = cos(2π(a−b))` applied to each pair's hue values: identical hues attract (+1), opposite hues repel (−1), quarter-turn hues are neutral (0). Magnitude follows `1 / (r² + softening)`. A fixed exponential damping (`DAMPING = 1.4 /s`) keeps clusters from oscillating forever.

## Key design constraints

- Physics arrays are always `np.float64`; keep them that way to avoid silent precision loss.
- `apply_forces` and `resolve_collisions` are O(n²) — acceptable up to ~1000 balls. Any changes to these functions must stay vectorized; a Python loop here would make the sim unplayable.
- Slider changes take effect on the *next* `sim.step()` — there is no deferred-apply mechanism, so UI edits are live.
- The sprite cache (`renderer._sprite_cache`) is invalidated only when `radius` changes. If ball radius becomes dynamic, update `_ensure_cache` accordingly.
