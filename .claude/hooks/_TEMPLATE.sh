#!/usr/bin/env bash
# [What it does, and WHY it exists.]
# Wired via [Event(matcher)] in settings.json. Without that entry it never runs.
set -uo pipefail

input=$(cat)                       # hooks receive JSON on stdin
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file" ] && exit 0

# exit 0 = allow (print advice to stderr); non-zero = block, reason on stderr.
exit 0
