import math
import random

from primer_common import palette

from config import NAMES


class Individual:
    """A blob carrying `num_alleles` alleles, each Rock, Paper or Scissors.

    It plays one allele picked uniformly at random per game, so one allele means
    a pure strategy and three means a mixed one in thirds. This is Primer's
    genotype model -- the strategy lives in the gene mix, not in a probability
    vector attached to the blob.
    """

    _next_id = 1

    def __init__(self, strategies, config, rng=None):
        self.strategies = list(strategies)
        self.config = config
        self.rng = rng or random
        self.reward = 0.0
        self.id = Individual._next_id
        Individual._next_id += 1

    @classmethod
    def reset_ids(cls):
        cls._next_id = 1

    def play(self):
        return self.rng.choice(self.strategies)

    @property
    def genotype(self):
        """Allele counts as (rock, paper, scissors) -- the ternary lattice point."""
        return tuple(self.strategies.count(i) for i in range(3))

    @property
    def label(self):
        counts = self.genotype
        if counts.count(0) == 2:  # pure
            return NAMES[counts.index(max(counts))]
        return "".join(NAMES[i][0] * counts[i] for i in range(3))

    @property
    def name(self):
        return f"{self.label.lower()}#{self.id}"

    @property
    def color(self):
        return palette.mix_by_weight(palette.STRATEGY_COLORS, self.genotype)

    def offspring_count(self):
        """Reward IS the expected number of children: floor, plus the remainder
        as a probability. `GetOffspringCount` in Primer's source."""
        whole = math.floor(self.reward)
        if self.rng.random() < self.reward - whole:
            whole += 1
        return whole

    def make_offspring(self):
        strategies = []
        for allele in self.strategies:
            if self.rng.random() < self.config.mutation_rate:
                allele = (allele + self.rng.choice((1, 2))) % 3
            strategies.append(allele)
        return Individual(strategies, self.config, self.rng)

    def __str__(self):
        return f"{self.label} — reward {self.reward:g}"

    __repr__ = __str__
