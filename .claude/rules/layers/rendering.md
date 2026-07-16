---
description: Rules for the shared rendering layer — pygame arena, play-by-play feed, matplotlib graphs
globs: ["primer_common/**/*.py", "*_sim/main.py"]
alwaysApply: false
---

# Rendering layer

`primer_common/` plus each sim's `main.py`. Reads sim state and events; never decides rules.

## Hard constraints

- **Never implement a rule here.** No survival, reproduction, payoff, or mutation logic in a
  rendered path. This bug already shipped once: `natural_selection_sim/main.py` kept its own copy
  of the end-of-day block and silently dropped every `Born`/`Died` event — the feed showed only
  day summaries and the tests stayed green. NS is now split `begin_day()` / `step()` /
  `finish_day()` so both paths share the logic. Keep it that way.
- **`primer_common/` imports nothing from the sims.** One-way dependency.
- Colours come from `primer_common/palette.py` (Primer's `constants.py`, `color_scheme = 2`).
  No hardcoded hex.

## Rendering vs. reality

Hawk/dove and RPS are non-spatial — the sim resolves instantly and `arena.Walker` animates the
walk purely for display. Don't mistake the animation for the model; moving a blob changes nothing.

Natural selection *is* spatial: `env.step()` is real. Its frame loop advances `max(1, speed)` steps
per frame.

## Performance

The arena gets unreadable and slow past a few hundred blobs — RPS caps drawn blobs at `MAX_DRAWN`
and draws the parent snapshot (the blobs that actually played). Primer does the same, disabling
blob animation entirely for his long runs.

## Graphs

`graphs.py` holds `LineGraph`, `Histogram`, `BarChart`, `Scatter3D`, `TernaryPlot`. Each sim uses
the chart Primer paired with it — don't swap them for something "better":

- natural selection → population line, speed histogram (0.0–2.2, 0.1 bins), 3D trait scatter
- hawk/dove → dove/hawk lines (+ an 11-bin `fight_chance` histogram in float mode)
- RPS → R/P/S bar chart + the ternary plot (the centrepiece of his video)

3D axes ignore `set_facecolor` — pane colours must be set via `axis.set_pane_color`, or the panes
render light against the dark theme.
