import random

from primer_common import palette


class Individual:
    """A blob with a `fight_chance` in [0, 1] -- its probability of playing hawk.

    Primer stores aggression as a float and rolls it fresh at every contest
    (`if fight_chance > random(): 'fight'`). In binary mode it only ever holds
    0 or 1, which is the hawk/dove demo; float mode lets it evolve continuously.
    """

    _next_id = 1

    def __init__(self, fight_chance, config, rng=None):
        self.fight_chance = fight_chance
        self.config = config
        self.rng = rng or random
        self.score = 0.0
        self.age = 0
        self.id = Individual._next_id
        Individual._next_id += 1

    @classmethod
    def reset_ids(cls):
        cls._next_id = 1

    @property
    def strategy(self):
        """Display label. In float mode this is just the likelier of the two."""
        return "Hawk" if self.fight_chance >= 0.5 else "Dove"

    @property
    def color(self):
        return palette.mix_colors(palette.DOVE, palette.HAWK, self.fight_chance)

    @property
    def name(self):
        return f"{self.strategy.lower()}#{self.id}"

    def reset(self):
        self.score = 0.0

    def plays_fight(self):
        """Rolled per contest, not fixed per lifetime."""
        return self.fight_chance > self.rng.random()

    def add_food(self, amount):
        self.score += amount

    def survives(self):
        return self.score > self.rng.random()

    def reproduces(self):
        """Independent of the survival roll -- Primer draws a second random().

        Using one roll for both (as the old code did) correlates the two
        outcomes and quietly distorts the equilibrium.
        """
        return self.score > 1 + self.rng.random()

    def make_offspring(self):
        chance = self.fight_chance
        if self.rng.random() < self.config.mutation_chance:
            if self.config.trait_mode == "binary":
                chance = 1 - chance  # flip dove <-> hawk
            else:
                delta = self.config.mutation_variation * self.rng.choice((-1, 1))
                chance = min(1.0, max(0.0, chance + delta))
        return Individual(chance, self.config, self.rng)

    def __str__(self):
        return f"{self.strategy} — Age: {self.age}, Score: {self.score:g}"

    __repr__ = __str__
