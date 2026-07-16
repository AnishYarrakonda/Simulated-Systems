#!/usr/bin/env bash
# The validation gate: rule checks + the statistical dynamics checks.
#
# The unit tests alone are NOT the gate. A wrong port passes every one of them and
# still produces the wrong emergent dynamic -- the ESS, the orbit direction and
# the trait drift are what actually catch it. That's why this exists separately.
#
# Takes a couple of minutes. Exits non-zero if anything fails.
set -uo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
cd "$root" || exit 1

fails=0
ok()   { printf '  \033[32mok\033[0m   %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fails=$((fails + 1)); }

echo ""
echo "1/4  rule checks"
if out=$(python3 -m pytest tests/ -q 2>&1); then
  ok "$(printf '%s' "$out" | tail -1)"
else
  bad "pytest"; printf '%s\n' "$out" | grep -E '^FAILED' | head -8 | sed 's/^/       /'
fi

# Pull a float out of a sim's summary line. Anchor on the trailing token, not the
# label -- "Hawk share over last 10 days: 46.4%" has a decoy number in the prose.
num() { grep -oE "$2" <<<"$1" | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1; }

echo ""
echo "2/4  hawk/dove reaches the 50/50 ESS from both directions"
# Band is deliberately wide (30-70). The population is only ~85, so binomial noise
# alone is about +/-11% at 2 sigma -- a tight band around 50 cries wolf. The failure
# this actually guards against is coexistence collapsing: a wrong payoff (e.g. coding
# hawk-vs-dove as 2/0) drives one type extinct and lands at 0% or 100%.
for spec in "10 150 from-hawk-majority" "150 10 from-dove-majority"; do
  set -- $spec
  o=$(cd dove_hawks_sim && python3 main.py --no-render --days 120 --doves "$1" --hawks "$2" --seed 2 2>/dev/null)
  pct=$(num "$o" '[0-9]+\.[0-9]+%')
  if [ -z "$pct" ]; then bad "$3: no output"; continue; fi
  if awk "BEGIN{exit !($pct > 30 && $pct < 70)}"; then ok "$3: ${pct}% hawks (both types coexist; ESS is 50)"
  else bad "$3: ${pct}% hawks -- coexistence lost; check the payoff matrix"; fi
done

echo ""
echo "3/4  natural selection: speed-only mutation drives speed up"
o=$(cd natural_selection_sim && python3 main.py --no-render --days 60 --seed 1 \
      --no-mutate-size --no-mutate-sense 2>/dev/null)
spd=$(num "$o" 'speed [0-9.]+')
if [ -z "$spd" ]; then bad "no output"
elif awk "BEGIN{exit !($spd > 1.15)}"; then ok "avg speed ${spd} (started 1.00)"
else bad "avg speed ${spd} -- expected >1.15; selection may be broken"; fi

echo ""
echo "4/4  RPS orbit direction (tie_cost sign)"
o=$(python3 - <<'PY' 2>/dev/null
import sys, os, math
root = os.getcwd(); sys.path.insert(0, root); sys.path.insert(0, os.path.join(root, "rps_sim"))
from config import Config
from simulation import Simulation
def rad(f): return math.sqrt(sum((x - 1/3)**2 for x in f))
for tie in (0.5, -0.5):
    cfg = Config(tie_cost=tie, num_days=60, initial_blob_count=3000, num_trees=1500,
                 initial_allele_frequencies=(2,1,1), seed=0, render=False)
    h = Simulation(cfg).run_headless()
    if len(h) < 5: print(f"{tie} died"); continue
    print(f"{tie} {rad(h[4]):.3f} {rad(h[-1]):.3f}")
PY
)
inward=$(awk '$1=="0.5"  {print ($3 < $2) ? "y" : "n"}' <<<"$o")
outward=$(awk '$1=="-0.5"{print ($3 > $2) ? "y" : "n"}' <<<"$o")
[ "$inward" = "y" ]  && ok  "tie_cost=0.5  spirals inward  ($(awk '$1=="0.5"{print $2" -> "$3}' <<<"$o"))" \
                     || bad "tie_cost=0.5 should spiral INWARD -- see rules/global/primer-fidelity.md"
[ "$outward" = "y" ] && ok  "tie_cost=-0.5 spirals outward ($(awk '$1=="-0.5"{print $2" -> "$3}' <<<"$o"))" \
                     || bad "tie_cost=-0.5 should spiral outward"

echo ""
if [ "$fails" -eq 0 ]; then echo "  all checks passed"; else echo "  $fails check(s) failed"; fi
echo ""
exit "$fails"
