# dynamics-analyst memory

Baselines. Re-measure rather than trusting these if the rules changed.

- **Hawk/dove ESS ~50%.** Both directions, 120 days: `--doves 10 --hawks 150 --seed 2` → 55.7%;
  `--doves 150 --hawks 10 --seed 3` → 54.3%; `--seed 2` → 38.3%. Population is only ~85, so
  binomial noise is ~±11% at 2σ — do not read a tight band around 50 as meaningful. The real
  signal is that **both types coexist**; a wrong payoff drives one extinct (0% or 100%).
- **RPS needs n>=3000.** At n=800 drift dominates and the orbit sign reads backwards. At n=3000,
  60 days, seed 0, init (2,1,1): tie −0.5 → r 0.531→0.680; 0 → 0.372→0.466 (drift, not signal);
  0.5 → 0.225→0.110. Measure radius `sqrt(sum((x_i − 1/3)^2))`, early vs. late windows.
- **NS speed drift.** `--no-mutate-size --no-mutate-sense`, 70 days: speed 1.00 → ~1.42 (seeds 1
  and 2 agree); size/sense stay exactly 1.00. At 60 days → ~1.41.
- **NS population** settles near `food_count` (100 food → ~100 blobs) since each needs 2 to breed.
- **NS predation** needs size variance to appear at all — at default mutation it's rare. Force it
  with `mutation_chance=0.5, mutation_variation=0.3`: 111 predation events in 30 days, and
  cannibalism then drives size up and population *down* (to ~10).
- **Timing.** NS 70 days ≈ 40s. Three seeds in one Bash call exceeds the 2-min timeout — one per
  call.
