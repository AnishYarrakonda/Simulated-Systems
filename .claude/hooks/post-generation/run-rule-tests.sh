#!/usr/bin/env bash
# Run the rule checks after Claude edits a sim file. ~0.1s, so it's cheap to
# always run. Catches a broken port immediately instead of three edits later.
#
# Advisory: reports failures on stderr but exits 0. The suite is fast but it is
# NOT the full gate -- a wrong port passes it. /sim-check is the real gate.
#
# Wired via PostToolUse(Edit|Write) in settings.json.
set -uo pipefail

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file" ] && exit 0

case "$file" in
  *.py) ;;
  *) exit 0 ;;
esac

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
cd "$root" || exit 0
[ -d tests ] || exit 0

if ! out=$(python3 -m pytest tests/ -q 2>&1); then
  {
    echo ""
    echo "  Rule checks FAILED after editing $(basename "$file"):"
    printf '%s\n' "$out" | grep -E '^(FAILED|E  |assert)' | head -12 | sed 's/^/    /'
    echo ""
    echo "  Full output: python3 -m pytest tests/ -q"
    echo ""
  } >&2
fi

exit 0
