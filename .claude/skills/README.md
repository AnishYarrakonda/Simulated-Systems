# skills/

Reusable capabilities invoked by name. Each is a kebab-case folder with a `SKILL.md`
(frontmatter `name` + `description`, then imperative instructions).

- `verify/` — how to drive the sims offscreen and what to look for in the arena, feed and each
  graph. Read this before trying to confirm anything rendered; it saves a cold start.
- `system-skills/`, `domain-skills/`, `operational-skills/`, `utility-skills/` — the standard
  categories, unused so far. `verify/` sits at the top level because it's the one skill here and
  categorising a single item adds nothing.

Clone `_TEMPLATE/SKILL.md` to add one.
