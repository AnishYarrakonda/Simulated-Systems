#!/usr/bin/env bash
# Warn when an edit touches a Primer-derived constant.
#
# These values are read from Primer's published source and several of them look
# like bugs to anyone who hasn't. The tie_cost sign especially: a widely-repeated
# claim says 0.5 should spiral outward. It doesn't. This hook exists so that
# "correction" gets a second look instead of silently landing.
#
# Advisory only -- exits 0 and prints to stderr. It never blocks a real change,
# because every one of these is legitimately tunable.
#
# Wired via PreToolUse(Edit|Write) in settings.json.
set -uo pipefail

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file" ] && exit 0

case "$file" in
  *_sim/*.py|*primer_common/*.py) ;;
  *) exit 0 ;;
esac

# The new content, whichever tool is writing it.
new=$(printf '%s' "$input" | jq -r '.tool_input.new_string // .tool_input.content // empty')
[ -z "$new" ] && exit 0

warn() { printf '  ! %s\n' "$1" >&2; }

hits=0
note() { hits=$((hits + 1)); warn "$1"; }

printf '%s' "$new" | grep -q 'tie_cost' && \
  note "tie_cost: 0.5 => spirals INWARD (stable). Verified analytically and at n=3000.
      The claim that positive tie_cost is unstable is WRONG. Do not 'fix' it."

printf '%s' "$new" | grep -Eq 'predator_size_ratio|1\.2' && \
  note "predation ratio 1.2 is Primer's PREDATOR_SIZE_RATIO (natural_sim.py)."

printf '%s' "$new" | grep -Eq 'hawk_take_fraction|sucker_fraction|fight_cost|share_fraction' && \
  note "hawk/dove payoffs: share 1/1, fight-vs-share 1.5/0.5, fight/fight 0/0, alone 2.
      Hawk-vs-dove is NOT 2/0 -- the dove keeps a quarter. 2/0 kills the doves
      and destroys the 50/50 ESS."

printf '%s' "$new" | grep -Eq 'energy_cost|size \*\* 3|speed \*\* 2' && \
  note "energy = size^3 * speed^2 + sense (natural_sim.py). The exponents are not
      interchangeable -- swapping them inverts the trade-off."

printf '%s' "$new" | grep -Eq 'mutation_variation|mutation_chance' && \
  note "NS mutation is DISCRETE: 5%/trait, delta exactly +/-0.1. Not Gaussian."

printf '%s' "$new" | grep -Eq 'survives|reproduces' && \
  note "survival and reproduction need TWO INDEPENDENT random() rolls.
      Sharing one correlates them and distorts the equilibrium silently."

if [ "$hits" -gt 0 ]; then
  {
    echo ""
    echo "  Primer-fidelity check -- $(basename "$file")"
    echo "  Source: Helpsypoo/primerpython, Primer-Learning/RockPaperScissors"
    echo "  See .claude/rules/global/primer-fidelity.md. Re-run /sim-check after."
    echo ""
  } >&2
fi

exit 0
