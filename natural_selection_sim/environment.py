"""Headless natural selection sim, ported from Primer's natural_sim.py."""

import math
import random

from primer_common.events import Born, DaySummary, Died, EventLog, Predation

from creature import Creature


class Food:
    __slots__ = ("x", "y", "eaten")

    def __init__(self, x, y):
        self.x, self.y, self.eaten = x, y, False


class Environment:
    def __init__(self, config):
        self.config = config
        self.rng = random.Random(config.seed)
        self.day = 0
        self.log = EventLog()

        Creature.reset_ids()
        self.creatures = [
            Creature(config, size=config.start_size, speed=config.start_speed,
                     sense=config.start_sense, rng=self.rng)
            for _ in range(config.creature_count())
        ]
        self.food = []
        self.day_to_population = {}
        self.day_to_averages = {"size": {}, "speed": {}, "sense": {}}
        self._first_day = True

    # -- setup -------------------------------------------------------------
    def food_count_today(self):
        cfg = self.config
        if cfg.famine_day is not None and self.day >= cfg.famine_day:
            return cfg.famine_food_count
        return cfg.food_count

    def spawn_food(self):
        """Uniform over the whole world -- Primer never restricted it to the middle."""
        e = self.config.world_extent
        self.food = [
            Food(self.rng.uniform(-e, e), self.rng.uniform(-e, e))
            for _ in range(self.food_count_today())
        ]

    def place_creatures(self):
        for c in self.creatures:
            if self._first_day:
                c.place_on_wall(self.rng)
                c.start_day()
            else:
                c.start_day(reverse_heading=True)
        self._first_day = False

    def day_length(self):
        """The day lasts as long as the most efficient creature can keep going."""
        if not self.creatures:
            return self.config.default_day_length
        return max(
            math.ceil(self.config.starting_energy / c.energy_cost)
            for c in self.creatures
            if c.energy_cost > 0
        )

    # -- per-step ----------------------------------------------------------
    def _nearest_food(self, c):
        best, best_d = None, c.sense_radius
        for f in self.food:
            if f.eaten:
                continue
            d = math.hypot(f.x - c.x, f.y - c.y)
            if d < best_d:
                best, best_d = f, d
        return best, best_d

    def _predator_near(self, c):
        """A creature 1.2x your size or bigger, close enough to see, not yet home."""
        ratio = self.config.predator_size_ratio
        best, best_d = None, c.sense_radius
        for other in self.creatures:
            if other is c or not other.alive or other.home:
                continue
            if other.size >= c.size * ratio:
                d = math.hypot(other.x - c.x, other.y - c.y)
                if d < best_d:
                    best, best_d = other, d
        return best

    def _nearest_prey(self, c):
        ratio = self.config.predator_size_ratio
        best, best_d = None, c.sense_radius
        for other in self.creatures:
            if other is c or not other.alive or other.home:
                continue
            # Immune once home -- that's the whole point of getting back.
            if other.size * ratio <= c.size:
                d = math.hypot(other.x - c.x, other.y - c.y)
                if d < best_d:
                    best, best_d = other, d
        return best, best_d

    def step(self):
        cfg = self.config
        for c in self.creatures:
            if not c.alive or c.home:
                continue

            if c.energy <= 0:
                c.alive = False
                c.dead_today = True
                self.log.emit(Died(who=c.name, cause="ran out of energy"))
                continue

            predator = self._predator_near(c)
            c.choose_state(predator is not None)

            if c.state == "fleeing":
                # Straight away from the predator: angle_to_predator + pi.
                c.heading_target = math.atan2(c.y - predator.y, c.x - predator.x)
            elif c.state == "homebound":
                c.aim_home()
            else:
                target = None
                if c.can_eat():
                    food, food_d = self._nearest_food(c)
                    prey, prey_d = self._nearest_prey(c)
                    if food and (not prey or food_d <= prey_d):
                        target = (food.x, food.y)
                    elif prey:
                        target = (prey.x, prey.y)
                if target:
                    c.heading_target = math.atan2(target[1] - c.y, target[0] - c.x)
                else:
                    c.wander()

            c.turn()
            c.advance()
            c.energy -= c.energy_cost

            if c.can_eat() and not c.home:
                self._try_eat(c)

    def _try_eat(self, c):
        cfg = self.config
        for f in self.food:
            if f.eaten:
                continue
            if math.hypot(f.x - c.x, f.y - c.y) < cfg.eat_distance:
                f.eaten = True
                c.eaten.append(f)
                if not c.can_eat():
                    return

        if not c.can_eat():
            return

        prey, d = self._nearest_prey(c)
        if prey and d < cfg.eat_distance:
            prey.alive = False
            prey.dead_today = True
            self.log.emit(
                Predation(predator=c.name, prey=prey.name,
                          predator_size=c.size, prey_size=prey.size)
            )
            # The prey's stomach transfers, and the prey itself counts as one food.
            for nom in prey.eaten:
                if c.can_eat():
                    c.eaten.append(nom)
            if c.can_eat():
                c.eaten.append(prey)

    # -- day ---------------------------------------------------------------
    def begin_day(self):
        self.day += 1
        self.log.start_day()
        self.spawn_food()
        self.place_creatures()
        return self.day_length()

    def everyone_done(self):
        return all((not c.alive) or c.home for c in self.creatures)

    def finish_day(self):
        """Survival, reproduction and logging.

        Shared by the headless loop and the rendered one -- the renderer used to
        carry its own copy, which silently dropped the birth/death events.
        """
        survivors, offspring, deaths = [], [], 0
        for c in self.creatures:
            if not c.alive:
                deaths += 1
                continue
            n = len(c.eaten)
            if n == 0 or not c.home:
                c.alive = False
                deaths += 1
                self.log.emit(Died(who=c.name, cause="never made it home"
                                   if n else "found no food"))
                continue
            survivors.append(c)
            if n >= 2:
                baby = c.make_offspring()
                offspring.append(baby)
                self.log.emit(Born(who=baby.name, parent=c.name))

        self.creatures = survivors + offspring
        self._record(len(offspring), deaths)
        return self.creatures

    def simulate_day(self):
        total_steps = self.begin_day()
        for _ in range(total_steps):
            if self.everyone_done():
                break
            self.step()
        return self.finish_day()

    def _record(self, births, deaths):
        n = len(self.creatures)
        self.day_to_population[self.day] = n
        avgs = self.average_traits()
        for k, v in avgs.items():
            self.day_to_averages[k][self.day] = v
        self.log.emit(
            DaySummary(day=self.day, population=n, births=births, deaths=deaths,
                       stats={f"avg {k}": v for k, v in avgs.items()})
        )

    def average_traits(self):
        n = len(self.creatures)
        if not n:
            return {"size": 0.0, "speed": 0.0, "sense": 0.0}
        return {
            "size": sum(c.size for c in self.creatures) / n,
            "speed": sum(c.speed for c in self.creatures) / n,
            "sense": sum(c.sense for c in self.creatures) / n,
        }

    def speed_histogram(self):
        counts = {}
        for c in self.creatures:
            counts[round(c.speed, 1)] = counts.get(round(c.speed, 1), 0) + 1
        return counts

    def run_headless(self):
        for _ in range(self.config.days):
            if not self.creatures:
                break
            self.simulate_day()
        return self
