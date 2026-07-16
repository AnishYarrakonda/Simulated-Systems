"""Natural selection, after Primer's "Simulating Natural Selection".

Two windows: a pygame arena (creatures forage the continuous world in real time,
then run for the edge) with the play-by-play underneath, and a matplotlib window
with the population line, the speed histogram and the 3D trait scatter.

    python3 main.py                                   # all traits mutate
    python3 main.py --no-mutate-size --no-mutate-sense  # speed only
    python3 main.py --famine-day 20                   # food 100 -> 10
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from primer_common import graphs, palette
from primer_common.arena import Arena

from config import Config
from environment import Environment

SPEED_BINS = [round(x / 10, 1) for x in range(23)]  # 0.0 .. 2.2, Primer's bins


def build_graphs():
    fig = graphs.new_figure("Natural selection — graphs", figsize=(13, 7))
    gs = fig.add_gridspec(2, 2, width_ratios=[3, 2], hspace=0.35, wspace=0.25)
    scatter = graphs.Scatter3D(fig.add_subplot(gs[:, 0], projection="3d"),
                               title="Traits")
    pop = graphs.LineGraph(fig.add_subplot(gs[0, 1]), {"Population": palette.CREATURE},
                           title="Population", ylabel="N")
    hist = graphs.Histogram(
        fig.add_subplot(gs[1, 1]),
        bins=SPEED_BINS,
        title="Speed distribution",
        xlabel="Speed",
        colors=[graphs.palette.to_mpl(palette.mix_colors(palette.BLUE, palette.ORANGE,
                                                         min(1.0, b / 2.2)))
                for b in SPEED_BINS],
    )
    return fig, scatter, pop, hist


def update_graphs(env, scatter, pop, hist):
    days = sorted(env.day_to_population)
    pop.update(days, {"Population": [env.day_to_population[d] for d in days]})
    hist.update(env.speed_histogram())
    scatter.update([c.size for c in env.creatures],
                   [c.sense for c in env.creatures],
                   [c.speed for c in env.creatures])
    graphs.draw()


def draw(arena, env):
    arena.draw_bounds()
    for f in env.food:
        if not f.eaten:
            arena.draw_food((f.x, f.y), radius=3)
    for c in env.creatures:
        if not c.alive:
            continue
        color = palette.GRAY if c.home else c.color
        arena.draw_blob((c.x, c.y), size=c.size, color=color)


def run_day_rendered(arena, env, scatter, pop, hist):
    """Unlike hawk/dove, this world is real -- step it live inside the frame loop."""
    total_steps = env.begin_day()
    step = 0
    while step < total_steps and arena.running:
        if not arena.pump():
            break
        if env.everyone_done():
            break

        if not arena.paused:
            for _ in range(max(1, int(arena.speed))):
                if step >= total_steps or env.everyone_done():
                    break
                env.step()
                step += 1

        arena.begin_frame()
        draw(arena, env)
        arena.end_frame(env.log, hud=f"Day {env.day}  pop {len(env.creatures)}  "
                                     f"step {step}/{total_steps}")

    env.finish_day()
    update_graphs(env, scatter, pop, hist)


def run(config):
    env = Environment(config)
    if not config.render:
        return env.run_headless()

    arena = Arena("Natural selection — arena", world_extent=config.world_extent)
    _, scatter, pop, hist = build_graphs()

    for _ in range(config.days):
        if not arena.running or not env.creatures:
            break
        run_day_rendered(arena, env, scatter, pop, hist)

    arena.quit()
    graphs.show()
    return env


def parse_args():
    d = Config()
    p = argparse.ArgumentParser(description="Primer-style natural selection simulation")
    p.add_argument("--days", type=int, default=d.days)
    p.add_argument("--food-count", type=int, default=d.food_count)
    p.add_argument("--initial-creatures", type=int, default=None)
    p.add_argument("--starting-energy", type=float, default=d.starting_energy)
    p.add_argument("--world-extent", type=float, default=d.world_extent)
    p.add_argument("--base-sense-distance", type=float, default=d.base_sense_distance)
    p.add_argument("--eat-distance", type=float, default=d.eat_distance)
    p.add_argument("--predator-size-ratio", type=float, default=d.predator_size_ratio)
    p.add_argument("--homebound-ratio", type=float, default=d.homebound_ratio)
    p.add_argument("--mutation-chance", type=float, default=d.mutation_chance)
    p.add_argument("--mutation-variation", type=float, default=d.mutation_variation)
    p.add_argument("--no-mutate-speed", action="store_true")
    p.add_argument("--no-mutate-size", action="store_true")
    p.add_argument("--no-mutate-sense", action="store_true")
    p.add_argument("--famine-day", type=int, default=None)
    p.add_argument("--famine-food-count", type=int, default=d.famine_food_count)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--no-render", action="store_true")
    a = p.parse_args()
    return Config(
        days=a.days,
        food_count=a.food_count,
        initial_creatures=a.initial_creatures,
        starting_energy=a.starting_energy,
        world_extent=a.world_extent,
        base_sense_distance=a.base_sense_distance,
        eat_distance=a.eat_distance,
        predator_size_ratio=a.predator_size_ratio,
        homebound_ratio=a.homebound_ratio,
        mutation_chance=a.mutation_chance,
        mutation_variation=a.mutation_variation,
        mutate_speed=not a.no_mutate_speed,
        mutate_size=not a.no_mutate_size,
        mutate_sense=not a.no_mutate_sense,
        famine_day=a.famine_day,
        famine_food_count=a.famine_food_count,
        seed=a.seed,
        render=not a.no_render,
    )


if __name__ == "__main__":
    env = run(parse_args())
    days = sorted(env.day_to_population)
    if days:
        last = days[-1]
        avg = env.average_traits()
        print(f"\nDay {last}: population {env.day_to_population[last]}")
        print(f"avg size {avg['size']:.2f}  speed {avg['speed']:.2f}  sense {avg['sense']:.2f}")
