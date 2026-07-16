# agents/

Sub-agents with their own system prompt and tool allowlist. One Markdown file each
(frontmatter: `name`, `description`, `tools`). The `description` drives auto-selection — make it
say *when* to use the agent, not just what it is.

- `quality/primer-fidelity-auditor.md` — does our rule match Primer's real source? Use before
  changing any Primer-derived default. Exists because summaries of these videos are often wrong.
- `quality/sim-verifier.md` — do the arena/feed/graphs actually render? Tests can't answer this.
- `research/dynamics-analyst.md` — what dynamic emerges under given params (ESS, orbit, drift)?
- `engineering/`, `operations/` — README only; no need has come up yet.

Each agent that keeps notes has a matching `.claude/agent-memory/<name>/MEMORY.md`.
