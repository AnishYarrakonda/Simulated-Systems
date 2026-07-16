#!/usr/bin/env bash
# Run a sim with its two windows. Handles the cd -- the sims import by bare name
# and only run from inside their own folder.
set -uo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
name="${1:-}"; shift 2>/dev/null || true
case "$name" in
  ns|natural|natural_selection|natural_selection_sim) dir=natural_selection_sim ;;
  hd|hawk|dove|hawks|dove_hawks|dove_hawks_sim)       dir=dove_hawks_sim ;;
  rps|rock|rps_sim)                                    dir=rps_sim ;;
  *) echo "usage: /sim <natural_selection|dove_hawks|rps> [flags]"; echo "  aliases: ns, hd, rps"; exit 1 ;;
esac
cd "$root/$dir" || exit 1
echo "  $dir: python3 main.py $*"
echo "  keys: space=pause  +/-=speed  q=quit"
exec python3 main.py "$@"
