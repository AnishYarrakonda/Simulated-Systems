# The 2026-07 Primer-fidelity rebuild

Why the code looks the way it does. Written right after the rebuild.

## Where it started

Three sims that were matplotlib line charts only — **no creature rendering at all**. They were
"inspired by" Primer rather than ported from him, and had drifted:

- **natural_selection** was a tile grid with `energy = 0.02*(vision^3 + size^2 + speed)^0.15` —
  exponents inverted vs. Primer's `size^3 * speed^2 + sense`. No predation, no home mechanic,
  Gaussian mutation instead of discrete ±0.1.
- **dove_hawks** had the payoff matrix *already exactly right*, but reused one `random()` roll for
  both survival and reproduction, and capped population at `patches*2`.
- **rps** had 10 mixed strategies (RRP, PPS…) and a per-strategy line chart. Primer's actual 2024
  video has none of that: 3 alleles, non-overlapping generations, ternary plot.

## What we found

Primer's real source exists and settles everything:
`Helpsypoo/primerpython` (natural selection + hawk/dove, Blender/Python) and
`Primer-Learning/RockPaperScissors` (RPS, Godot/C#). Rules were ported from those.

## The lesson that cost the most

**Research summaries were confidently wrong, and the source was right.** A research pass concluded
`tie_cost=0.5` makes the RPS equilibrium unstable (outward spiral), reasoning `ε = -tie_cost < 0`.
The implementation then measured the *opposite*. Rather than "fixing" the sim to match the claim,
we derived it: `V = x_r*x_p*x_s` gives `d(ln V)/dt = tie_cost*(3*sum(x^2) - 1) >= 0`, so positive
tie_cost is **stabilising**. Primer's scene is named `FindStability`, which agrees. Confirmed
empirically at n=3000.

Had we trusted the summary, we'd have inverted a correct simulation to match a wrong claim. Hence
the `primer-fidelity-auditor` agent (source, not summaries), the pre-generation hook, and the
mandate at the top of CLAUDE.md.

Second lesson: **n matters.** At n=800 drift swamps the orbit signal and you read the sign
backwards. The first measurement was ambiguous for exactly this reason.

## Bugs found by running, not by testing

- The NS rendered path had its own copy of the end-of-day block and dropped every `Born`/`Died`
  event — the feed showed only day summaries while all tests stayed green. Fixed by splitting the
  day into `begin_day`/`step`/`finish_day` shared by both paths.
- `.gitignore` had been deleted-but-unstaged, which is why `__pycache__`/`.DS_Store`/`.idea` had
  reappeared as untracked noise.
