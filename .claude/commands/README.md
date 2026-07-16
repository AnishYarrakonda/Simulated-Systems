# commands/

Custom slash commands, grouped by implementation language. Each `<name>.md` is the command body;
the script alongside does the work.

- `/sim <name> [flags]` → `bash/sim.sh` — run a sim with windows. Handles the `cd` (sims import by
  bare name and only run from inside their own folder).
- `/sim-check` → `bash/sim-check.sh` — **the validation gate.** pytest plus the statistical
  dynamics checks. ~2 min, exits non-zero on failure.
- `node/`, `python/` — unused; this is a Python repo whose tasks are one-liners best expressed in
  bash.

Clone `_TEMPLATE.md` to add one.
