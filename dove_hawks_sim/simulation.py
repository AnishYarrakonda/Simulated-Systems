from patch import Patch

import random

class Simulation():

    # creates a new environment with number_of_patches patches
    def __init__(self, number_of_patches):
        self.day = 1  # day number
        self.number_of_patches = number_of_patches  # number of patches
        self.doveCount = 0  # total number of doves
        self.hawkCount = 0  # total number of hawks
        self.max_population = number_of_patches * 2  # stores the max population
        self.all_individuals = []  # list of individuals in the simulation
        self.environment = [Patch() for _ in range(number_of_patches)]  # environment storing all the patches

        # Population history dictionaries of (day number : count)
        self.doves_on_day = {}
        self.hawks_on_day = {}
        self.individuals_on_day = {}

        # resets the patches so the simulation is ready on day 1
        for patch in self.environment:
            patch.reset()

    # adds an individual to the simulation if there is space
    def add_individual_to_sim(self, individual):
        self.all_individuals.append(individual)

    # resets all individuals and patches in the simulation
    def reset(self):
        for individual in self.all_individuals:
            individual.reset()
        for patch in self.environment:
            patch.reset()

    # updates the number of doves and hawks
    def update_counts(self):
        self.doveCount = 0
        self.hawkCount = 0
        for individual in self.all_individuals:
            if individual.strategy == "Dove":
                self.doveCount += 1
            else:
                self.hawkCount += 1

    # assigns every individual a random patch
    def assignPatches(self):
        # total patch spots (2 per patch)
        patch_numbers = [num for _ in range(2) for num in range(self.number_of_patches)]

        # lists to hold individuals per patch
        patch_lists = [[] for _ in range(self.number_of_patches)]

        random.shuffle(patch_numbers)
        for individual in self.all_individuals:
            patch_number = patch_numbers.pop()
            patch_lists[patch_number].append(individual)

        for i in range(self.number_of_patches):
            self.environment[i].encounter(patch_lists[i])

    # survival and reproduction logic for all individuals
    def survive_and_reproduce_all(self):
        new_individuals = []

        # shuffle the individuals so neither doves nor hawks get reproduce before the other consistently
        # this is because without shuffling the list goes in order which is doves first since they were added first
        # this means all doves reproduce reaching the cap before the hawks get to reproduce
        # so all hawk offspring are immediately killed due to the cap
        random.shuffle(self.all_individuals)

        for individual in self.all_individuals:
            individual.survive_and_reproduce()

            if individual.survives:
                individual.increment_age()
                if individual.reproduces:
                    # Only add offspring if population limit is not exceeded
                    if len(self.all_individuals) + len(new_individuals) < self.max_population:
                        offspring = individual.reproduce()
                        new_individuals.append(offspring)
            else:
                individual.die()

        # Remove dead individuals
        self.all_individuals = [ind for ind in self.all_individuals if ind.isAlive]

        # Use your method to add offspring, instead of directly extending the list
        for offspring in new_individuals:
            self.add_individual_to_sim(offspring)

    # simulates one day
    def simulate_day(self):
        self.reset()
        self.assignPatches()
        self.survive_and_reproduce_all()
        self.update_counts()

        # Track populations for this day
        self.doves_on_day[self.day] = self.doveCount
        self.hawks_on_day[self.day] = self.hawkCount
        self.individuals_on_day[self.day] = len(self.all_individuals)

        self.day += 1

    # print out the average population of the strategy or all strategies
    def print_population_average(self, population_type):
        if population_type == "Dove":
            numbers = self.doves_on_day.values()
        elif population_type == "Hawk":
            numbers = self.hawks_on_day.values()
        else:
            numbers = self.individuals_on_day.values()

        print(sum(numbers) / len(numbers))
