"""Headless natural selection sim, ported from Primer's natural_sim.py."""

import math
import random

from primer_common.events import Born, DaySummary, Died, EventLog, Predation

from creature import Creature


class Food:
    __slots__ = ("x", "y", "eaten", "idx")

    def __init__(self, x, y):
        self.x, self.y, self.eaten = x, y, False
        self.idx = 0  # position in Environment.food, for tie-break parity


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

        # -- uniform spatial grid ---------------------------------------------
        # The neighbour scans (predator/prey/food) were O(N^2)/O(N*F) per step
        # and dominated the profile. A grid keyed by cell turns them into a
        # local ring scan. Cell size ~= a default sense radius (eat 10 +
        # sense 25) so a typical query touches a 5x5 block.
        #
        # Bit-identicality: the grid reproduces the linear scan's answer exactly
        # by (a) filtering candidates with the same `d2 < r2` test, (b) breaking
        # ties by list index (min d2, then min idx -- what the strict-`<` linear
        # loop does), and (c) being updated *incrementally* as each creature
        # moves, so a scan sees creatures processed earlier this step at their
        # new positions and later ones at their old positions -- precisely the
        # live reads the original loop made.
        self._cell = 35.0
        e = config.world_extent
        self._ncols = max(1, math.ceil(2 * e / self._cell))
        self._cgrid = []  # creatures: list of cell buckets, rebuilt each day
        self._fgrid = []  # food: rebuilt each day in spawn_food
        self._active = 0  # creatures still alive and not yet home (for everyone_done)

    def _cell_of(self, x, y):
        n = self._ncols
        e = self.config.world_extent
        cx = int((x + e) / self._cell)
        cy = int((y + e) / self._cell)
        cx = 0 if cx < 0 else (n - 1 if cx >= n else cx)
        cy = 0 if cy < 0 else (n - 1 if cy >= n else cy)
        return cy * n + cx

    def _build_creature_grid(self):
        n = self._ncols
        self._cgrid = [[] for _ in range(n * n)]
        for i, c in enumerate(self.creatures):
            c._idx = i
            ci = self._cell_of(c.x, c.y)
            c._cellidx = ci
            self._cgrid[ci].append(c)

    def _regrid_creature(self, c):
        ci = self._cell_of(c.x, c.y)
        if ci != c._cellidx:
            self._cgrid[c._cellidx].remove(c)
            self._cgrid[ci].append(c)
            c._cellidx = ci

    def _build_food_grid(self):
        n = self._ncols
        self._fgrid = [[] for _ in range(n * n)]
        for i, f in enumerate(self.food):
            f.idx = i
            self._fgrid[self._cell_of(f.x, f.y)].append(f)

    def _ring(self, x, y, radius):
        """Yield the flat cell indices within `radius` of (x, y)."""
        n = self._ncols
        e = self.config.world_extent
        cx = int((x + e) / self._cell)
        cy = int((y + e) / self._cell)
        rings = int(radius / self._cell) + 1  # +1 covers partial straddled cells
        for gy in range(max(0, cy - rings), min(n, cy + rings + 1)):
            base = gy * n
            for gx in range(max(0, cx - rings), min(n, cx + rings + 1)):
                yield base + gx

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
        self._build_food_grid()

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
    # Distances are compared squared throughout the per-step scans: d < r iff
    # d^2 < r^2 for non-negative values, and dropping the sqrt removes the 44M
    # math.hypot calls that dominated the profile. The returned distances are
    # therefore squared too -- callers compare them against each other or against
    # a squared threshold, so the ordering is identical.
    def _nearest_food(self, c):
        r = c.sense_radius
        best, best_d2, best_idx = None, r * r, 0
        cx, cy = c.x, c.y
        grid = self._fgrid
        for ci in self._ring(cx, cy, r):
            for f in grid[ci]:
                if f.eaten:
                    continue
                dx, dy = f.x - cx, f.y - cy
                d2 = dx * dx + dy * dy
                # min d2, ties broken by list index -- matches the strict-`<`
                # linear scan, which keeps the earliest index at a tied distance.
                if d2 < best_d2 or (d2 == best_d2 and best is not None and f.idx < best_idx):
                    best, best_d2, best_idx = f, d2, f.idx
        return best, best_d2

    def _predator_near(self, c):
        """A creature 1.2x your size or bigger, close enough to see, not yet home."""
        ratio = self.config.predator_size_ratio
        r = c.sense_radius
        best, best_d2, best_idx = None, r * r, 0
        cx, cy, size_thresh = c.x, c.y, c.size * ratio
        grid = self._cgrid
        for ci in self._ring(cx, cy, r):
            for other in grid[ci]:
                if other is c or not other.alive or other.home:
                    continue
                if other.size >= size_thresh:
                    dx, dy = other.x - cx, other.y - cy
                    d2 = dx * dx + dy * dy
                    if d2 < best_d2 or (d2 == best_d2 and best is not None and other._idx < best_idx):
                        best, best_d2, best_idx = other, d2, other._idx
        return best

    def _nearest_prey(self, c):
        ratio = self.config.predator_size_ratio
        r = c.sense_radius
        best, best_d2, best_idx = None, r * r, 0
        cx, cy, csize = c.x, c.y, c.size
        grid = self._cgrid
        for ci in self._ring(cx, cy, r):
            for other in grid[ci]:
                if other is c or not other.alive or other.home:
                    continue
                # Immune once home -- that's the whole point of getting back.
                if other.size * ratio <= csize:
                    dx, dy = other.x - cx, other.y - cy
                    d2 = dx * dx + dy * dy
                    if d2 < best_d2 or (d2 == best_d2 and best is not None and other._idx < best_idx):
                        best, best_d2, best_idx = other, d2, other._idx
        return best, best_d2

    def step(self):
        cfg = self.config
        for c in self.creatures:
            if not c.alive or c.home:
                continue

            if c.energy <= 0:
                c.alive = False
                c.dead_today = True
                self._active -= 1
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
            # Reflect c's new position in the grid immediately, so the creatures
            # processed after it this step read its updated position -- exactly
            # what the original live-scanning loop did.
            self._regrid_creature(c)
            if c.home:  # reached the wall with food this step
                self._active -= 1
            c.energy -= c.energy_cost

            if c.can_eat() and not c.home:
                self._try_eat(c)

    def _try_eat(self, c):
        cfg = self.config
        eat_d2 = cfg.eat_distance * cfg.eat_distance
        cx, cy = c.x, c.y
        grid = self._fgrid
        # Collect food in reach, then eat in list-index order so the eat-until-
        # cap outcome matches the original loop over self.food exactly.
        reachable = []
        for ci in self._ring(cx, cy, cfg.eat_distance):
            for f in grid[ci]:
                if f.eaten:
                    continue
                dx, dy = f.x - cx, f.y - cy
                if dx * dx + dy * dy < eat_d2:
                    reachable.append(f)
        if reachable:
            reachable.sort(key=lambda f: f.idx)
            for f in reachable:
                f.eaten = True
                c.eaten.append(f)
                if not c.can_eat():
                    return

        if not c.can_eat():
            return

        prey, d2 = self._nearest_prey(c)
        if prey and d2 < eat_d2:
            prey.alive = False
            prey.dead_today = True
            self._active -= 1  # prey was alive and not home, so it counted as active
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
        # Every creature starts the day alive and not home, so all are "active".
        self._active = len(self.creatures)
        self._build_creature_grid()
        return self.day_length()

    def everyone_done(self):
        # O(1): _active tracks creatures still alive and not home. Equivalent to
        # all((not c.alive) or c.home for c in self.creatures) but without the
        # per-step O(N) sweep the day loop used to pay every step.
        return self._active == 0

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
