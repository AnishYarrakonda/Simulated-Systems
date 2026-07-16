"""Headless hawk/dove sim. Renders nothing -- see main.py for the windows."""

import random

from primer_common.events import DaySummary, Encounter, EventLog, Ate

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
        self.patches = [Patch(config, i) for i in range(config.food_count)]

        self.doves_on_day = {}
        self.hawks_on_day = {}
        self.individuals_on_day = {}
        self.last_contests = []

    def _seed_population(self):
        cfg = self.config
        if cfg.doves is not None or cfg.hawks is not None:
            doves = cfg.doves or 0
            hawks = cfg.hawks or 0
            pop = [Individual(0.0, cfg, self.rng) for _ in range(doves)]
            pop += [Individual(1.0, cfg, self.rng) for _ in range(hawks)]
        else:
            # Primer: fight_chance = i % 2, then shuffle.
            pop = [
                Individual(float(i % 2), cfg, self.rng)
                for i in range(cfg.num_creatures)
            ]
        self.rng.shuffle(pop)
        return pop

    # -- counts ------------------------------------------------------------
    @property
    def dove_count(self):
        return sum(1 for i in self.individuals if i.fight_chance < 0.5)

    @property
    def hawk_count(self):
        return sum(1 for i in self.individuals if i.fight_chance >= 0.5)

    def fight_chance_histogram(self, bins=11):
        counts = {i: 0 for i in range(bins)}
        for ind in self.individuals:
            counts[round(ind.fight_chance * (bins - 1))] += 1
        return counts

    # -- day ---------------------------------------------------------------
    def assign(self):
        """Each blob picks a random bush from those not yet eaten.

        Primer does this sequentially: a bush leaves the pool the moment it holds
        two blobs. That's subtly different from dealing out fixed slots up front,
        and it's what produces the lone-blob-eats-alone case.
        """
        for patch in self.patches:
            patch.clear()

        order = list(self.individuals)
        self.rng.shuffle(order)

        available = list(self.patches)
        contests = []
        for ind in order:
            if not available:
                break  # no bush left: this blob eats nothing and will likely die
            patch = self.rng.choice(available)
            patch.add(ind)
            if patch.is_full():
                available.remove(patch)
                contests.append(patch)

        # Bushes left holding a single blob feed it alone.
        for patch in available:
            if not patch.is_empty():
                contests.append(patch)

        self.last_contests = contests
        return contests

    def resolve_all(self, contests):
        for patch in contests:
            kind, s1, s2 = patch.resolve()
            if kind == "alone":
                self.log.emit(Ate(who=patch.individual1.name, score=s1, where=patch.index))
            elif kind is not None:
                self.log.emit(
                    Encounter(
                        a=patch.individual1.name,
                        b=patch.individual2.name,
                        a_score=s1,
                        b_score=s2,
                        where=patch.index,
                    )
                )

    def survive_and_reproduce(self):
        """No population cap: Primer lets the rolls decide the population."""
        survivors = []
        births = 0
        deaths = 0
        for ind in self.individuals:
            if ind.survives():
                ind.age += 1
                survivors.append(ind)
                if ind.reproduces():
                    survivors.append(ind.make_offspring())
                    births += 1
            else:
                deaths += 1
        self.individuals = survivors
        return births, deaths

    def simulate_day(self):
        self.day += 1
        self.log.start_day()
        for ind in self.individuals:
            ind.reset()

        contests = self.assign()
        self.resolve_all(contests)
        births, deaths = self.survive_and_reproduce()

        doves, hawks = self.dove_count, self.hawk_count
        self.doves_on_day[self.day] = doves
        self.hawks_on_day[self.day] = hawks
        self.individuals_on_day[self.day] = len(self.individuals)

        total = max(1, len(self.individuals))
        self.log.emit(
            DaySummary(
                day=self.day,
                population=len(self.individuals),
                births=births,
                deaths=deaths,
                stats={"doves": doves, "hawks": hawks, "hawk %": 100 * hawks / total},
            )
        )
        return contests
