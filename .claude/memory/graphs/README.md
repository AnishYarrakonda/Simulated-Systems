# memory/graphs/

Diagrams. Empty for now — the dependency graph is small enough to state in one line, and it lives
in `rules/global/architecture.md`:

    sim cores (headless)  --events-->  primer_common {arena, feed, graphs}

`primer_common` imports nothing from the sims. The dependency points one way.
