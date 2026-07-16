#!/usr/bin/env bash
# Delete .DS_Store / __pycache__ / .pytest_cache before a commit.
#
# Mostly belt-and-braces: .gitignore already covers all of these. It earns its
# keep as a canary -- .gitignore was once deleted-but-unstaged, and untracked
# junk suddenly appearing is exactly what that looks like. So this also checks
# .gitignore still exists.
#
# Wired via PreToolUse(Bash) in settings.json; no-ops unless the command is a
# git commit. Exits 0 always -- never blocks a commit.
set -uo pipefail

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
printf '%s' "$cmd" | grep -q 'git commit' || exit 0

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
cd "$root" || exit 0

removed=$(find . -path ./.git -prune -o \
  \( -name '.DS_Store' -o -name '__pycache__' -o -name '.pytest_cache' \) -print 2>/dev/null | wc -l | tr -d ' ')

find . -path ./.git -prune -o \
  \( -name '.DS_Store' -o -name '__pycache__' -o -name '.pytest_cache' \) -exec rm -rf {} + 2>/dev/null

[ "$removed" != "0" ] && echo "  pre-commit: removed $removed junk path(s)" >&2

if [ ! -f .gitignore ]; then
  echo "  ! .gitignore is MISSING -- it covers __pycache__/, .DS_Store, .idea/." >&2
  echo "    It has gone deleted-but-unstaged before. Check: git status .gitignore" >&2
fi

exit 0
