from individual import Individual
from patch import Patch
import random
from collections import Counter

class Simulation():
    
    # initializes the sim with the correct number of patches
    def __init__(self, number_of_patches):
        self.day = 1
        self.number_of_patches = number_of_patches
        self.max_population = number_of_patches * 2
        self.all_individuals = []
        self.environment = [Patch() for _ in range(number_of_patches)]

        self.strategy_names = [
            "RRR", "PPP", "SSS",
            "RPS", "RRP", "RRS",
            "PPR", "PPS", "SSR",
            "SSP"
        ]

        # map the strategy tuples to names
        self.strategy_map = {
            Individual.strategy_types[i]: self.strategy_names[i]
            for i in range(len(self.strategy_names))
        }

        # initialize strategy count and population history dictionaries in one place
        self.strategies = Individual.strategy_types

        # strategy counts initialized to zero
        self.strategy_counts = {s: 0 for s in self.strategies}

        # population history per strategy
        self.strategy_logs = {s: {} for s in self.strategies}

        self.individuals_on_day = {}

        # reset the sim for day 1
        self.reset()

    # converts the strategy string like "RRS" to the tuple like (2/3, 0, 1/3)
    def str_to_strategy(self, s):
        s = s.lower()
        counts = [s.count("r"), s.count("p"), s.count("s")]
        total = sum(counts)
        if total == 0:
            raise ValueError(f"Invalid strategy string '{s}'")
        return tuple(c / total for c in counts)

    # adds an individual to the sim
    def add_individual_to_sim(self, individual):
        self.all_individuals.append(individual)

    # resets the sim for each new day
    def reset(self):
        for individual in self.all_individuals:
            individual.reset()
        for patch in self.environment:
            patch.reset()

    # updates the counts of each strategy
    def update_counts(self):
        # Reset counts
        for s in self.strategies:
            self.strategy_counts[s] = 0

        # Count individuals per strategy using Counter for speed
        strat_list = [ind.strategy for ind in self.all_individuals]
        counts = Counter(strat_list)
        for s in self.strategies:
            self.strategy_counts[s] = counts.get(s, 0)

    # assigns each individual to a patch for the day
    def assignPatches(self):
        patch_numbers = [num for _ in range(2) for num in range(self.number_of_patches)]
        patch_lists = [[] for _ in range(self.number_of_patches)]

        random.shuffle(patch_numbers)
        for individual in self.all_individuals:
            patch_number = patch_numbers.pop()
            patch_lists[patch_number].append(individual)

        for i in range(self.number_of_patches):
            self.environment[i].encounter(patch_lists[i])

    # all individuals either survive/die and/or reproduce/don't reproduce at the end of the day
    # this function loops through each individuals list to quickly apply the changes to each one
    # random.shuffle ensures no bias toward particular strategies at the front of the list
    def survive_and_reproduce_all(self):
        # stores offspring in a list
        new_individuals = []
        # shuffles to prevent biased reproduction rates
        random.shuffle(self.all_individuals)
        # stores survivors in a list to prevent potential RunTime Errors
        survivors = []
        # iterates through every individual
        for individual in self.all_individuals:
            # applies method to set their survival and reproduction for the day
            individual.survive_and_reproduce()

            if individual.survives:
                survivors.append(individual)
            else:
                individual.die()

        self.all_individuals = survivors

        for individual in self.all_individuals:
            if individual.reproduces:
                if len(self.all_individuals) + len(new_individuals) < self.max_population:
                    offspring = individual.reproduce()
                    new_individuals.append(offspring)

        for offspring in new_individuals:
            self.add_individual_to_sim(offspring)


    # simulates one day
    def simulate_day(self):
        self.reset()
        self.assignPatches()
        self.survive_and_reproduce_all()
        self.update_counts()

        for s in self.strategies:
            self.strategy_logs[s][self.day] = self.strategy_counts[s]

        self.individuals_on_day[self.day] = len(self.all_individuals)

        self.day += 1

    # adds individuals to the sim by their name like "RRR"
    def add_individuals_by_name(self, strategy_str, count):
        strategy_tuple = self.str_to_strategy(strategy_str)
        if strategy_tuple not in self.strategy_map:
            raise ValueError(f"Strategy tuple {strategy_tuple} not found in known strategies")
        for _ in range(count):
            self.add_individual_to_sim(Individual(strategy_tuple, self))

    # prints the averages of all population types
    def print_population_average(self):
        print("Average population per strategy:")
        for strat_tuple, log in self.strategy_logs.items():
            if log:
                avg = sum(log.values()) / len(log)
                name = self.strategy_map.get(strat_tuple, str(strat_tuple))
                print(f"{name}: {avg:.2f}")
            else:
                name = self.strategy_map.get(strat_tuple, str(strat_tuple))
                print(f"{name}: No data")

        # Overall population average
        if self.individuals_on_day:
            overall_avg = sum(self.individuals_on_day.values()) / len(self.individuals_on_day)
            print(f"Total Population Average: {overall_avg:.2f}")
        else:
            print("No population data yet.")
