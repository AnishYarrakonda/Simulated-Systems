# rules/

Guidance scoped narrower than CLAUDE.md.

- `global/` — always-on baseline, `@`-referenced from CLAUDE.md so it loads every session.
  - `primer-fidelity.md` — **the important one.** Primer's source is the authority; the tie_cost
    sign; every load-bearing constant.
  - `architecture.md` — the headless-core / rendering split, the day loop, events.
  - `conventions.md` — style, comments, naming, config, randomness, tests.
  - `workflows.md` — run, test, the validation gate, adding a rule.
- `layers/` — `sim-cores.md` (headless rule logic) and `rendering.md` (pygame/matplotlib).
  Frontmatter globs; load on demand.
- `languages/` — `python.md`. Only Python is used here.
- `paths/` — `tests.md`.
- `platforms/`, `vendors/` — README only. Nothing to put here: the sims run as local desktop
  Python with no deploy target, no cloud runtime, and no third-party service integration.

Global rules are `@`-referenced from CLAUDE.md. Scoped rules use frontmatter `globs` and load when
a matching file is in play — don't `@`-reference those.
