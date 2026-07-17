import math
import random

from primer_common import palette


def wrap_pi(angle):
    """Fold an angle into (-pi, pi]."""
    return (angle + math.pi) % (2 * math.pi) - math.pi


class Creature:
    _next_id = 1

    def __init__(self, config, size=1.0, speed=1.0, sense=1.0, rng=None):
        self.config = config
        self.rng = rng or random
        self.size = size
        self.speed = speed
        self.sense = sense

        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0
        self.heading_target = 0.0
        self.d_heading = 0.0

        self.energy = config.starting_energy
        self.eaten = []  # food objects consumed today; caps at 2
        self.state = "foraging"
        self.alive = True
        self.home = False  # made it back to an edge having eaten
        self.dead_today = False

        self.id = Creature._next_id
        Creature._next_id += 1

        # size/speed/sense never mutate on a live creature (offspring are new
        # objects), so these derived values are constant for its whole life.
        # Cached once here -- they sit in the O(N^2) per-step scan hot path and
        # were the top property cost in the profile.
        self.energy_cost = self._compute_energy_cost()
        self.sense_radius = config.eat_distance + config.base_sense_distance * sense

    @classmethod
    def reset_ids(cls):
        cls._next_id = 1

    # -- derived -----------------------------------------------------------
    def _compute_energy_cost(self):
        """Primer's cost equation: size^3 * speed^2 + sense, charged per step.

        The cubic on size and the square on speed are what make big and fast
        expensive enough to trade off against their benefits.
        """
        cfg = self.config
        cost = (self.size * cfg.size_adjust_factor) ** 3 * (
            self.speed * cfg.speed_adjust_factor
        ) ** 2
        cost += self.sense
        return cost / cfg.sim_resolution

    @property
    def name(self):
        return f"blob#{self.id}"

    @property
    def color(self):
        return palette.CREATURE

    def steps_left(self):
        cost = self.energy_cost
        return math.floor(self.energy / cost) if cost > 0 else 0

    def distance_out(self):
        """Distance to the nearest wall -- how far it is from safety."""
        e = self.config.world_extent
        return min(e - abs(self.x), e - abs(self.y))

    # -- day setup ---------------------------------------------------------
    def place_on_wall(self, rng):
        e = self.config.world_extent
        wall = rng.randrange(4)
        if wall == 0:  # top, heading down
            self.x, self.y, self.heading = rng.uniform(-e, e), e, -math.pi / 2
        elif wall == 1:  # right, heading left
            self.x, self.y, self.heading = e, rng.uniform(-e, e), math.pi
        elif wall == 2:  # bottom, heading up
            self.x, self.y, self.heading = rng.uniform(-e, e), -e, math.pi / 2
        else:  # left, heading right
            self.x, self.y, self.heading = -e, rng.uniform(-e, e), 0.0
        self.heading_target = self.heading

    def start_day(self, reverse_heading=False):
        """Survivors resume from where they ended, turned back around."""
        self.energy = self.config.starting_energy
        self.eaten = []
        self.state = "foraging"
        self.home = False
        self.dead_today = False
        self.d_heading = 0.0
        if reverse_heading:
            self.heading = wrap_pi(self.heading + math.pi)
            self.heading_target = self.heading

    # -- movement ----------------------------------------------------------
    def choose_state(self, predator_near):
        if predator_near:
            self.state = "fleeing"
            return

        n = len(self.eaten)
        if n >= 2:
            self.state = "homebound"
        elif n == 1:
            # Head home once the trip home is starting to look expensive. The
            # state latches: once homebound, it never goes back to foraging.
            if self.state == "homebound" or (
                self.steps_left() * self.speed
                < self.distance_out() * self.config.homebound_ratio
            ):
                self.state = "homebound"
            else:
                self.state = "foraging"
        else:
            self.state = "foraging" if self.state != "homebound" else "homebound"

    def wander(self):
        cfg = self.config
        e = cfg.world_extent
        if max(abs(self.x), abs(self.y)) + cfg.edge_margin > e:
            # Near the edge, bias back toward the middle instead of wandering out.
            self.heading_target = math.atan2(-self.y, -self.x)
        else:
            self.heading_target = wrap_pi(
                self.heading_target
                + self.rng.uniform(-cfg.heading_target_variation, cfg.heading_target_variation)
            )

    def aim_home(self):
        """Home is the nearest wall, not where the day started."""
        e = self.config.world_extent
        gaps = ((e - self.x, 0.0), (e + self.x, math.pi),
                (e - self.y, math.pi / 2), (e + self.y, -math.pi / 2))
        self.heading_target = min(gaps, key=lambda g: g[0])[1]

    def turn(self):
        cfg = self.config
        diff = wrap_pi(self.heading_target - self.heading)
        if diff > 0:
            self.d_heading = min(self.d_heading + cfg.turn_acceleration_eff,
                                 cfg.max_turn_speed_eff)
        elif diff < 0:
            self.d_heading = max(self.d_heading - cfg.turn_acceleration_eff,
                                 -cfg.max_turn_speed_eff)
        if abs(diff) < abs(self.d_heading):  # don't overshoot
            self.d_heading = diff
        self.heading = wrap_pi(self.heading + self.d_heading)

    def effective_speed(self):
        """Turning costs speed, so sharp course changes slow a creature down."""
        cfg = self.config
        ratio = abs(self.d_heading) / cfg.max_turn_speed_eff if cfg.max_turn_speed_eff else 0
        return self.speed * (1 - ratio**2 / 2)

    def advance(self):
        e = self.config.world_extent
        speed = self.effective_speed()

        nx = self.x + math.cos(self.heading) * speed
        ny = self.y + math.sin(self.heading) * speed

        outside = max(abs(nx), abs(ny)) >= e
        if outside:
            nx = min(e, max(-e, nx))
            ny = min(e, max(-e, ny))
            # Reaching the edge only counts as home if it actually ate something.
            if not self.home and len(self.eaten) > 0:
                self.home = True
        self.x, self.y = nx, ny

    def can_eat(self):
        return len(self.eaten) < 2

    # -- reproduction ------------------------------------------------------
    def _mutate(self, value, enabled):
        cfg = self.config
        if enabled and self.rng.random() < cfg.mutation_chance:
            value += cfg.mutation_variation * self.rng.choice((-1, 1))
        return value

    def make_offspring(self):
        cfg = self.config
        child = Creature(
            cfg,
            size=self._mutate(self.size, cfg.mutate_size),
            speed=self._mutate(self.speed, cfg.mutate_speed),
            sense=self._mutate(self.sense, cfg.mutate_sense),
            rng=self.rng,
        )
        child.x, child.y, child.heading = self.x, self.y, self.heading
        return child

    def __str__(self):
        return (f"Creature(size={self.size:.2f}, speed={self.speed:.2f}, "
                f"sense={self.sense:.2f}, ate={len(self.eaten)})")

    __repr__ = __str__
