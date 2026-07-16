# /sim <name> [flags]

Run a simulation with its arena + graph windows. Accepts `natural_selection` (`ns`),
`dove_hawks` (`hd`), or `rps`, plus any flag that sim's `--help` lists.

Run `.claude/commands/bash/sim.sh "$ARGUMENTS"` and report what happened.

Examples: `/sim rps --tie-cost 0`, `/sim ns --famine-day 20`, `/sim hd --doves 10 --hawks 150`.
Add `--no-render` to skip the windows and just print a summary.
