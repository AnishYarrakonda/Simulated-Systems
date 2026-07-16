# hooks/

Lifecycle scripts. The folders are conceptual; the real wiring is in `settings.json`. **A script
without a settings.json entry never runs.** All three below are wired and executable, and all
exit 0 — they warn, they don't block.

| script | event | does |
|---|---|---|
| `pre-generation/primer-fidelity-guard.sh` | `PreToolUse(Edit\|Write)` | Warns when an edit touches a Primer-derived constant (tie_cost sign, 1.2× predation, payoffs, energy formula, mutation, the two rolls). Exists because these look like bugs to anyone who hasn't read Primer's source — the tie_cost sign nearly got "corrected" once. |
| `post-generation/run-rule-tests.sh` | `PostToolUse(Edit\|Write)` | Runs `pytest tests/ -q` (~0.1s) after any `.py` edit, reports failures. Not the full gate — a wrong port passes it. |
| `pre-commit/strip-junk.sh` | `PreToolUse(Bash)` | On `git commit`: deletes `.DS_Store`/`__pycache__`/`.pytest_cache` and warns if `.gitignore` has gone missing (it was deleted-but-unstaged once). |

`pre-command/`, `post-commit/` — README only; nothing needed yet.

**All three require `jq`** (present at `/usr/bin/jq`). Without it they silently no-op. Hooks read
JSON on stdin; non-zero exit blocks with the reason on stderr. `chmod +x` any script you add.
