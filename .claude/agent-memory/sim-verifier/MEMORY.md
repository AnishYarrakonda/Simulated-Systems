# sim-verifier memory

- Driving offscreen works: `SDL_VIDEODRIVER=dummy` + `MPLBACKEND=Agg`, wrap `Arena.end_frame` to
  `pygame.image.save` at frame N then set `self.running = False`. Full recipe in
  `.claude/skills/verify/SKILL.md`.
- Good capture frames: ~240 for hawk/dove and RPS (lands mid-"day" phase, blobs visible in transit);
  ~900 for natural selection (day 3, so the feed has content).
- **Known regression shape:** a feed containing only `-- day N` summaries and no per-event lines
  means the day loop dropped its events — check whether a rendered path re-implemented
  survival/reproduction instead of calling `finish_day()`. This shipped once in
  `natural_selection_sim/main.py`.
- 3D matplotlib axes ignore `set_facecolor`; panes need `axis.set_pane_color` or they render light
  against the dark theme. Fixed in `graphs.py::Scatter3D._reset`.
- `plt.pause` under Agg warns "FigureCanvasAgg is non-interactive" — harmless.
- Verified renders (2026-07): HD arena + feed showing `1.5 / 0.5`, `1 / 1`, `0 / 0`; RPS arena +
  ternary + bar chart, feed showing `2 / 0` and `0.5 / 0.5`; NS arena with grey home blobs on the
  edge, bounds, and HUD `step 151/422`.
