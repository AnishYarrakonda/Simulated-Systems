"""Rock/Paper/Scissors, after Primer's "Simulating the Evolution of Rock, Paper, Scissors".

Two windows: a pygame arena (blobs walk to mango trees, pair up, play) with the
play-by-play underneath, and a matplotlib window with the bar chart and the
ternary plot -- the ternary plot being the centrepiece of the video.

    python3 main.py                      # tie_cost = 0.5 -> spirals inward, stable
    python3 main.py --tie-cost 0         # neutral orbit, drifts to fixation
    python3 main.py --tie-cost -0.5      # spirals outward
    python3 main.py --num-alleles 3      # mixed strategies
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer_common import graphs, palette
from primer_common.arena import PHASES, Arena, Walker, ring_positions

from config import NAMES, Config
from simulation import Simulation

# The arena gets unreadable and slow past a few hundred blobs; Primer animates a
# subset too (AnimateBlobs = false for his 2000-day run).
MAX_DRAWN = 120


def build_graphs():
    fig = graphs.new_figure("Rock / Paper / Scissors — graphs", figsize=(12, 6))
    gs = fig.add_gridspec(1, 2, wspace=0.25)
    bars = graphs.BarChart(
        fig.add_subplot(gs[0]),
        categories=NAMES,
        colors=palette.STRATEGY_COLORS,
        title="Allele share",
        ylabel="%",
    )
    ternary = graphs.TernaryPlot(fig.add_subplot(gs[1]), title="Population on the simplex")
    return fig, bars, ternary


def update_graphs(sim, bars, ternary):
    r, p, s = sim.allele_fractions()
    bars.update({"Rock": r * 100, "Paper": p * 100, "Scissors": s * 100})
    ternary.update(r, p, s)
    graphs.draw()


def build_walkers(contests, trees, homes):
    walkers = {}
    for tree in contests:
        spot = trees[tree.index % len(trees)]
        for slot, ind in enumerate((tree.individual1, tree.individual2)):
            if ind is None:
                continue
            offset = 8 if slot == 0 else -8
            walkers[ind.id] = Walker(
                homes[len(walkers) % len(homes)], (spot[0] + offset, spot[1])
            )
    return walkers


def draw(arena, drawn, trees, walkers, phase, t):
    for spot in trees:
        arena.draw_food(spot, radius=4)
    for ind in drawn:
        walker = walkers.get(ind.id)
        if walker is None:
            continue
        squash = 1.0 if walker.eating(phase, t) else 0.0
        arena.draw_blob(walker.position(phase, t), color=ind.color, squash=squash)


def run(config):
    sim = Simulation(config)

    if not config.render:
        sim.run_headless()
        return sim

    arena = Arena("Rock / Paper / Scissors — arena", world_extent=150)
    _, bars, ternary = build_graphs()

    tree_spots = ring_positions(min(config.num_trees, 80), radius=95, jitter=20, rng=sim.rng)

    for _ in range(config.num_days):
        if not arena.running or not sim.individuals:
            break

        # Snapshot the parents before reproduction replaces them -- these are the
        # blobs that actually played today, so they're the ones worth drawing.
        parents = list(sim.individuals)
        contests = sim.simulate_day()

        drawn = parents[:MAX_DRAWN]
        drawn_ids = {ind.id for ind in drawn}
        shown = [t for t in contests if
                 (t.individual1 and t.individual1.id in drawn_ids)
                 or (t.individual2 and t.individual2.id in drawn_ids)]
        homes = ring_positions(max(1, len(drawn)), radius=140)
        walkers = build_walkers(shown[: len(tree_spots)], tree_spots, homes)

        update_graphs(sim, bars, ternary)

        r, p, s = sim.allele_fractions()
        hud = f"Day {sim.day}  pop {len(sim.individuals)}  R {r:.0%} P {p:.0%} S {s:.0%}"
        for phase, duration in PHASES:
            elapsed = 0.0
            while elapsed < duration and arena.running:
                if not arena.pump():
                    break
                arena.begin_frame()
                draw(arena, drawn, tree_spots, walkers, phase, min(1.0, elapsed / duration))
                dt = arena.end_frame(sim.log, hud=hud)
                if not arena.paused:
                    elapsed += dt * arena.speed

    arena.quit()
    graphs.show()
    return sim


def parse_args():
    d = Config()
    p = argparse.ArgumentParser(description="Primer-style rock/paper/scissors simulation")
    p.add_argument("--num-days", type=int, default=d.num_days)
    p.add_argument("--blobs", type=int, default=d.initial_blob_count)
    p.add_argument("--trees", type=int, default=d.num_trees)
    p.add_argument("--mutation-rate", type=float, default=d.mutation_rate)
    p.add_argument("--num-alleles", type=int, default=d.num_alleles_per_blob)
    p.add_argument("--win-magnitude", type=float, default=d.win_magnitude)
    p.add_argument(
        "--tie-cost", type=float, default=d.tie_cost,
        help="0.5 = spirals inward, stable (Primer's default); "
             "0 = neutral orbit; negative = spirals outward",
    )
    p.add_argument("--seed", type=int, default=d.seed)
    p.add_argument("--no-render", action="store_true")
    a = p.parse_args()
    return Config(
        num_days=a.num_days,
        initial_blob_count=a.blobs,
        num_trees=a.trees,
        mutation_rate=a.mutation_rate,
        num_alleles_per_blob=a.num_alleles,
        win_magnitude=a.win_magnitude,
        tie_cost=a.tie_cost,
        seed=a.seed,
        render=not a.no_render,
    )


if __name__ == "__main__":
    cfg = parse_args()
    sim = run(cfg)
    if sim.individuals_on_day:
        last = max(sim.individuals_on_day)
        r, p, s = sim.allele_fractions()
        print(f"\nDay {last}: population {sim.individuals_on_day[last]}")
        print(f"Rock {r:.1%}  Paper {p:.1%}  Scissors {s:.1%}")
        print("Interior equilibrium is 1/3 each.")
