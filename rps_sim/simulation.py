"""Headless rock/paper/scissors sim, ported from Primer's EvoGameTheorySim.cs."""

import random

from primer_common.events import Ate, DaySummary, Encounter, EventLog

from config import NAMES
from individual import Individual
from patch import Patch


class Simulation:
    def __init__(self, config):
        self.config = config
        self.rng = random.Random(config.seed)
        self.day = 0
        self.log = EventLog()

        Individual.reset_ids()
        self.individuals = self._seed_population()
        self.trees = [Patch(config, i) for i in range(config.num_trees)]

        self.strategy_logs = {name: {} for name in NAMES}
        self.individuals_on_day = {}
        self.last_contests = []

    def _seed_population(self):
        cfg = self.config
        freqs = cfg.initial_allele_frequencies or (1, 1, 1)
        total = sum(freqs)
        weights = [f / total for f in freqs]

        pop = []
        for _ in range(cfg.initial_blob_count):
            strategies = self.rng.choices(
                range(3), weights=weights, k=cfg.num_alleles_per_blob
            )
            pop.append(Individual(strategies, cfg, self.rng))
        return pop

    # -- counts ------------------------------------------------------------
    def allele_counts(self):
        """Total alleles of each type -- the population's point on the simplex."""
        counts = [0, 0, 0]
        for ind in self.individuals:
            for allele in ind.strategies:
                counts[allele] += 1
        return counts

    def allele_fractions(self):
        counts = self.allele_counts()
        total = sum(counts) or 1
        return [c / total for c in counts]

    def genotype_counts(self):
        """Blobs per lattice point, for the mixed-strategy ternary bars."""
        counts = {}
        for ind in self.individuals:
            counts[ind.genotype] = counts.get(ind.genotype, 0) + 1
        return counts

    # -- day ---------------------------------------------------------------
    def assign(self):
        """Primer's tree allocation.

        num_games = clamp(N - T, 0, T) trees host a pair; the blobs left over eat
        alone (two offspring) if a tree is still free, and starve otherwise. So
        N <= T means everyone doubles, and N >= 2T starves the surplus.
        """
        cfg = self.config
        for tree in self.trees:
            tree.clear()

        parents = list(self.individuals)
        self.rng.shuffle(parents)

        num_games = max(0, len(parents) - cfg.num_trees)
        num_games = min(num_games, cfg.num_trees)

        contests = []
        for i in range(num_games):
            tree = self.trees[i]
            tree.add(parents[2 * i])
            tree.add(parents[2 * i + 1])
            contests.append(tree)

        starved = []
        next_tree = num_games
        for j in range(num_games * 2, len(parents)):
            if num_games < cfg.num_trees and next_tree < cfg.num_trees:
                tree = self.trees[next_tree]
                tree.add(parents[j])
                contests.append(tree)
                next_tree += 1
            else:
                parents[j].reward = 0.0
                starved.append(parents[j])

        self.last_contests = contests
        return contests, starved

    def resolve_all(self, contests):
        for tree in contests:
            kind, moves, r1, r2 = tree.resolve()
            if kind == "alone":
                self.log.emit(Ate(who=tree.individual1.name, score=r1, where=tree.index))
            elif kind == "game":
                self.log.emit(
                    Encounter(
                        a=f"{tree.individual1.name} ({moves[0]})",
                        b=f"{tree.individual2.name} ({moves[1]})",
                        a_score=r1,
                        b_score=r2,
                        where=tree.index,
                    )
                )

    def reproduce(self):
        """Generations do not overlap -- the next day is children only."""
        children = []
        for ind in self.individuals:
            for _ in range(ind.offspring_count()):
                children.append(ind.make_offspring())
        parents = len(self.individuals)
        self.individuals = children
        return len(children), parents

    def simulate_day(self):
        self.day += 1
        self.log.start_day()

        contests, _starved = self.assign()
        self.resolve_all(contests)
        births, parents = self.reproduce()

        counts = self.allele_counts()
        total = sum(counts) or 1
        for i, name in enumerate(NAMES):
            self.strategy_logs[name][self.day] = counts[i]
        self.individuals_on_day[self.day] = len(self.individuals)

        self.log.emit(
            DaySummary(
                day=self.day,
                population=len(self.individuals),
                births=births,
                deaths=parents,  # every parent is replaced
                stats={f"{n} %": 100 * counts[i] / total for i, n in enumerate(NAMES)},
            )
        )
        return contests

    def run_headless(self):
        history = []
        for _ in range(self.config.num_days):
            if not self.individuals:
                break
            self.simulate_day()
            history.append(self.allele_fractions())
        return history
