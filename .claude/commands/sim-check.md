# /sim-check

The validation gate. Run before pushing anything that touches a sim.

Runs the rule checks **plus** the statistical dynamics checks: hawk/dove coexistence from both
directions, natural-selection speed drift, and the RPS orbit direction. The unit tests alone are
not sufficient — a wrong port passes all of them while producing the wrong dynamic.

Takes ~2 minutes. Run `.claude/commands/bash/sim-check.sh` and report the results.
