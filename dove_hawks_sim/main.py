"""Hawk/Dove, after Primer's "Simulating the Evolution of Aggression".

Two windows: a pygame arena (blobs walk to bushes, pair up, resolve) with the
play-by-play underneath, and a matplotlib window with the live graphs.

    python3 main.py                          # Primer's defaults
    python3 main.py --doves 10 --hawks 150   # converges to the same 50/50 ESS
    python3 main.py --trait-mode float --mutation-chance 0.01
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer_common import graphs, palette
from primer_common.arena import PHASES, Arena, Walker, ring_positions

from config import Config
from simulation import Simulation


def build_graphs(config):
    fig = graphs.new_figure("Hawk / Dove — graphs")
    gs = fig.add_gridspec(2, 1, hspace=0.35)
    line = graphs.LineGraph(
        fig.add_subplot(gs[0]),
        {"Doves": palette.DOVE, "Hawks": palette.HAWK},
        title="Doves vs. Hawks",
        ylabel="Creatures",
    )
    if config.trait_mode == "float":
        # Primer switches to an 11-bin fight_chance histogram in float mode.
        second = graphs.Histogram(
            fig.add_subplot(gs[1]),
            bins=range(11),
            title="Aggression distribution",
            xlabel="fight_chance (tenths)",
            colors=[
                palette.to_mpl(palette.mix_colors(palette.DOVE, palette.HAWK, i / 10))
                for i in range(11)
            ],
            width=0.7,
        )
    else:
        second = graphs.LineGraph(
            fig.add_subplot(gs[1]),
            {"Total": palette.TEXT},
            title="Total population",
            ylabel="Creatures",
        )
    return fig, line, second


def update_graphs(sim, line, second, config):
    days = sorted(sim.individuals_on_day)
    line.update(
        days,
        {
            "Doves": [sim.doves_on_day[d] for d in days],
            "Hawks": [sim.hawks_on_day[d] for d in days],
        },
    )
    if config.trait_mode == "float":
        second.update(sim.fight_chance_histogram())
    else:
        second.update(days, {"Total": [sim.individuals_on_day[d] for d in days]})
    graphs.draw()


def build_walkers(sim, contests, bushes, homes):
    """Send each contesting blob out to its bush; the two share it side by side."""
    walkers = {}
    for patch in contests:
        bush = bushes[patch.index % len(bushes)]
        for slot, ind in enumerate((patch.individual1, patch.individual2)):
            if ind is None:
                continue
            offset = 9 if slot == 0 else -9
            walkers[ind.id] = Walker(
                homes[len(walkers) % len(homes)], (bush[0] + offset, bush[1])
            )
    return walkers


def draw(arena, sim, bushes, walkers, phase, t):
    for bush in bushes:
        arena.draw_food(bush, radius=4)
    for ind in sim.individuals:
        walker = walkers.get(ind.id)
        if walker is None:
            continue
        squash = 1.0 if walker.eating(phase, t) else 0.0
        arena.draw_blob(walker.position(phase, t), color=ind.color, squash=squash)


def run(config):
    sim = Simulation(config)

    if not config.render:
        for _ in range(config.days):
            sim.simulate_day()
        return sim

    arena = Arena("Hawk / Dove — arena", world_extent=150)
    build_graphs_result = build_graphs(config)
    _, line, second = build_graphs_result

    for _ in range(config.days):
        if not arena.running:
            break

        contests = sim.simulate_day()
        bushes = ring_positions(config.food_count, radius=95, jitter=18, rng=sim.rng)
        homes = ring_positions(max(1, len(sim.individuals)), radius=140)
        walkers = build_walkers(sim, contests, bushes, homes)

        update_graphs(sim, line, second, config)

        hud = f"Day {sim.day}  pop {len(sim.individuals)}"
        for phase, duration in PHASES:
            elapsed = 0.0
            while elapsed < duration and arena.running:
                if not arena.pump():
                    break
                arena.begin_frame()
                draw(arena, sim, bushes, walkers, phase, min(1.0, elapsed / duration))
                dt = arena.end_frame(sim.log, hud=hud)
                if not arena.paused:
                    elapsed += dt * arena.speed

    arena.quit()
    graphs.show()
    return sim


def parse_args():
    d = Config()
    p = argparse.ArgumentParser(description="Primer-style hawk/dove simulation")
    p.add_argument("--days", type=int, default=d.days)
    p.add_argument("--num-creatures", type=int, default=d.num_creatures)
    p.add_argument("--food-count", type=int, default=d.food_count)
    p.add_argument("--food-value", type=float, default=d.food_value)
    p.add_argument("--fight-cost", type=float, default=d.fight_cost)
    p.add_argument("--hawk-take-fraction", type=float, default=d.hawk_take_fraction)
    p.add_argument("--sucker-fraction", type=float, default=d.sucker_fraction)
    p.add_argument("--share-fraction", type=float, default=d.share_fraction)
    p.add_argument("--fight-fraction", type=float, default=d.fight_fraction)
    p.add_argument("--mutation-chance", type=float, default=d.mutation_chance)
    p.add_argument("--trait-mode", choices=("binary", "float"), default=d.trait_mode)
    p.add_argument("--doves", type=int, default=None)
    p.add_argument("--hawks", type=int, default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--no-render", action="store_true")
    a = p.parse_args()
    return Config(
        days=a.days,
        num_creatures=a.num_creatures,
        food_count=a.food_count,
        food_value=a.food_value,
        fight_cost=a.fight_cost,
        hawk_take_fraction=a.hawk_take_fraction,
        sucker_fraction=a.sucker_fraction,
        share_fraction=a.share_fraction,
        fight_fraction=a.fight_fraction,
        mutation_chance=a.mutation_chance,
        trait_mode=a.trait_mode,
        doves=a.doves,
        hawks=a.hawks,
        seed=a.seed,
        render=not a.no_render,
    )


if __name__ == "__main__":
    sim = run(parse_args())
    days = sorted(sim.individuals_on_day)
    if days:
        tail = days[-min(10, len(days)) :]
        hawk_pct = [
            100 * sim.hawks_on_day[d] / max(1, sim.individuals_on_day[d]) for d in tail
        ]
        print(f"\nFinal population: {sim.individuals_on_day[days[-1]]}")
        print(f"Hawk share over last {len(tail)} days: {sum(hawk_pct) / len(hawk_pct):.1f}%")
        print("Primer's mixed ESS is 50%.")
